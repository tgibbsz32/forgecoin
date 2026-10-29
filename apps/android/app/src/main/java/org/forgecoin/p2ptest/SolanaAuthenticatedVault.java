package org.forgecoin.p2ptest;

import javax.crypto.Cipher;
import java.util.Arrays;

/** Pending, single-use operation; never persists or migrates existing wallets. */
public final class SolanaAuthenticatedVault {
 private SolanaAuthenticatedVault() {}
 public static Operation encrypt(byte[] plaintext) throws Exception {
  if(plaintext==null || plaintext.length==0 || plaintext.length>SolanaVaultEnvelope.MAX_PLAINTEXT)
   throw new IllegalArgumentException("Invalid vault material size");
  return new Operation(SolanaAuthenticatedKey.beginEncrypt(),plaintext,true);
 }
 public static Operation decrypt(String value) throws Exception {
  SolanaVaultEnvelope envelope=SolanaVaultEnvelope.parse(value);
  return new Operation(SolanaAuthenticatedKey.beginDecrypt(envelope.iv()),envelope.ciphertext(),false);
 }
 public static final class Operation implements AutoCloseable {
  private final Cipher cipher;
  private byte[] input;
  private final boolean encrypt;
  Operation(Cipher cipher,byte[] input,boolean encrypt) {
   this.cipher=cipher; this.input=input.clone(); this.encrypt=encrypt;
  }
  public synchronized Cipher cipher() {
   if(input==null)throw new IllegalStateException("Operation consumed");
   return cipher;
  }
  /** Caller supplies the exact Cipher returned by the successful CryptoObject prompt. */
  public synchronized byte[] finish(Cipher authenticatedCipher) throws Exception {
   if(input==null)throw new IllegalStateException("Operation consumed");
   try {
    if(authenticatedCipher!=cipher)throw new SecurityException("Authentication cipher mismatch");
    byte[] result=cipher.doFinal(input);
    if(!encrypt)return result;
    return SolanaVaultEnvelope.of(cipher.getIV(),result).encode().getBytes(java.nio.charset.StandardCharsets.US_ASCII);
   } finally { close(); }
  }
  @Override public synchronized void close() {
   if(input!=null) { Arrays.fill(input,(byte)0); input=null; }
  }
 }
}
