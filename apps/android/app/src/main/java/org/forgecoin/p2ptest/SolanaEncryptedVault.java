package org.forgecoin.p2ptest;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
/** Keystore-backed authenticated encryption. Device-bound; mnemonic backup required. */
public final class SolanaEncryptedVault {
 private static final String STORE="AndroidKeyStore",ALIAS="forgecoin.solana.v1";
 private SolanaEncryptedVault(){}
 private static SecretKey key() throws Exception {
  KeyStore store=KeyStore.getInstance(STORE);store.load(null);
  SecretKey existing=(SecretKey)store.getKey(ALIAS,null);
  if(existing!=null)return existing;
  KeyGenerator generator=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,STORE);
  generator.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
      .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
      .setKeySize(256).build());
  return generator.generateKey();
 }
 public static String encrypt(byte[] plaintext) throws Exception {
  if(plaintext==null||plaintext.length==0)throw new IllegalArgumentException("Empty vault material");
  Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,key());
  return "forgecoin-solana-android-gcm-v1:"+Base64.encodeToString(cipher.getIV(),Base64.NO_WRAP)+":"+
    Base64.encodeToString(cipher.doFinal(plaintext),Base64.NO_WRAP);
 }
 public static byte[] decrypt(String envelope) throws Exception {
  if(envelope==null||!envelope.startsWith("forgecoin-solana-android-gcm-v1:"))throw new IllegalArgumentException("Unsupported vault format");
  String[] parts=envelope.split(":",-1);if(parts.length!=3)throw new IllegalArgumentException("Invalid vault envelope");
  byte[] iv=Base64.decode(parts[1],Base64.NO_WRAP),ct=Base64.decode(parts[2],Base64.NO_WRAP);
  if(iv.length!=12||ct.length<17||ct.length>65536)throw new IllegalArgumentException("Invalid envelope size");
  Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,iv));
  return cipher.doFinal(ct);
 }
}
