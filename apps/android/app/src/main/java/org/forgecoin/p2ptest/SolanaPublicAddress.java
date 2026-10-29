package org.forgecoin.p2ptest;
import java.math.BigInteger;
import java.util.Arrays;
import org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters;

/** Solana public address using Bouncy Castle Ed25519, not custom curve arithmetic. */
public final class SolanaPublicAddress {
 private SolanaPublicAddress(){}
 public static String fromPhrase(String phrase,String[] englishWords,int account) throws Exception {
  byte[] seed=SolanaRecoveryCore.recover(phrase,englishWords,account);
  try {
   byte[] pub=new Ed25519PrivateKeyParameters(seed,0).generatePublicKey().getEncoded();
   try{return base58(pub);}finally{Arrays.fill(pub,(byte)0);}
  } finally {Arrays.fill(seed,(byte)0);}
 }
 public static String base58(byte[] data){
  final String alphabet="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  BigInteger value=new BigInteger(1,data);StringBuilder s=new StringBuilder();
  while(value.signum()>0){BigInteger[] qr=value.divideAndRemainder(BigInteger.valueOf(58));s.append(alphabet.charAt(qr[1].intValue()));value=qr[0];}
  for(byte b:data){if(b!=0)break;s.append('1');}
  return s.reverse().toString();
 }
}
