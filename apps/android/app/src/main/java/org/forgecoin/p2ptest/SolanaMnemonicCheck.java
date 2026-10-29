package org.forgecoin.p2ptest;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;
/** Standalone BIP39 English wordlist/checksum verification; never logs seed words. */
public final class SolanaMnemonicCheck {
 private SolanaMnemonicCheck(){}
 public static String[] load(InputStream stream) throws IOException {
  if(stream==null)throw new IOException("Wordlist missing");
  ArrayList<String> words=new ArrayList<>();
  try(BufferedReader r=new BufferedReader(new InputStreamReader(stream,StandardCharsets.UTF_8))){
   String line;while((line=r.readLine())!=null)words.add(line);
  }
  if(words.size()!=2048||!words.get(0).equals("abandon")||!words.get(2047).equals("zoo")||
      new HashSet<>(words).size()!=2048)throw new IOException("Invalid BIP39 wordlist");
  return words.toArray(new String[0]);
 }
 public static boolean valid(String mnemonic,String[] words) throws GeneralSecurityException {
  if(mnemonic==null||words==null||words.length!=2048)return false;
  String[] tokens=mnemonic.split(" ",-1);int n=tokens.length;
  if(n!=12&&n!=15&&n!=18&&n!=21&&n!=24)return false;
  Map<String,Integer> indexes=new HashMap<>();
  for(int i=0;i<2048;i++)indexes.put(words[i],i);
  int entropyBits=n*32/3,checksumBits=entropyBits/32;
  byte[] entropy=new byte[entropyBits/8];int[] bits=new int[n*11];int k=0;
  for(String token:tokens){Integer idx=indexes.get(token);if(idx==null)return false;
   for(int b=10;b>=0;b--)bits[k++]=(idx>>>b)&1;
  }
  for(int i=0;i<entropyBits;i++)if(bits[i]!=0)entropy[i/8]|=(byte)(1<<(7-i%8));
  byte[] digest=MessageDigest.getInstance("SHA-256").digest(entropy);
  int result=0;
  for(int i=0;i<checksumBits;i++)result|=bits[entropyBits+i]^((digest[i/8]>>>(7-i%8))&1);
  Arrays.fill(entropy,(byte)0);Arrays.fill(digest,(byte)0);Arrays.fill(bits,0);
  return result==0;
 }
}
