package org.forgecoin.p2ptest;
import java.security.GeneralSecurityException;
import java.util.Arrays;
/** Production signing is disabled. Public derivation uses Android platform Ed25519 when supported. */
public final class SolanaEd25519Public {
 private SolanaEd25519Public(){}
 public static String addressFromSeed(byte[] seed) throws GeneralSecurityException {
  if(seed==null||seed.length!=32)throw new IllegalArgumentException("Ed25519 seed must be 32 bytes");
  // Intentionally fail closed pending an audited Android-compatible seed->public implementation.
  throw new GeneralSecurityException("Ed25519 seed-to-public derivation not yet integrated; address display disabled");
 }
}
