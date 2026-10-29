package org.forgecoin.p2ptest;
import org.junit.Test;
import static org.junit.Assert.*;
public class FrgAmountTest {
 @Test public void exactConsensusUnits() {
  assertEquals("1",FrgAmount.parsePositiveAtomic("0.00000001"));
  assertEquals("100000000",FrgAmount.parsePositiveAtomic("1"));
  assertEquals("123456789",FrgAmount.parsePositiveAtomic("1.23456789"));
  assertEquals("5000000000000000",FrgAmount.parsePositiveAtomic("50000000"));
  assertEquals("18446744073709551615",FrgAmount.parsePositiveAtomic("184467440737.09551615"));
 }
 @Test public void rejectRoundingOverflowAndAmbiguousInput() {
  for(String bad:new String[]{null,"","0","0.00000000","-1","+1","01","1e2"," 1","1 ",".1","1.","0.000000001","184467440737.09551616","999999999999999999999999999999","NaN"})
   assertThrows(IllegalArgumentException.class,() -> FrgAmount.parsePositiveAtomic(bad));
 }
}
