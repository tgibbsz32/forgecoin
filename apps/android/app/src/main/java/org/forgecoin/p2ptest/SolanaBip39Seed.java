package org.forgecoin.p2ptest;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.text.Normalizer;
import java.util.Arrays;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/** BIP39 mnemonic-to-seed component. No key persistence, signing or network access. */
public final class SolanaBip39Seed {
    private SolanaBip39Seed() {}
    public static byte[] derive(String mnemonic, String passphrase) throws GeneralSecurityException {
        if (mnemonic == null || mnemonic.trim().isEmpty()) throw new IllegalArgumentException("Mnemonic required");
        String input = Normalizer.normalize(mnemonic, Normalizer.Form.NFKD);
        String saltText = Normalizer.normalize("mnemonic" + (passphrase == null ? "" : passphrase), Normalizer.Form.NFKD);
        byte[] pwd = input.getBytes(StandardCharsets.UTF_8);
        byte[] salt = saltText.getBytes(StandardCharsets.UTF_8);
        byte[] block = new byte[salt.length + 4];
        byte[] output = new byte[64];
        try {
            System.arraycopy(salt, 0, block, 0, salt.length);
            block[block.length - 1] = 1;
            Mac mac = Mac.getInstance("HmacSHA512");
            mac.init(new SecretKeySpec(pwd,"HmacSHA512"));
            byte[] u = mac.doFinal(block);
            byte[] t = u.clone();
            for (int i=1;i<2048;i++) {
                byte[] next = mac.doFinal(u);
                Arrays.fill(u,(byte)0);
                u = next;
                for (int j=0;j<64;j++) t[j] ^= u[j];
            }
            System.arraycopy(t,0,output,0,64);
            Arrays.fill(u,(byte)0);Arrays.fill(t,(byte)0);
            return output;
        } finally {
            Arrays.fill(pwd,(byte)0);Arrays.fill(salt,(byte)0);
            Arrays.fill(block,(byte)0);
        }
    }
}
