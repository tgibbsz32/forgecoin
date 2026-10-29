package org.forgecoin.p2ptest;
/** Standalone JDK regression check: no Android runtime, JUnit or real wallet required. */
public final class SolanaSlip10Smoke {
 private static String hex(byte[] a){StringBuilder b=new StringBuilder();for(byte x:a)b.append(String.format("%02x",x&255));return b.toString();}
 public static void main(String[] args) throws Exception {
  String p="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
  byte[] seed=SolanaSlip10.derive(p,"",0);
  if(!hex(seed).equals("37df573b3ac4ad5b522e064e25b63ea16bcbe79d449e81a0268d1047948bb445"))
   throw new AssertionError("Solana SLIP10 deterministic reference mismatch");
  if(java.util.Arrays.equals(seed,SolanaSlip10.derive(p,"",1)))throw new AssertionError("Account separation failed");
  System.out.println("ANDROID_SLIP10_REFERENCE_VECTOR_OK");
  java.util.Arrays.fill(seed,(byte)0);
 }
}
