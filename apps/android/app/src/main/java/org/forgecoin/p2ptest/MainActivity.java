package org.forgecoin.p2ptest;

import android.app.Activity;
import android.app.ActivityManager;
import android.app.AlertDialog;
import android.os.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.*;
import android.net.Uri;
import android.view.*;
import android.text.InputFilter;
import android.text.InputType;
import android.widget.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class MainActivity extends Activity {
    private static final int NAVY=Color.rgb(7,16,27), PANEL=Color.rgb(17,30,43);
    private static final int CYAN=Color.rgb(61,224,208), BLUE=Color.rgb(87,152,255);
    private static final int WHITE=Color.rgb(241,247,252), MUTED=Color.rgb(160,175,190);
    private final Handler handler=new Handler(Looper.getMainLooper());
    private TextView status,logs,deviceSafetyStatus,randomXTestResult,miningStatus;
    private Button randomXTestButton;
    private final AtomicBoolean randomXTestRunning = new AtomicBoolean(false);
    private final Runnable refresh=new Runnable(){public void run(){
        if(status!=null)status.setText(NodeService.status);
        if(logs!=null)logs.setText(NodeService.logText());
        if(deviceSafetyStatus!=null)deviceSafetyStatus.setText(MiningDeviceStatus.summary(MainActivity.this));
        if(miningStatus!=null) {
            MiningStatistics stats=MiningService.statistics();
            double rate=stats.hashesPerSecond(SystemClock.elapsedRealtime());
            String speed=Double.isFinite(rate)?String.format(java.util.Locale.ROOT,"%.1f H/s",rate):"Hashrate unavailable";
            miningStatus.setText(MiningService.status()+"\n"+speed+"  |  Accepted "+stats.accepted()+"  |  Rejected "+stats.rejected());
        }
        handler.postDelayed(this,2500);
    }};
    private int dp(int value){return Math.round(value * getResources().getDisplayMetrics().density);}
    private GradientDrawable panelBackground(){
        GradientDrawable b=new GradientDrawable();b.setColor(PANEL);b.setCornerRadius(22);b.setStroke(1,Color.rgb(40,62,83));return b;
    }
    private TextView label(String s,int size,int color){
        TextView v=new TextView(this);v.setText(s);v.setTextColor(color);v.setTextSize(size);
        v.setPadding(0,8,0,8);return v;
    }
    private LinearLayout panel(LinearLayout main){
        LinearLayout p=new LinearLayout(this);p.setOrientation(LinearLayout.VERTICAL);p.setPadding(24,18,24,22);
        p.setBackground(panelBackground());
        LinearLayout.LayoutParams margins=new LinearLayout.LayoutParams(-1,-2);margins.setMargins(0,0,0,20);
        main.addView(p,margins);return p;
    }
    private Button button(String text,boolean enabled,LinearLayout parent,Runnable action){
        Button b=new Button(this);b.setText(text);b.setAllCaps(false);
        b.setTextColor(enabled?NAVY:MUTED);
        GradientDrawable fill = enabled
            ? new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, new int[]{CYAN,BLUE})
            : new GradientDrawable();
        if(!enabled) fill.setColor(Color.rgb(46,59,74));
        fill.setCornerRadius(9 * getResources().getDisplayMetrics().density);
        b.setBackground(fill);
        b.setMinHeight((int)(48 * getResources().getDisplayMetrics().density));
        LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(-1,-2);
        bp.setMargins(0,6,0,6); b.setLayoutParams(bp);
        b.setEnabled(enabled);parent.addView(b);
        if(enabled&&action!=null)b.setOnClickListener(v->action.run());
        return b;
    }
    private void link(String title,String url,LinearLayout parent){
        button(title,true,parent,()->{
            try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url)));}
            catch(Exception e){Toast.makeText(this,"No browser available",Toast.LENGTH_LONG).show();}
        });
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(NAVY);getWindow().setNavigationBarColor(NAVY);
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(NAVY);
        scroll.setOnApplyWindowInsetsListener((view,insets)->{
            view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),
                insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            return insets;
        });
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(16),dp(16),dp(16),dp(24));scroll.addView(root);
        LinearLayout head=new LinearLayout(this);head.setOrientation(LinearLayout.HORIZONTAL);head.setGravity(Gravity.CENTER_VERTICAL);
        ImageView logo=new ImageView(this);logo.setImageResource(org.forgecoin.p2ptest.R.drawable.forgecoin_brand_logo);
        logo.setContentDescription("ForgeCoin official blue logo");
        logo.setScaleType(ImageView.ScaleType.FIT_CENTER);head.addView(logo,new LinearLayout.LayoutParams(dp(64),dp(64)));
        LinearLayout brand=new LinearLayout(this);brand.setOrientation(LinearLayout.VERTICAL);brand.setPadding(14,0,0,0);
        brand.addView(label("FORGECOIN",25,WHITE));brand.addView(label("PRIVACY  /  CPU MINING",11,CYAN));
        head.addView(brand);root.addView(head);
        root.addView(label("Android miner & wallet",22,WHITE));
        root.addView(label("New-mainnet candidate — restricted testing. No public mining or wallet operations until the native runtime is validated.",13,MUTED));
        LinearLayout wallet=panel(root);wallet.addView(label("FRG WALLET",17,CYAN));
        wallet.addView(label("Secure wallet creation, seed restoration, balance scanning, send/receive and encrypted local storage are required for release.",13,WHITE));
        final TextView nativeWalletStatus=label("Local wallet and balance sync are available on disposable chains in development builds.",12,MUTED);
        boolean nativeWalletReady=BuildConfig.DEBUG && NativeFrgWallet.available();
        button("Create native FRG wallet",nativeWalletReady,wallet,()->NativeWalletUi.create(this,nativeWalletStatus));
        button("Restore native FRG wallet",nativeWalletReady,wallet,()->NativeWalletUi.restore(this,nativeWalletStatus));
        button("Unlock / receive address / backup",nativeWalletReady,wallet,()->NativeWalletUi.unlock(this,nativeWalletStatus));
        button("Sync isolated wallet balance",nativeWalletReady,wallet,()->NativeWalletUi.sync(this,nativeWalletStatus));
        button("Send FRG — validation pending",false,wallet,null);
        wallet.addView(nativeWalletStatus);
        LinearLayout publicAddressPanel=panel(root);
        publicAddressPanel.addView(label("CHECK A PUBLIC FRG ADDRESS",17,CYAN));
        publicAddressPanel.addView(label("Offline standard, integrated and subaddress checksum verification for the frozen native FRG mainnet. This does not create a wallet or prove the owner controls the address.",12,MUTED));
        final EditText publicAddressInput=new EditText(this);
        publicAddressInput.setSingleLine(false);
        publicAddressInput.setMaxLines(2);
        publicAddressInput.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        publicAddressInput.setFilters(new InputFilter[]{new InputFilter.LengthFilter(140)});
        publicAddressInput.setTextColor(WHITE);
        publicAddressInput.setHintTextColor(MUTED);
        publicAddressInput.setHint("Paste a public ForgeCoin address");
        publicAddressInput.setContentDescription("Enter public FRG address for offline checksum validation; never enter a recovery phrase");
        publicAddressPanel.addView(publicAddressInput);
        final TextView addressResult=label("Public address not checked",12,WHITE);
        addressResult.setContentDescription("ForgeCoin address checksum result");
        button("Validate FRG public address",BuildConfig.DEBUG,publicAddressPanel,()->{
            try {
                FrgPublicAddress.Result parsed=FrgPublicAddress.parse(
                    publicAddressInput.getText().toString().trim());
                String kind=parsed.kind==FrgPublicAddress.Kind.STANDARD
                    ? "Standard" : parsed.kind==FrgPublicAddress.Kind.INTEGRATED
                    ? "Integrated" : "Subaddress";
                addressResult.setText("PASS: Native FRG mainnet "+kind
                    +" address. Prefix "+parsed.networkPrefix
                    +" and Keccak-256 checksum match. Public-format check only.");
            } catch(IllegalArgumentException exception) {
                addressResult.setText("REJECTED: invalid address length, Base58, FRG network prefix or checksum.");
            }
        });
        publicAddressPanel.addView(addressResult);
        LinearLayout mine=panel(root);mine.addView(label("RANDOMX MINING",17,CYAN));
        mine.addView(label("Solo and pool mining must use verified ARM64 RandomX executables and the frozen FRG chain identity.",13,WHITE));
        final boolean miningQaReady=BuildConfig.DEBUG && MiningService.runtimePresent(this);
        mine.addView(label("DEVICE MINING SAFETY (READ ONLY)",15,CYAN));
        mine.addView(label("The isolated miner checks battery, heat, available memory and screen state while it runs.",12,MUTED));
        deviceSafetyStatus=label("Reading device status...",12,WHITE);
        deviceSafetyStatus.setContentDescription("Read-only mining device diagnostics");
        mine.addView(deviceSafetyStatus);
        mine.addView(label("MINING INTENSITY",13,CYAN));
        final TextView intensityHint=label("",12,WHITE);
        final SeekBar intensity=new SeekBar(this);
        intensity.setMax(100);
        intensity.setMin(1);
        int initial=getPreferences(MODE_PRIVATE).getInt("future-mining-intensity",50);
        intensity.setProgress(Math.max(1,Math.min(100,initial)));
        intensityHint.setText("Next session: "+intensity.getProgress()+"%");
        intensity.setContentDescription("CPU intensity for the next mining session");
        intensity.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar bar,int value,boolean user){
                intensityHint.setText("Next session: "+value+"%");
                if(user) getPreferences(MODE_PRIVATE).edit()
                    .putInt("future-mining-intensity",value).apply();
            }
            public void onStartTrackingTouch(SeekBar bar){}
            public void onStopTrackingTouch(SeekBar bar){}
        });
        mine.addView(intensity);
        mine.addView(intensityHint);
        button("Start isolated solo mining",miningQaReady,mine,()->MiningQaUi.ask(this,0,intensity.getProgress()));
        button("Start isolated pool mining",miningQaReady,mine,()->MiningQaUi.ask(this,2,intensity.getProgress()));
        button("Stop mining",miningQaReady,mine,()->stopService(new Intent(this,MiningService.class)));
        if(miningQaReady) {
            miningStatus=label("Miner stopped",12,WHITE);
            miningStatus.setContentDescription("Current mining hashrate and accepted or rejected shares");
            mine.addView(miningStatus);
        }
        mine.addView(label("Local development mining only. Stop the miner before changing its endpoint or intensity.",12,MUTED));
        mine.addView(label("VERIFY ARM64 RANDOMX (OFFLINE QA)",15,CYAN));
        mine.addView(label("One fixed known-answer hash; never mines, searches nonces, submits shares or connects to a pool. Temporarily uses substantial memory.",12,MUTED));
        randomXTestButton=button("Verify one RandomX hash",BuildConfig.DEBUG,mine,()->askRandomXSelfTest());
        randomXTestResult=label("Not tested on this handset",12,WHITE);
        randomXTestResult.setContentDescription("Offline native RandomX hashing test result");
        mine.addView(randomXTestResult);
        LinearLayout explore=panel(root);explore.addView(label("BLOCK EXPLORER & POOL STATS",17,CYAN));
        explore.addView(label("Read-only web tools. Statistics must be treated as unavailable until the production network and pool are validated.",13,MUTED));
        link("Pool dashboard", "https://tgibbsz32.github.io/forgecoin/pool.html",explore);
        link("Pool observer / statistics", "https://tgibbsz32.github.io/forgecoin/pool-observer.html",explore);
        link("FRG mainnet status (explorer not launched)", "https://tgibbsz32.github.io/forgecoin/current-mainnet.html",explore);
        LinearLayout partners=panel(root);
        partners.addView(label("PARTNER OFFERS",17,CYAN));
        partners.addView(label("Advertisement: ForgeCoin may earn a commission from purchases made through partner links. No offers are active unless listed on the website.",12,MUTED));
        link("View partner offers", "https://tgibbsz32.github.io/forgecoin/#affiliate-offers",partners);
        LinearLayout node=panel(root);node.addView(label("NODE DIAGNOSTICS",17,CYAN));
        node.addView(label("Legacy ARM64 daemon is not certified for the October 26 mainnet. Remote node startup is disabled.",13,MUTED));
        node.addView(label("ARM64 wallet: "+(NativeFrgWallet.available()?"loaded":"unavailable")
            +"  |  RandomX: "+(NativeRandomX.available()?"loaded":"unavailable"),12,MUTED));
        status=label("Stopped",13,WHITE);node.addView(status);
        logs=label("",10,MUTED);logs.setTypeface(Typeface.MONOSPACE);node.addView(logs);
        LinearLayout solana=panel(root);solana.addView(label("SOLANA / mFRG — FUTURE RELEASE",17,BLUE));
        solana.addView(label("DEBUG BUILDS ONLY — disposable wallet UI tests. Never deposit funds.",12,MUTED));
        button("Create Solana TEST wallet",BuildConfig.DEBUG,solana,()->SolanaDebugAuthGate.require(this,()->SolanaWalletDebugFlow.create(this)));
        button("Restore Solana TEST wallet",BuildConfig.DEBUG,solana,()->SolanaDebugAuthGate.require(this,()->SolanaWalletDebugFlow.restore(this)));
        button("mFRG balances / transfer — unavailable",false,solana,null);
        button("FRG staking — unavailable",false,solana,null);
        setContentView(scroll);
    }
    private boolean eligibleForOneHashSelfTest() {
        if (!BuildConfig.DEBUG || !NativeRandomX.available()) {
            randomXTestResult.setText("Native ARM64 RandomX library unavailable; no hashing performed.");
            return false;
        }
        PowerManager power=(PowerManager)getSystemService(Context.POWER_SERVICE);
        if (power==null || power.isPowerSaveMode()) {
            randomXTestResult.setText("Self-test blocked by unavailable power status or battery saver.");
            return false;
        }
        if (Build.VERSION.SDK_INT>=Build.VERSION_CODES.Q &&
            power.getCurrentThermalStatus()>=PowerManager.THERMAL_STATUS_MODERATE) {
            randomXTestResult.setText("Self-test blocked: device thermal status is moderate or worse.");
            return false;
        }
        if (Build.VERSION.SDK_INT>=Build.VERSION_CODES.Q &&
            power.getCurrentThermalStatus()<PowerManager.THERMAL_STATUS_NONE) {
            randomXTestResult.setText("Self-test blocked: thermal status unavailable.");
            return false;
        }
        Intent battery=registerReceiver(null,new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        if (battery==null) {
            randomXTestResult.setText("Self-test blocked: battery status unavailable.");
            return false;
        }
        int level=battery.getIntExtra(BatteryManager.EXTRA_LEVEL,-1);
        int scale=battery.getIntExtra(BatteryManager.EXTRA_SCALE,-1);
        int chargingState=battery.getIntExtra(BatteryManager.EXTRA_STATUS,-1);
        if (level<0 || scale<=0 || level>scale) {
            randomXTestResult.setText("Self-test blocked: invalid battery measurement.");
            return false;
        }
        boolean charging=chargingState==BatteryManager.BATTERY_STATUS_CHARGING
                || chargingState==BatteryManager.BATTERY_STATUS_FULL;
        if (!charging && ((long)level*100/scale)<20) {
            randomXTestResult.setText("Self-test blocked: battery below 20% while unplugged.");
            return false;
        }
        ActivityManager activity=(ActivityManager)getSystemService(Context.ACTIVITY_SERVICE);
        ActivityManager.MemoryInfo memory=new ActivityManager.MemoryInfo();
        if(activity==null) {
            randomXTestResult.setText("Self-test blocked: memory status unavailable.");
            return false;
        }
        activity.getMemoryInfo(memory);
        if(memory.lowMemory || memory.availMem<512L*1024L*1024L) {
            randomXTestResult.setText("Self-test blocked: insufficient free memory for RandomX light cache.");
            return false;
        }
        return true;
    }

    private void askRandomXSelfTest() {
        if(randomXTestRunning.get() || !eligibleForOneHashSelfTest())return;
        new AlertDialog.Builder(this)
            .setTitle("Offline native RandomX self-test")
            .setMessage("Perform exactly one fixed RandomX light-VM hash? This may briefly consume hundreds of MB of RAM and warm the device. No wallet, mining, network or pool access occurs.")
            .setNegativeButton("Cancel",null)
            .setPositiveButton("Run one hash",(dialog,which)->runOneRandomXHash())
            .show();
    }

    private void runOneRandomXHash() {
        if(!eligibleForOneHashSelfTest() ||
           !randomXTestRunning.compareAndSet(false,true))return;
        randomXTestButton.setEnabled(false);
        randomXTestResult.setText("Running one offline native RandomX reference hash...");
        Thread worker=new Thread(()->{
            long started=SystemClock.elapsedRealtime();
            boolean verified=false;
            try { verified=RandomXSelfTest.runOnce(); }
            catch(RuntimeException | LinkageError | OutOfMemoryError ignored) {
                // A failed native computation must never become a mining
                // success or trigger any retry/background loop.
            }
            final boolean result=verified;
            final long elapsed=SystemClock.elapsedRealtime()-started;
            randomXTestRunning.set(false);
            runOnUiThread(()->{
                if(isFinishing() || isDestroyed())return;
                randomXTestResult.setText(result
                    ? "PASS: one real ARM64 RandomX reference hash matched in "+elapsed+" ms. Not mining."
                    : "FAIL: native RandomX reference hash not verified. Mining still disabled.");
                randomXTestButton.setEnabled(BuildConfig.DEBUG);
            });
        },"single-randomx-offline-qa-hash");
        worker.setDaemon(true);
        worker.start();
    }

    @Override protected void onResume(){super.onResume();handler.post(refresh);}
    @Override protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
}
