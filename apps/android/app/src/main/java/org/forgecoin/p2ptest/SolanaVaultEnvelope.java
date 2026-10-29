package org.forgecoin.p2ptest;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

/** Strict v2 wire format. Header is authenticated as GCM additional data. */
public final class SolanaVaultEnvelope {
 public static final String HEADER="forgecoin-solana-android-auth-gcm-v2";
 public static final int MAX_PLAINTEXT=65520;
 private final byte[] iv, ciphertext;
 private SolanaVaultEnvelope(byte[] iv, byte[] ciphertext) {
  this.iv=iv.clone(); this.ciphertext=ciphertext.clone();
 }
 public static byte[] aad() { return HEADER.getBytes(StandardCharsets.US_ASCII); }
 public byte[] iv() { return iv.clone(); }
 public byte[] ciphertext() { return ciphertext.clone(); }
 public static SolanaVaultEnvelope of(byte[] iv, byte[] ciphertext) {
  if(iv==null || iv.length!=12 || ciphertext==null || ciphertext.length<17 || ciphertext.length>65536)
   throw new IllegalArgumentException("Invalid v2 vault size");
  return new SolanaVaultEnvelope(iv,ciphertext);
 }
 public String encode() {
  return HEADER+":"+Base64.getEncoder().encodeToString(iv)+":"+Base64.getEncoder().encodeToString(ciphertext);
 }
 public static SolanaVaultEnvelope parse(String value) {
  if(value==null || value.length()>87440) throw new IllegalArgumentException("Invalid v2 vault size");
  String[] fields=value.split(":",-1);
  if(fields.length!=3 || !HEADER.equals(fields[0])) throw new IllegalArgumentException("Unsupported vault format");
  byte[] iv=Base64.getDecoder().decode(fields[1]), ct=Base64.getDecoder().decode(fields[2]);
  SolanaVaultEnvelope result=of(iv,ct);
  if(!result.encode().equals(value)) throw new IllegalArgumentException("Noncanonical vault encoding");
  return result;
 }
}
