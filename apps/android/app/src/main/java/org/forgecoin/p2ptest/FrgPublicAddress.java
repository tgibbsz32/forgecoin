package org.forgecoin.p2ptest;

import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.Arrays;
import org.bouncycastle.crypto.digests.KeccakDigest;

/**
 * Native FRG CryptoNote public-address decoder, CHECKSUM/PREFIX ONLY.
 * Uses 8-byte-block CryptoNote Base58 and Keccak-256 (NOT SHA3-256).
 *
 * A valid checksum is not evidence of a real wallet, key ownership, live
 * network, an acceptable Ed25519 curve point, or a spendable output.
 * No private/seed material, RPC, networking or address generation.
 */
public final class FrgPublicAddress {
    private FrgPublicAddress() {}

    private static final String ALPHABET =
        "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
    private static final BigInteger FIFTY_EIGHT = BigInteger.valueOf(58);
    // Base58 block lengths for 1..8 binary bytes.
    private static final int[] ENCODED = {0, 2, 3, 5, 6, 7, 9, 10, 11};
    // Lengths of the decoded binary blocks for an encoded last block.
    private static final int[] DECODED = {0, -1, 1, 2, -1, 3, 4, 5, -1, 6, 7, 8};

    public enum Kind { STANDARD, INTEGRATED, SUBADDRESS }

    public static final class Result {
        public final Kind kind;
        public final int networkPrefix;
        public final String canonicalAddress;
        private final byte[] publicSpendKey;
        private final byte[] publicViewKey;
        private final byte[] shortPaymentId;

        private Result(Kind kind, int prefix, String address, byte[] decoded) {
            this.kind = kind;
            this.networkPrefix = prefix;
            this.canonicalAddress = address;
            this.publicSpendKey = Arrays.copyOfRange(decoded, 2, 34);
            this.publicViewKey = Arrays.copyOfRange(decoded, 34, 66);
            this.shortPaymentId = kind == Kind.INTEGRATED ?
                Arrays.copyOfRange(decoded, 66, 74) : null;
        }

        public byte[] spendPublicKey() { return publicSpendKey.clone(); }
        public byte[] viewPublicKey() { return publicViewKey.clone(); }
        public byte[] integratedPaymentId() {
            return shortPaymentId == null ? null : shortPaymentId.clone();
        }
    }

    private static IllegalArgumentException invalid() {
        return new IllegalArgumentException("Invalid FRG public address format or checksum.");
    }

    static byte[] keccak256(byte[] message) {
        if (message == null) throw new IllegalArgumentException("Missing input.");
        KeccakDigest digest = new KeccakDigest(256);
        digest.update(message, 0, message.length);
        byte[] result = new byte[32];
        digest.doFinal(result, 0);
        return result;
    }

    private static int blockLength(int encodedLength) {
        return encodedLength >= 0 && encodedLength < DECODED.length ?
            DECODED[encodedLength] : -1;
    }

    private static byte[] decodeBase58(String input) {
        if (input == null || input.length() < 97 || input.length() > 108)
            throw invalid();
        int full = input.length() / ENCODED[8];
        int tail = input.length() % ENCODED[8];
        int tailBytes = blockLength(tail);
        if (tailBytes < 0) throw invalid();
        byte[] decoded = new byte[full * 8 + tailBytes];
        int offset = 0, index = 0;
        while (index < input.length()) {
            int digits = Math.min(11, input.length() - index);
            int bytes = blockLength(digits);
            if (bytes < 0) throw invalid();
            BigInteger number = BigInteger.ZERO;
            for (int j = 0; j < digits; j++) {
                int base58 = ALPHABET.indexOf(input.charAt(index + j));
                if (base58 < 0) throw invalid();
                number = number.multiply(FIFTY_EIGHT).add(BigInteger.valueOf(base58));
            }
            if (number.bitLength() > bytes * 8) throw invalid();
            byte[] encodedInteger = number.toByteArray();
            int src = 0;
            // BigInteger may prepend one sign byte; reject any nonzero overflow.
            if (encodedInteger.length > bytes) {
                if (encodedInteger.length != bytes + 1 || encodedInteger[0] != 0)
                    throw invalid();
                src = 1;
            }
            int meaningful = encodedInteger.length - src;
            System.arraycopy(encodedInteger, src, decoded,
                             offset + bytes - meaningful, meaningful);
            index += digits;
            offset += bytes;
        }
        return decoded;
    }

    /**
     * Verify selected frozen 20261026 FRG mainnet prefixes and checksum.
     *
     * This does not perform elliptic-curve point validation. The actual native
     * wallet and daemon must independently validate any address used to spend.
     */
    public static Result parse(String publicAddress) {
        byte[] decoded = decodeBase58(publicAddress);
        if (decoded.length < 70 || decoded.length > 78 ||
            (decoded.length != 70 && decoded.length != 78))
            throw invalid();
        // Canonical ULEB128 of 190, 191 and 192; exact 2-byte prefixes.
        if ((decoded[1] & 255) != 1) throw invalid();
        int first = decoded[0] & 255;
        Kind kind;
        int prefix;
        if (first == 0xBE && decoded.length == 70) {
            prefix = 190; kind = Kind.STANDARD;
        } else if (first == 0xBF && decoded.length == 78) {
            prefix = 191; kind = Kind.INTEGRATED;
        } else if (first == 0xC0 && decoded.length == 70) {
            prefix = 192; kind = Kind.SUBADDRESS;
        } else {
            throw invalid();
        }
        int end = decoded.length - 4;
        byte[] check = keccak256(Arrays.copyOf(decoded, end));
        byte[] given = Arrays.copyOfRange(decoded, end, decoded.length);
        if (!MessageDigest.isEqual(Arrays.copyOf(check, 4), given))
            throw invalid();
        return new Result(kind, prefix, publicAddress, decoded);
    }
}
