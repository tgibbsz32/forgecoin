package org.forgecoin.p2ptest;
/** RandomX CPU hashing primitive for deterministic integration QA. NOT a block miner. */
public final class NativeRandomX {
    private static final boolean LOADED;
    static {
        boolean ok;
        try { System.loadLibrary("forge_randomx"); ok=true; }
        catch (UnsatisfiedLinkError | SecurityException e) { ok=false; }
        LOADED=ok;
    }
    private NativeRandomX(){}
    private static native byte[] hashLight(byte[] key, byte[] input);
    public static boolean available() { return LOADED; }
    public static byte[] hash(byte[] key, byte[] input) {
        if(!LOADED) throw new IllegalStateException("ARM64 RandomX runtime unavailable");
        if(key==null||key.length<1||key.length>128||input==null||input.length<1||input.length>256)
            throw new IllegalArgumentException("Invalid RandomX input lengths");
        byte[] out=hashLight(key,input);
        if(out==null||out.length!=32) throw new IllegalStateException("RandomX native calculation failed");
        return out;
    }
}
