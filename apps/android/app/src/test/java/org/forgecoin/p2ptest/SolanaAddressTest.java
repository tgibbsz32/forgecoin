package org.forgecoin.p2ptest;
import org.junit.Test;
import static org.junit.Assert.*;
public class SolanaAddressTest {
 @Test public void base58AllZeroAndOne() {
  byte[] zeros=new byte[32];
  assertEquals("11111111111111111111111111111111",SolanaAddress.encode(zeros));
  zeros[31]=1;
  assertEquals("11111111111111111111111111111112",SolanaAddress.encode(zeros));
 }
 @Test(expected=IllegalArgumentException.class) public void wrongKeySizeRejected() {
  SolanaAddress.encode(new byte[31]);
 }
 @Test(expected=java.security.GeneralSecurityException.class) public void unsignedAddressDerivationFailsClosed() throws Exception {
  SolanaEd25519Public.addressFromSeed(new byte[32]);
 }
}
