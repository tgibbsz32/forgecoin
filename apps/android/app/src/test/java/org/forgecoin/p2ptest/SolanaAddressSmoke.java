package org.forgecoin.p2ptest;
public final class SolanaAddressSmoke {
 public static void main(String[] args){
  byte[] zero=new byte[32];String value=SolanaAddress.encode(zero);
  if(!value.equals("11111111111111111111111111111111"))throw new AssertionError("zero key Base58 mismatch");
  byte[] one=new byte[32];one[31]=1;
  if(!SolanaAddress.encode(one).equals("11111111111111111111111111111112"))throw new AssertionError("one key Base58 mismatch");
  System.out.println("SOLANA_BASE58_PUBLIC_ADDRESS_ENCODING_PASS");
 }
}
