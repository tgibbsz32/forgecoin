package org.forgecoin.p2ptest;

import android.os.Build;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/**
 * Experimental v2 key for an authenticated per-operation CryptoObject flow.
 * Do not use with the legacy v1 vault format; an authenticated prompt must
 * finish successfully with the initialized Cipher before doFinal is called.
 */
public final class SolanaAuthenticatedKey {
 private static final String ALIAS="forgecoin.solana.auth.v2";
 private SolanaAuthenticatedKey() {}
 private static SecretKey getKey() throws Exception {
  if(Build.VERSION.SDK_INT<30)throw new UnsupportedOperationException("API 30+ required");
  KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);
  SecretKey key=(SecretKey)ks.getKey(ALIAS,null);
  if(key!=null)return key;
  KeyGenerator gen=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
  KeyGenParameterSpec spec=new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
   .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
   .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
   .setKeySize(256)
   .setUserAuthenticationRequired(true)
   .setUserAuthenticationParameters(0,KeyProperties.AUTH_BIOMETRIC_STRONG)
   .build();
  gen.init(spec);
  return gen.generateKey();
 }
 public static Cipher beginEncrypt() throws Exception {
  Cipher c=Cipher.getInstance("AES/GCM/NoPadding");
  c.init(Cipher.ENCRYPT_MODE,getKey());
  return c;
 }
 public static Cipher beginDecrypt(byte[] iv) throws Exception {
  if(iv==null||iv.length!=12)throw new IllegalArgumentException("Invalid IV");
  Cipher c=Cipher.getInstance("AES/GCM/NoPadding");
  c.init(Cipher.DECRYPT_MODE,getKey(),new GCMParameterSpec(128,iv));
  return c;
 }
}
