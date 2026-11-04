package org.forgecoin.p2ptest;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * One fixed known-answer RandomX light-VM QA vector.
 *
 * Not a miner: never searches a nonce, builds a block, submits work, connects
 * to a node/pool, accesses a wallet key, or runs continuously. The native
 * hash library is tested on-device only in explicitly restricted debug UI.
 */
public final class RandomXSelfTest {
    private RandomXSelfTest() {}

    private static final byte[] KEY =
        "test key 000".getBytes(StandardCharsets.US_ASCII);
    private static final byte[] MESSAGE =
        "This is a test".getBytes(StandardCharsets.US_ASCII);
    // Known vector from the vendored/upstream RandomX test suite.
    private static final byte[] EXPECTED = fromHex(
        "639183aae1bf4c9a35884cb46b09cad9175f04efd7684e7262a0ac1c2f0b4e3f");

    private static byte[] fromHex(String hex) {
        if (hex.length() != 64) throw new IllegalArgumentException("Expected 32-byte digest");
        byte[] data = new byte[32];
        for (int i = 0; i < data.length; ++i) {
            int hi = Character.digit(hex.charAt(i * 2), 16);
            int lo = Character.digit(hex.charAt(i * 2 + 1), 16);
            if (hi < 0 || lo < 0) throw new IllegalArgumentException("Bad digest vector");
            data[i] = (byte) ((hi << 4) | lo);
        }
        return data;
    }

    public static boolean isKnownAnswer(byte[] hash) {
        return hash != null && MessageDigest.isEqual(EXPECTED, hash);
    }

    public static boolean runOnce() {
        if (!NativeRandomX.available()) return false;
        byte[] computed = NativeRandomX.hash(KEY.clone(), MESSAGE.clone());
        return isKnownAnswer(computed);
    }

    public static byte[] knownAnswerForUnitTest() {
        return EXPECTED.clone();
    }
}
