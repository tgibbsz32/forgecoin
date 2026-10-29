package org.forgecoin.p2ptest;
import java.io.FileInputStream;
import java.util.Arrays;
public final class SolanaRecoveryCoreSmoke {
 public static void main(String[] args) throws Exception {
  String[] words=SolanaMnemonicCheck.load(new FileInputStream(args[0]));
  String phrase="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
  byte[] checked=SolanaRecoveryCore.recover(phrase,words,0);
  byte[] direct=SolanaSlip10.derive(phrase,"",0);
  if(!Arrays.equals(checked,direct))throw new AssertionError("Recovery divergence");
  boolean rejected=false;
  try{SolanaRecoveryCore.recover(phrase.replace("about","zoo"),words,0);}
  catch(IllegalArgumentException expected){rejected=true;}
  if(!rejected)throw new AssertionError("Invalid recovery accepted");
  Arrays.fill(checked,(byte)0);Arrays.fill(direct,(byte)0);
  System.out.println("ANDROID_VALIDATED_RECOVERY_CORE_PASS");
 }
}
