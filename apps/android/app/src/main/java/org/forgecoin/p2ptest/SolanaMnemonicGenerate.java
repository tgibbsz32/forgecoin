package org.forgecoin.p2ptest;
import java.security.*;
import java.util.*;
/** BIP39 English 12-word generation with checksum and independent CSPRNG. */
public final class SolanaMnemonicGenerate {
 private SolanaMnemonicGenerate(){}
 public static String fromEntropy(byte[] entropy,String[] words)throws Exception{
  if(entropy==null||entropy.length!=16||words==null||words.length!=2048)throw new IllegalArgumentException("Expected 128-bit entropy and BIP39 words");
  byte[] checksum=MessageDigest.getInstance("SHA-256").digest(entropy);
  StringBuilder out=new StringBuilder();
  for(int i=0;i<12;i++){
   int index=0;
   for(int j=0;j<11;j++){
    int b=i*11+j;
    int bit=b<128?((entropy[b/8]>>>(7-b%8))&1):((checksum[0]>>>(7-(b-128)))&1);
    index=(index<<1)|bit;
   }
   if(i!=0)out.append(' ');out.append(words[index]);
  }
  Arrays.fill(checksum,(byte)0);return out.toString();
 }
 public static String create(String[] words)throws Exception{
  byte[] entropy=new byte[16];new SecureRandom().nextBytes(entropy);
  try{return fromEntropy(entropy,words);}finally{Arrays.fill(entropy,(byte)0);}
 }
}
