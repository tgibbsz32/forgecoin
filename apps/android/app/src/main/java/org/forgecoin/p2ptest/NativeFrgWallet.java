package org.forgecoin.p2ptest;

/**
 * JNI boundary for this repository's native wallet_api. No Java key derivation,
 * remote wallet RPC or substituting a different chain's engine.
 * Call on a worker thread; password byte arrays must be cleared by callers.
 * Network operations remain unavailable until the acceptance gates pass.
 */
public final class NativeFrgWallet {
    private static final boolean LOADED;
    static {
        boolean loaded;
        try { System.loadLibrary("forge_wallet"); loaded = true; }
        catch (UnsatisfiedLinkError | SecurityException error) { loaded = false; }
        LOADED = loaded;
    }
    private NativeFrgWallet() {}
    public static boolean available() { return LOADED; }
    static native long create(String privatePath, byte[] password);
    static native long restore(String privatePath, byte[] password, String mnemonic, long height);
    static native long open(String privatePath, byte[] password);
    static native String address(long session);
    static native String seed(long session);
    static native String snapshot(long session);
    private static native String refreshLocal(long session,int port);
    static String refreshQaNode(long session,int port) throws Exception {
        FrgQaNode.requireIsolated(port);
        return refreshLocal(session,port);
    }
    private static native String prepareLocal(long session,int port,String recipient,long atomic);
    private static native String commitLocal(long session,int port);
    static native void cancelLocal(long session);
    static String prepareQaSend(long session,int port,String recipient,long atomic) throws Exception {
        FrgQaNode.requireIsolated(port);
        return prepareLocal(session,port,recipient,atomic);
    }
    static String confirmQaSend(long session,int port) throws Exception {
        FrgQaNode.requireIsolated(port);
        return commitLocal(session,port);
    }
    static native void close(long session);
}
