package org.forgecoin.p2ptest;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.util.Arrays;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import android.util.Base64;

/**
 * Encrypted local storage for an eventual reviewed native FRG wallet seed.
 * Does not derive FRG keys, create wallets, or enable spending.
 * The Android Keystore key is device-bound; a recovery phrase must be backed
 * up separately by the user. No seed is logged or placed in an Intent.
 */
public final class FrgSeedVault {
    private static final String ALIAS = "frg-wallet-v1";
    private static final String PREFS = "frg-encrypted-vault";
    private static final String IV = "iv";
    private static final String DATA = "ciphertext";
    private FrgSeedVault() {}

    private static SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        KeyStore.Entry entry = store.getEntry(ALIAS, null);
        if (entry instanceof KeyStore.SecretKeyEntry)
            return ((KeyStore.SecretKeyEntry) entry).getSecretKey();
        KeyGenerator generator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS,
            KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setRandomizedEncryptionRequired(true)
            .build());
        return generator.generateKey();
    }

    public static synchronized void save(Context context, char[] seed) throws Exception {
        if (seed == null || seed.length == 0) throw new IllegalArgumentException("Empty seed");
        validateRecoveryPhrase(seed);
        if (exists(context))
            throw new IllegalStateException("A wallet backup already exists; refusing to overwrite it");
        byte[] plaintext = new String(seed).getBytes(StandardCharsets.UTF_8);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, key(), new SecureRandom());
            byte[] encrypted = cipher.doFinal(plaintext);
            SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
            if (!prefs.edit().putString(IV, Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
                .putString(DATA, Base64.encodeToString(encrypted, Base64.NO_WRAP)).commit())
                throw new IllegalStateException("Unable to persist encrypted wallet seed");
            Arrays.fill(encrypted, (byte) 0);
        } finally {
            Arrays.fill(plaintext, (byte) 0);
        }
    }

    public static synchronized char[] load(Context context) throws Exception {
        SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String iv = prefs.getString(IV, null), ciphertext = prefs.getString(DATA, null);
        if (iv == null || ciphertext == null) throw new IllegalStateException("No local wallet backup");
        byte[] nonce = Base64.decode(iv, Base64.NO_WRAP);
        if (nonce.length != 12) throw new IllegalStateException("Invalid vault nonce");
        byte[] encrypted = Base64.decode(ciphertext, Base64.NO_WRAP);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, nonce));
        byte[] plaintext = cipher.doFinal(encrypted);
        try { return new String(plaintext, StandardCharsets.UTF_8).toCharArray(); }
        finally { Arrays.fill(plaintext, (byte) 0); }
    }

    /** Structural check only: the native wallet must validate mnemonic words,
     * checksum, language and derive keys before accepting a restored wallet. */
    public static void validateRecoveryPhrase(char[] phrase) {
        if (phrase == null) throw new IllegalArgumentException("Recovery phrase required");
        String normalized = new String(phrase).trim();
        if (normalized.isEmpty()) throw new IllegalArgumentException("Recovery phrase required");
        String[] words = normalized.split("\\s+");
        if (words.length != 25)
            throw new IllegalArgumentException("ForgeCoin recovery phrase must contain 25 words");
        for (String word : words)
            if (!word.matches("[\\p{L}]+"))
                throw new IllegalArgumentException("Recovery phrase contains invalid characters");
    }

    public static synchronized boolean exists(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return prefs.contains(IV) && prefs.contains(DATA);
    }
}
