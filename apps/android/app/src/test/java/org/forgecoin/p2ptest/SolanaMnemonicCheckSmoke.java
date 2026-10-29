package org.forgecoin.p2ptest;
import java.io.FileInputStream;
public final class SolanaMnemonicCheckSmoke {
 public static void main(String[] args) throws Exception {
  String[] words=SolanaMnemonicCheck.load(new FileInputStream(args[0]));
  String known="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
  if(!SolanaMnemonicCheck.valid(known,words))throw new AssertionError("Known BIP39 phrase rejected");
  if(SolanaMnemonicCheck.valid(known.replace("about","zoo"),words))throw new AssertionError("Invalid checksum accepted");
  if(SolanaMnemonicCheck.valid("invalid words",words))throw new AssertionError("Unknown words accepted");
  System.out.println("ANDROID_BIP39_CHECKSUM_REFERENCE_PASS");
 }
}
