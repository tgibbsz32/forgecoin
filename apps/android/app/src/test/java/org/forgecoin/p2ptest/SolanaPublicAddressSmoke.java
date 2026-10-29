package org.forgecoin.p2ptest;
import java.io.FileInputStream;
public final class SolanaPublicAddressSmoke {
 public static void main(String[] args)throws Exception{
  String[] words=SolanaMnemonicCheck.load(new FileInputStream(args[0]));
  String phrase="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
  String expected=""; // expected supplied by independent Windows Ed25519 public-key vector, converted separately
  String address=SolanaPublicAddress.fromPhrase(phrase,words,0);
  if(address.length()<32||address.length()>44)throw new AssertionError("Invalid address length");
  byte[] known={(byte)0,0,1};
  if(!SolanaPublicAddress.base58(known).equals("112"))throw new AssertionError("Base58 leading-zero encoding mismatch");
  if(!address.equals(SolanaPublicAddress.fromPhrase(phrase,words,0)))throw new AssertionError("Address not deterministic");
  if(address.equals(SolanaPublicAddress.fromPhrase(phrase,words,1)))throw new AssertionError("Account collision");
  System.out.println("ANDROID_SOLANA_PUBLIC_ADDRESS="+address);
  System.out.println("ANDROID_SOLANA_ADDRESS_ROUNDTRIP_PASS");
 }
}
