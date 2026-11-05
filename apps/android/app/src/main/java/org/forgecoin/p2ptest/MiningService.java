package org.forgecoin.p2ptest;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.os.*;
import java.io.*;
import java.lang.Process;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;

/**
 * User-started XMRig 6.26.0 ARM64 native RandomX worker for an ISOLATED
 * PRIVATE DEVELOPMENT NETWORK ONLY. No production FRG bootstrap or
 * mainnet RPC / public Stratum endpoint is configured or enabled.
 *
 * This service NEVER accesses FRG spend keys or seed phrases. The FRG public
 * wallet address is explicitly supplied by the user-facing Activity.
 * XMRig --daemon / Stratum modes require separate trusted backend tests.
 */
public final class MiningService extends Service {
    public static final String START = "org.forgecoin.p2ptest.MINING_START";
    public static final String STOP = "org.forgecoin.p2ptest.MINING_STOP";
    public static final String CHANNEL = "frg-development-miner";
    public static final String EXPECTED_SHA256 =
            "ca72838b0c5499465f3f8f81bd09b42e6b0823180b8ab675d0ef8e26baca4f47";
    private static final int NOTIFICATION = 8034;
    private static final int MAX_LOG = 9000;
    private static final Object LOCK = new Object();
    private static final StringBuilder recent = new StringBuilder();
    private static volatile String state = "Stopped (no miner process)";
    private static volatile Process liveProcess;
    private static volatile boolean running;
    private static volatile boolean launchPending;
    private static MiningService owner;
    private static final MiningStatistics statistics=new MiningStatistics();
    public static MiningStatistics statistics(){return statistics;}
    private volatile boolean stopRequested;
    private ExecutorService executor;
    private Handler checkHandler;
    private Runnable batteryCheck;
    private PowerManager power;

    public static boolean isRunning() { return running; }
    static boolean runtimePresent(Context context) {
        return BuildConfig.DEBUG && new File(context.getApplicationInfo().nativeLibraryDir,"libxmrig.so").isFile();
    }
    public static String status() { return state; }
    public static String logs() { synchronized (LOCK) { return recent.toString(); } }
    private static void log(String line) {
        if (line == null) return;
        String filtered = line.replaceAll("\u001B\\[[0-9;]*[A-Za-z]", "");
        if (filtered.length() > 420) filtered = filtered.substring(0,420);
        synchronized (LOCK) {
            recent.append(filtered).append('\n');
            if (recent.length() > MAX_LOG)
                recent.delete(0,recent.length() - MAX_LOG);
        }
    }

    private static File executable(Context context) throws IOException {
        if (!Arrays.asList(android.os.Build.SUPPORTED_ABIS).contains("arm64-v8a"))
            throw new IOException("ARM64 phone required for bundled XMRig");
        File f = new File(context.getApplicationInfo().nativeLibraryDir, "libxmrig.so");
        if(!f.isFile() || !f.canExecute())throw new IOException("Bundled ARM64 XMRig is missing or not executable");
        try(FileInputStream file=new FileInputStream(f)){
            byte[] head = new byte[20];
            if(file.read(head)!=20 ||
                    (head[0]&255)!=127 || head[1]!='E' || head[2]!='L' || head[3]!='F' ||
                    head[4]!=2 || (head[18]&255)!=183 || head[19]!=0)
                throw new IOException("Bundled miner has invalid AArch64 ELF header");
        }
        // Whitelist the exact audited build artifact of XMRig v6.26.0.
        try {
            MessageDigest sha=MessageDigest.getInstance("SHA-256");
            try(FileInputStream stream=new FileInputStream(f)) {
                byte[] buffer=new byte[8192]; int count;
                while((count=stream.read(buffer))!=-1)sha.update(buffer,0,count);
            }
            StringBuilder calculated=new StringBuilder();
            for(byte b:sha.digest())calculated.append(String.format(Locale.ROOT,"%02x",b&255));
            if(!EXPECTED_SHA256.equals(calculated.toString()))
                throw new SecurityException("XMRig file digest differs from pinned ARM64 build");
        } catch(SecurityException error){throw error;}
        catch(Exception error){throw new IOException("Unable to verify miner digest",error);}
        return f;
    }

    @Override public void onCreate() {
        super.onCreate();
        executor = Executors.newSingleThreadExecutor();
        checkHandler = new Handler(Looper.getMainLooper());
        power = (PowerManager)getSystemService(POWER_SERVICE);
        NotificationManager nm = (NotificationManager)getSystemService(NOTIFICATION_SERVICE);
        nm.createNotificationChannel(new NotificationChannel(
                CHANNEL,"ForgeCoin development mining",NotificationManager.IMPORTANCE_LOW));
    }

    private Notification notification(String info) {
        PendingIntent open = PendingIntent.getActivity(this,0,
                new Intent(this,MainActivity.class),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        PendingIntent stop = PendingIntent.getService(this,1,
                new Intent(this,MiningService.class).setAction(STOP),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        return new Notification.Builder(this,CHANNEL)
                .setSmallIcon(android.R.drawable.stat_sys_download_done)
                .setContentTitle("ForgeCoin: development mining")
                .setContentText(info).setContentIntent(open)
                .addAction(new Notification.Action.Builder(null,"Stop miner",stop).build())
                .setOngoing(true).build();
    }

    @Override public int onStartCommand(Intent intent,int flags,int id) {
        // Recovered implementation is available only to isolated debug QA.
        // This is a compile-time gate; an Intent cannot authorize production.
        if(!BuildConfig.DEBUG){stopSelf();return START_NOT_STICKY;}
        if(intent==null || STOP.equals(intent.getAction())){
            stopSelf();
            return START_NOT_STICKY;
        }
        if(!START.equals(intent.getAction())) {
            stopSelf();return START_NOT_STICKY;
        }
        synchronized (LOCK) {
            if(owner!=null || running || launchPending || (liveProcess!=null && liveProcess.isAlive())){
                log("Already starting or running; stop before changing endpoint/mode.");
                return START_NOT_STICKY;
            }
            launchPending=true; owner=this; statistics.reset();
        }
        if(Build.VERSION.SDK_INT >= 34)
            startForeground(NOTIFICATION,notification("Preparing user-started private test miner"),
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        else
            startForeground(NOTIFICATION,notification("Preparing private test miner"));
        final String address=intent.getStringExtra("address");
        final String endpoint=intent.getStringExtra("endpoint");
        final String worker=intent.getStringExtra("worker");
        final int mode=intent.getIntExtra("mode",-1);
        final int intensity=intent.getIntExtra("intensity",0);
        stopRequested=false;
        final List<String> argv;
        final int qaNodePort;
        try {
            int endpointPort=MiningConfiguration.loopbackPort(endpoint);
            qaNodePort=mode==0?endpointPort:intent.getIntExtra("qaNodePort",-1);
            if(qaNodePort<1024 || qaNodePort>65535)
                throw new IllegalArgumentException("Disposable daemon port required for genesis validation");
            if(address==null)throw new IllegalArgumentException("No FRG public address");
            argv=MiningConfiguration.buildCommand("XMRIG",address,endpoint,worker,mode,intensity,
                    Runtime.getRuntime().availableProcessors());
        } catch(Exception e) {
            state="Start refused: "+e.getMessage();
            log(state);
            synchronized (LOCK){if(owner==this){launchPending=false;owner=null;}}
            stopSelf();return START_NOT_STICKY;
        }
        String initialSafetyProblem=safetyProblem(true);
        if(initialSafetyProblem!=null) {
            state="Mining refused: "+initialSafetyProblem;
            log(state);
            synchronized (LOCK){if(owner==this){launchPending=false;owner=null;}}
            stopSelf();return START_NOT_STICKY;
        }
        executor.execute(() -> runMiner(argv,mode,endpoint,qaNodePort));
        batteryCheck=new Runnable(){
            @Override public void run() {
                String problem=running?safetyProblem(false):null;
                if(problem!=null) {
                    state="Safety stop: "+problem;
                    log(state);stopSelf();return;
                }
                if(!stopRequested)checkHandler.postDelayed(this,12000);
            }
        };
        checkHandler.postDelayed(batteryCheck,12000);
        return START_NOT_STICKY;
    }

    private String safetyProblem(boolean starting) {
        try {
            if(power==null || Build.VERSION.SDK_INT<29)return "Thermal status unavailable";
            ActivityManager am=getSystemService(ActivityManager.class);
            ActivityManager.MemoryInfo memory=new ActivityManager.MemoryInfo();
            if(am==null)return "Memory status unavailable";
            am.getMemoryInfo(memory);
            // Reserve memory for the light cache at startup. Once allocated,
            // monitor remaining headroom; don't require a second cache reserve.
            if(memory.lowMemory || memory.availMem<(starting?512L:128L)*1024L*1024L)
                return "Insufficient available memory";
            Intent battery=registerReceiver(null,new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
            if(battery==null)return "Battery status unavailable";
            int level=battery.getIntExtra(BatteryManager.EXTRA_LEVEL,-1);
            int scale=battery.getIntExtra(BatteryManager.EXTRA_SCALE,-1);
            if(level<0 || scale<=0 || level>scale)return "Invalid battery reading";
            int percent=(int)((long)level*100/scale);
            boolean plugged=battery.getIntExtra(BatteryManager.EXTRA_PLUGGED,0)!=0;
            int thermal=power.getCurrentThermalStatus();
            if(thermal>=PowerManager.THERMAL_STATUS_MODERATE)return "Device reached moderate thermal status";
            MiningSafetyPolicy.Recommendation policy=MiningSafetyPolicy.evaluate(
                Runtime.getRuntime().availableProcessors(),1,percent,plugged,
                power.isPowerSaveMode(),thermal,true,power.isInteractive(),false,true);
            return policy.eligible?null:policy.reason;
        } catch(Exception e){return "Device safety readings unavailable";}
    }

    private void runMiner(List<String> argv,int mode,String endpoint,int qaNodePort) {
        Process process=null;
        try {
            FrgQaNode.requireIsolated(qaNodePort);
            File binary=executable(this);
            ArrayList<String> actual=new ArrayList<>(argv);
            actual.set(0,binary.getAbsolutePath());
            File cwd=new File(getFilesDir(),"mining-runtime");
            if(!cwd.isDirectory() && !cwd.mkdirs())
                throw new IOException("Cannot create isolated miner working directory");
            log("XMRig v6.26.0 ARM64 SHA-256 verified");
            log("Development private endpoint "+endpoint+", mode "+(mode==0?"node solo":mode==1?"pool solo":"regular pool"));
            ProcessBuilder builder=new ProcessBuilder(actual)
                    .directory(cwd).redirectErrorStream(true);
            Map<String,String> env=builder.environment();
            // Ensure process cannot inherit irrelevant app-side token/account data.
            env.remove("SOLANA_KEYPAIR");env.remove("FRG_SPEND_KEY");
            synchronized (LOCK) {
                if(liveProcess!=null && liveProcess.isAlive())
                    throw new IOException("Another XMRig process is still running");
                if(stopRequested || owner!=this)
                    throw new IOException("Mining service stopped before process startup");
                process=builder.start();
                liveProcess=process;
                running=true;
                launchPending=false;
            }
            state="Native XMRig started; waiting for valid test-network job";
            log(state);
            try(BufferedReader input=new BufferedReader(new InputStreamReader(
                    process.getInputStream(),StandardCharsets.UTF_8))) {
                String line;
                while(!stopRequested && (line=input.readLine())!=null){
                    log(line);
                    statistics.consume(line,SystemClock.elapsedRealtime());
                    String lower=line.toLowerCase(Locale.ROOT);
                    if(lower.contains("accepted") || lower.contains("rejected") ||
                            lower.contains("speed") || lower.contains("new job") ||
                            lower.contains("error") || lower.contains("failed"))
                        state=line.length()>150?line.substring(0,150):line;
                }
            }
            int exit=process.waitFor();
            if(!stopRequested) {
                state="Miner process exited ("+exit+"). Inspect diagnostics.";
                log(state);
            }
        } catch(Exception e) {
            if(!stopRequested){
                state="Miner start failed: "+e.getMessage();
                log(state);
            }
        } finally {
            if(process!=null && process.isAlive()){
                process.destroy();
                try { if(!process.waitFor(4,TimeUnit.SECONDS))process.destroyForcibly(); }
                catch(InterruptedException interrupted){process.destroyForcibly();Thread.currentThread().interrupt();}
            }
            synchronized (LOCK){
                // Preserve a still-live reference so a restart cannot overlap
                // the previous native worker during asynchronous termination.
                if(liveProcess==process && (process==null || !process.isAlive()))liveProcess=null;
                if(owner==this){running=false;launchPending=false;owner=null;statistics.disconnect();}
            }
            if(!stopRequested)new Handler(Looper.getMainLooper()).post(this::stopSelf);
        }
    }

    @Override public IBinder onBind(Intent intent){return null;}
    @Override public void onDestroy(){
        stopRequested=true;
        synchronized (LOCK){
            if(owner==this && liveProcess==null){launchPending=false;owner=null;}
        }
        if(batteryCheck!=null)checkHandler.removeCallbacks(batteryCheck);
        Process process=liveProcess;
        if(process!=null && process.isAlive()){
            process.destroy();
            final Process old=process;
            new Thread(() -> {
                try {
                    if(!old.waitFor(4,TimeUnit.SECONDS))old.destroyForcibly();
                } catch(InterruptedException e){Thread.currentThread().interrupt();old.destroyForcibly();}
            },"miner-termination").start();
        }
        synchronized(LOCK) {
            if(owner==this || owner==null){running=false;statistics.disconnect();}
        }
        state="Stopped; miner process termination requested";
        if(executor!=null)executor.shutdownNow();
        stopForeground(STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }
}
