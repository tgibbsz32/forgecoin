package org.forgecoin.p2ptest;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.util.Arrays;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
/** Hardened SLIP-0010 Ed25519 seed for m/44'/501'/account'/0'. No persistence. */
public final class SolanaSlip10 {
 private SolanaSlip10(){}
 private static byte[] hmac(byte[] key,byte[] message) throws GeneralSecurityException {
  Mac mac=Mac.getInstance("HmacSHA512");mac.init(new SecretKeySpec(key,"HmacSHA512"));return mac.doFinal(message);
 }
 public static byte[] derive(String mnemonic,String passphrase,int account) throws GeneralSecurityException {
  if(account<0)throw new IllegalArgumentException("Account must be nonnegative");
  byte[] bip39=SolanaBip39Seed.derive(mnemonic,passphrase);
  byte[] master=null,key=new byte[32],chain=new byte[32];
  try {
   master=hmac("ed25519 seed".getBytes(StandardCharsets.US_ASCII),bip39);
   System.arraycopy(master,0,key,0,32);System.arraycopy(master,32,chain,0,32);
   long[] path={44,501,account,0};
   for(long step:path){
    long index=step|0x80000000L;
    byte[] data=new byte[37];data[0]=0;System.arraycopy(key,0,data,1,32);
    data[33]=(byte)(index>>>24);data[34]=(byte)(index>>>16);data[35]=(byte)(index>>>8);data[36]=(byte)index;
    byte[] result=hmac(chain,data);
    System.arraycopy(result,0,key,0,32);System.arraycopy(result,32,chain,0,32);
    Arrays.fill(result,(byte)0);Arrays.fill(data,(byte)0);
   }
   return key.clone();
  } finally {
   Arrays.fill(bip39,(byte)0);if(master!=null)Arrays.fill(master,(byte)0);
   Arrays.fill(key,(byte)0);Arrays.fill(chain,(byte)0);
  }
 }
}
