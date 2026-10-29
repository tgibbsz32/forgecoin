package org.forgecoin.p2ptest;
import java.math.BigInteger;
import java.security.GeneralSecurityException;
import java.util.Arrays;
/** Base58 encoding for an independently derived 32-byte Ed25519 public key. */
public final class SolanaAddress {
 private static final String ALPHABET="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
 private SolanaAddress(){}
 public static String encode(byte[] publicKey){
  if(publicKey==null||publicKey.length!=32)throw new IllegalArgumentException("Ed25519 public key must be 32 bytes");
  int zeros=0;while(zeros<32&&publicKey[zeros]==0)zeros++;
  BigInteger value=new BigInteger(1,publicKey);
  StringBuilder result=new StringBuilder();
  BigInteger base=BigInteger.valueOf(58);
  while(value.signum()>0){BigInteger[] div=value.divideAndRemainder(base);result.append(ALPHABET.charAt(div[1].intValue()));value=div[0];}
  for(int i=0;i<zeros;i++)result.append('1');
  return result.reverse().toString();
 }
}
