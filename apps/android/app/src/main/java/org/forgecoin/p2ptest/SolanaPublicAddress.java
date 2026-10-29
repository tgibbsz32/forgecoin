package org.forgecoin.p2ptest;
import java.math.BigInteger;
import java.security.*;
import java.security.spec.*;
import java.util.Arrays;

/** Deterministic Ed25519 public key and Solana base58 public address. No signing or wallet storage. */
public final class SolanaPublicAddress {
 private SolanaPublicAddress(){}
 private static final BigInteger P=BigInteger.ONE.shiftLeft(255).subtract(BigInteger.valueOf(19));
 private static final BigInteger D=BigInteger.valueOf(-121665).multiply(BigInteger.valueOf(121666).modInverse(P)).mod(P);
 private static final BigInteger BX=new BigInteger("15112221349535400772501151409588531511454012693041857206046113283949847762202");
 private static final BigInteger BY=new BigInteger("46316835694926478169428394003475163141307993866256225615783033603165251855960");
 private static final class Point {
  final BigInteger x,y;
  Point(BigInteger x,BigInteger y){this.x=x;this.y=y;}
 }
 private static Point add(Point a,Point b){
  BigInteger xy=a.x.multiply(b.x).multiply(a.y).multiply(b.y).mod(P).multiply(D).mod(P);
  BigInteger x=a.x.multiply(b.y).add(a.y.multiply(b.x)).mod(P).multiply(BigInteger.ONE.add(xy).mod(P).modInverse(P)).mod(P);
  BigInteger y=a.y.multiply(b.y).add(a.x.multiply(b.x)).mod(P).multiply(BigInteger.ONE.subtract(xy).mod(P).modInverse(P)).mod(P);
  return new Point(x,y);
 }
 private static byte[] publicKey(byte[] seed) throws Exception {
  if(seed==null||seed.length!=32)throw new IllegalArgumentException("Ed25519 seed length");
  byte[] digest=MessageDigest.getInstance("SHA-512").digest(seed);
  digest[0]&=(byte)248; digest[31]&=(byte)63; digest[31]|=(byte)64;
  BigInteger scalar=BigInteger.ZERO;
  for(int i=31;i>=0;i--)scalar=scalar.shiftLeft(8).add(BigInteger.valueOf(digest[i]&255));
  Point sum=new Point(BigInteger.ZERO,BigInteger.ONE),base=new Point(BX,BY);
  for(int i=0;i<255;i++){if(scalar.testBit(i))sum=add(sum,base);base=add(base,base);}
  byte[] out=new byte[32];BigInteger y=sum.y;
  for(int i=0;i<32;i++){out[i]=y.byteValue();y=y.shiftRight(8);}
  if(sum.x.testBit(0))out[31]|=(byte)128;
  Arrays.fill(digest,(byte)0);return out;
 }
 public static String fromPhrase(String phrase,String[] englishWords,int account) throws Exception {
  byte[] seed=SolanaRecoveryCore.recover(phrase,englishWords,account);
  try{return base58(publicKey(seed));}finally{Arrays.fill(seed,(byte)0);}
 }
 public static String base58(byte[] data){
  final String alphabet="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  BigInteger value=new BigInteger(1,data);StringBuilder s=new StringBuilder();
  while(value.signum()>0){BigInteger[] qr=value.divideAndRemainder(BigInteger.valueOf(58));s.append(alphabet.charAt(qr[1].intValue()));value=qr[0];}
  for(byte b:data){if(b!=0)break;s.append('1');}
  return s.reverse().toString();
 }
}
