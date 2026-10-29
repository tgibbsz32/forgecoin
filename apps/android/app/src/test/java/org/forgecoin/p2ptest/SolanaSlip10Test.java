package org.forgecoin.p2ptest;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.Arrays;
public class SolanaSlip10Test {
 private static String hex(byte[] a){StringBuilder s=new StringBuilder();for(byte b:a)s.append(String.format("%02x",b&255));return s.toString();}
 @Test public void deterministicAndAccountSeparated() throws Exception {
  String p="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
  byte[] a=SolanaSlip10.derive(p,"",0),b=SolanaSlip10.derive(p,"",0),c=SolanaSlip10.derive(p,"",1);
  assertEquals(32,a.length);assertArrayEquals(a,b);assertFalse(Arrays.equals(a,c));
 }
 @Test(expected=IllegalArgumentException.class) public void rejectsNegativeAccount() throws Exception {
  SolanaSlip10.derive("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about","",-1);
 }
}
