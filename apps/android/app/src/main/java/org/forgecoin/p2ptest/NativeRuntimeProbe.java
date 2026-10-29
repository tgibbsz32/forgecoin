package org.forgecoin.p2ptest;
/** Observability only. Does not implement, certify or enable mining/wallet operations. */
public final class NativeRuntimeProbe {
    private static final boolean LOADED;
    static {
        boolean ok;
        try { System.loadLibrary("forge_runtime_probe"); ok=true; }
        catch (UnsatisfiedLinkError | SecurityException e) { ok=false; }
        LOADED=ok;
    }
    private NativeRuntimeProbe() {}
    private static native String nativeCapabilities();
    public static boolean isLoaded() { return LOADED; }
    public static String status() {
        if (!LOADED) return "ARM64 JNI probe unavailable; wallet and mining disabled";
        try { return nativeCapabilities(); }
        catch (UnsatisfiedLinkError | SecurityException e) {
            return "Native probe invocation failed; wallet and mining disabled";
        }
    }
}
