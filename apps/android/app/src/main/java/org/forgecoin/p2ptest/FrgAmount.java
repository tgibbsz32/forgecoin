package org.forgecoin.p2ptest;

import java.math.BigInteger;

/** Offline send-amount preparation only. Does not create, sign or broadcast transactions. */
public final class FrgAmount {
 // src/cryptonote_config.h: CRYPTONOTE_DISPLAY_DECIMAL_POINT=8, COIN=100000000.
 private static final BigInteger COIN=BigInteger.valueOf(100000000L);
 private static final BigInteger UINT64_MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
 private FrgAmount() {}
 /** Returns the unsigned decimal atomic amount expected by native wallet RPC, without floating point. */
 public static String parsePositiveAtomic(String value) {
  if(value==null || value.length()>29 || !value.matches("(0|[1-9][0-9]*)(\\.[0-9]{1,8})?"))
   throw new IllegalArgumentException("Invalid FRG amount");
  String[] fields=value.split("\\.",-1);
  BigInteger amount=new BigInteger(fields[0]).multiply(COIN);
  if(fields.length==2) {
   String fraction=fields[1];
   while(fraction.length()<8)fraction+="0";
   amount=amount.add(new BigInteger(fraction));
  }
  if(amount.signum()<=0 || amount.compareTo(UINT64_MAX)>0)
   throw new IllegalArgumentException("FRG amount outside unsigned 64-bit range");
  return amount.toString();
 }
}
