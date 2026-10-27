package org.forgecoin.p2ptest;

import android.app.*;
import android.content.*;
import android.os.*;
import org.json.JSONObject;
import java.io.*;
import java.lang.Process;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

public class NodeService extends Service {
    public static volatile String status = "Stopped\nPeers: —\nHeight: —\nSync: —\nLatest block hash: —";
    private static final StringBuilder logs = new StringBuilder();
    private static final Object lifecycle = new Object();
    private static volatile Process activeProcess;
    private volatile Process process;
    private volatile boolean stopping;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private int rpcPort;
    public static synchronized String logText() { return logs.toString(); }
    private static synchronized void log(String line) {
        logs.append(line).append('\n');
        if (logs.length() > 24000) logs.delete(0, logs.length() - 20000);
    }
    public static String normalizePeer(String input) {
        String s = input.trim();
        if (s.matches("[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?")) s += ":39480";
        if (!s.matches("[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?:39480"))
            throw new IllegalArgumentException("Enter a hostname or IPv4 address, optionally followed by :39480");
        return s;
    }
    @Override public IBinder onBind(Intent intent) { return null; }
    @Override public void onCreate() {
        super.onCreate();
        NotificationManager manager = getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("node", "ForgeCoin node", NotificationManager.IMPORTANCE_LOW));
    }
    @Override public int onStartCommand(Intent intent, int flags, int id) {
        if (intent != null && "STOP".equals(intent.getAction())) { stopSelf(); return START_NOT_STICKY; }
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent view = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop = PendingIntent.getService(this, 1, new Intent(this, NodeService.class).setAction("STOP"), PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        startForeground(1, new Notification.Builder(this, "node").setSmallIcon(android.R.drawable.stat_notify_sync)
            .setContentTitle("ForgeCoin P2P test").setContentText("Node running • tap to view status").setContentIntent(view)
            .addAction(new Notification.Action.Builder(null, "Stop", stop).build()).setOngoing(true).build());
        if (intent == null || !intent.hasExtra("peer")) { stopSelf(); return START_NOT_STICKY; }
        synchronized (lifecycle) {
            if (started) { log("Already running. Stop before changing the remote peer."); return START_NOT_STICKY; }
            started = true;
        }
        final String peer;
        try { peer = normalizePeer(intent.getStringExtra("peer")); }
        catch (Exception e) { status = "Invalid peer"; stopSelf(); return START_NOT_STICKY; }
        worker.execute(() -> runNode(peer));
        return START_NOT_STICKY;
    }
    private boolean started;
    private void runNode(String peer) {
        try {
            synchronized (lifecycle) {
                if (activeProcess != null && activeProcess.isAlive()) throw new IOException("Previous daemon is still stopping; wait and retry");
            }
            File binary = new File(getApplicationInfo().nativeLibraryDir, "libforged.so");
            if (!binary.canExecute()) throw new IOException("ARM64 daemon is missing or not executable");
            File data = new File(getFilesDir(), "phase3");
            if (!data.isDirectory() && !data.mkdirs()) throw new IOException("Cannot create private blockchain directory");
            try (ServerSocket socket = new ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"))) { rpcPort = socket.getLocalPort(); }
            ArrayList<String> command = new ArrayList<>(Arrays.asList(binary.getAbsolutePath(),
                "--data-dir", data.getAbsolutePath(),
                "--add-exclusive-node", peer, "--no-igd", "--non-interactive", "--no-zmq",
                "--rpc-bind-ip", "127.0.0.1", "--rpc-bind-port", Integer.toString(rpcPort), "--rpc-ssl", "disabled",
                "--p2p-bind-ip", "127.0.0.1", "--p2p-bind-port", "49480", "--in-peers", "0",
                "--allow-local-ip", "--check-updates", "disabled", "--disable-dns-checkpoints",
                "--log-level", "0", "--max-log-file-size", "1048576", "--max-log-files", "2",
                "--log-file", new File(data, "forged.log").getAbsolutePath()));
            synchronized (lifecycle) {
                if (stopping) return;
                if (activeProcess != null && activeProcess.isAlive()) throw new IOException("Previous daemon is still stopping; wait and retry");
                process = new ProcessBuilder(command).directory(data).redirectErrorStream(true).start();
                activeProcess = process;
            }
            log("Starting Phase 3 daemon. Remote peer: " + peer);
            Thread reader = new Thread(() -> {
                try (BufferedReader input = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                    String line; while ((line = input.readLine()) != null) log(line);
                } catch (IOException ignored) { }
            }, "daemon-log"); reader.start();
            while (!stopping && process.isAlive()) {
                try {
                    JSONObject info = rpc("/get_info", "{}");
                    if (!"OK".equals(info.optString("status"))) throw new IOException(info.optString("status", "RPC not ready"));
                    long peers = info.optLong("incoming_connections_count") + info.optLong("outgoing_connections_count");
                    long targetHeight = info.optLong("target_height");
                    boolean synced = info.optBoolean("synchronized") || (peers > 0 && targetHeight == 0);
                    String sync = peers == 0 ? "Waiting for peer" : synced ? "Synchronized" : "Syncing";
                    status = "Running → " + peer + "\nPeers: " + peers + "\nHeight: " + info.optLong("height")
                        + "\nTarget height: " + targetHeight + "\nSync: " + sync + "\nLatest block hash:\n" + info.optString("top_block_hash", "—");
                } catch (Exception e) { status = "Starting / RPC unavailable\n" + e.getMessage() + "\nSee daemon logs below."; }
                Thread.sleep(2000);
            }
            if (!stopping) { status = "Daemon exited (" + process.exitValue() + "). See logs."; log(status); }
        } catch (Exception e) { if (!stopping) { status = "Start failed: " + e.getMessage(); log(status); } }
        finally { if (!stopping) new Handler(Looper.getMainLooper()).post(this::stopSelf); }
    }
    private JSONObject rpc(String path, String body) throws Exception {
        HttpURLConnection c = request(path, body);
        try {
            if (c.getResponseCode() != 200) throw new IOException("Local RPC HTTP " + c.getResponseCode());
            try (InputStream in = c.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096]; int n;
                while ((n = in.read(buffer)) != -1) { out.write(buffer, 0, n); if (out.size() > 262144) throw new IOException("RPC response too large"); }
                return new JSONObject(out.toString("UTF-8"));
            }
        } finally { c.disconnect(); }
    }
    private HttpURLConnection request(String path, String body) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL("http://127.0.0.1:" + rpcPort + path).openConnection(Proxy.NO_PROXY);
        c.setConnectTimeout(1500); c.setReadTimeout(1500); c.setInstanceFollowRedirects(false); c.setRequestMethod("POST"); c.setDoOutput(true);
        c.setRequestProperty("Content-Type", "application/json");
        try (OutputStream out = c.getOutputStream()) { out.write(body.getBytes(StandardCharsets.UTF_8)); }
        return c;
    }
    @Override public void onTimeout(int startId, int fgsType) { log("Android session time limit reached."); stopSelf(); }
    @Override public void onDestroy() {
        stopping = true; status = "Stopping…"; worker.shutdownNow();
        new Thread(() -> {
                Process p;
                synchronized (lifecycle) { p = process; }
                if (p != null && p.isAlive()) {
                    p.destroy(); // SIGTERM: daemon's signal handler flushes LMDB.
                    try { if (!p.waitFor(30, TimeUnit.SECONDS)) { log("Stop timeout; forcing daemon exit."); p.destroyForcibly(); p.waitFor(5, TimeUnit.SECONDS); } }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                }
                synchronized (lifecycle) {
                    if (activeProcess == p) { activeProcess = null;
                        status = "Stopped\nPeers: —\nHeight: —\nSync: —\nLatest block hash: —";
                    }
                }
            log("Node stopped.");
        }, "daemon-stop").start();
        stopForeground(STOP_FOREGROUND_REMOVE); super.onDestroy();
    }
}

[executed on device: TREYS_DELL_RTX (a6f7a031-77f9-48a0-8221-947182e0b72a)]