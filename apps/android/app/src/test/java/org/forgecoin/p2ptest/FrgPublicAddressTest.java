package org.forgecoin.p2ptest;

import org.junit.Test;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import static org.junit.Assert.*;

public class FrgPublicAddressTest {
    // Public, disposable QA recipient address used by the repository's
    // isolated Windows native full-block test. Not a private key or seed.
    private static final String NATIVE_QA_ADDRESS =
        "YnJ4sygA2VbA4nvoXssZcSKh4fwsw4g3DaujrVCDXSwWGuXwnYTfNsKPVunwuAf8joPEWfePpMh6CEsyEqMpQz2i2uFy112XA";
    private static final String ALPHABET =
        "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
    private static final int[] ENCODED = {0,2,3,5,6,7,9,10,11};

    private static String hex(byte[] bytes) {
        StringBuilder b = new StringBuilder();
        for (byte value : bytes) b.append(String.format("%02x", value & 255));
        return b.toString();
    }

    private static void reject(String input) {
        try {
            FrgPublicAddress.parse(input);
            fail("Malformed/other-chain public address unexpectedly accepted");
        } catch (IllegalArgumentException expected) {
            assertFalse(expected.getMessage().contains("YnJ4"));
        }
    }

    // Independent test fixture encoder (production class deliberately decodes
    // public addresses only, and never derives wallet keys or seeds).
    private static String encode(int networkPrefix, byte[] spend, byte[] view,
                                 byte[] payment) {
        byte[] data = new byte[2 + 32 + 32 + (payment == null ? 0 : 8) + 4];
        data[0] = (byte)(0x80 | (networkPrefix & 0x7f));
        data[1] = (byte)(networkPrefix >>> 7);
        System.arraycopy(spend,0,data,2,32);
        System.arraycopy(view,0,data,34,32);
        if (payment != null) System.arraycopy(payment,0,data,66,8);
        byte[] hash = FrgPublicAddress.keccak256(
            Arrays.copyOf(data,data.length-4));
        System.arraycopy(hash,0,data,data.length-4,4);
        StringBuilder output = new StringBuilder();
        for (int at = 0; at < data.length; at += 8) {
            int size = Math.min(8, data.length-at);
            int targetLen = ENCODED[size];
            byte[] source = Arrays.copyOfRange(data,at,at+size);
            BigInteger number = new BigInteger(1,source);
            StringBuilder block = new StringBuilder();
            for (int i=0;i<targetLen;i++) {
                BigInteger[] div = number.divideAndRemainder(BigInteger.valueOf(58));
                block.append(ALPHABET.charAt(div[1].intValue()));
                number = div[0];
            }
            assertEquals(BigInteger.ZERO,number);
            output.append(block.reverse());
        }
        return output.toString();
    }

    @Test public void knownKeccak256NotSha3() {
        assertEquals("c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
            hex(FrgPublicAddress.keccak256(new byte[0])));
        assertEquals("4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45",
            hex(FrgPublicAddress.keccak256("abc".getBytes(StandardCharsets.US_ASCII))));
    }

    @Test public void parseRealFrozenFrgNativeAddress() {
        FrgPublicAddress.Result result = FrgPublicAddress.parse(NATIVE_QA_ADDRESS);
        assertEquals(FrgPublicAddress.Kind.STANDARD,result.kind);
        assertEquals(190,result.networkPrefix);
        assertEquals(97,result.canonicalAddress.length());
        assertEquals(32,result.spendPublicKey().length);
        assertEquals(32,result.viewPublicKey().length);
        assertNull(result.integratedPaymentId());
        byte[] first = result.spendPublicKey();
        first[0] ^= 1;
        assertFalse(Arrays.equals(first,result.spendPublicKey()));
    }

    @Test public void integratedAndSubaddressPrefixesWithValidChecksums() {
        FrgPublicAddress.Result standard = FrgPublicAddress.parse(NATIVE_QA_ADDRESS);
        byte[] payment = "12345678".getBytes(StandardCharsets.US_ASCII);
        String integrated = encode(191,standard.spendPublicKey(),
                                    standard.viewPublicKey(),payment);
        FrgPublicAddress.Result recovered = FrgPublicAddress.parse(integrated);
        assertEquals(FrgPublicAddress.Kind.INTEGRATED,recovered.kind);
        assertEquals(191,recovered.networkPrefix);
        assertEquals(108,recovered.canonicalAddress.length());
        assertArrayEquals(payment,recovered.integratedPaymentId());
        String subaddress = encode(192,standard.spendPublicKey(),
                                    standard.viewPublicKey(),null);
        FrgPublicAddress.Result recoveredSub = FrgPublicAddress.parse(subaddress);
        assertEquals(FrgPublicAddress.Kind.SUBADDRESS,recoveredSub.kind);
        assertEquals(192,recoveredSub.networkPrefix);
        assertNull(recoveredSub.integratedPaymentId());
    }

    @Test public void rejectChecksumDamageAndInvalidBase58() {
        String replacement = NATIVE_QA_ADDRESS.endsWith("A") ? "B" : "A";
        reject(NATIVE_QA_ADDRESS.substring(0,NATIVE_QA_ADDRESS.length()-1) + replacement);
        reject(NATIVE_QA_ADDRESS.replace('Y','0'));
        reject(NATIVE_QA_ADDRESS.replace('Y','O'));
        reject(NATIVE_QA_ADDRESS.replace('Y','I'));
        reject(NATIVE_QA_ADDRESS.replace('Y','l'));
        reject(NATIVE_QA_ADDRESS + "1");
        reject(" " + NATIVE_QA_ADDRESS);
        reject(NATIVE_QA_ADDRESS.substring(1));
        reject("");
        reject(null);
    }

    @Test public void rejectChecksumValidButOtherChainOrWrongLength() {
        FrgPublicAddress.Result standard = FrgPublicAddress.parse(NATIVE_QA_ADDRESS);
        // Correct checksum is insufficient: only selected native prefixes
        // and corresponding exact payload types are permitted.
        reject(encode(193, standard.spendPublicKey(),standard.viewPublicKey(),null));
        reject(encode(191, standard.spendPublicKey(),standard.viewPublicKey(),null));
        reject(encode(190, standard.spendPublicKey(),standard.viewPublicKey(),
                      "12345678".getBytes(StandardCharsets.US_ASCII)));
    }
}
