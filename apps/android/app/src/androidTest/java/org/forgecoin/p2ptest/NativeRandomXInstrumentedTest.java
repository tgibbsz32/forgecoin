package org.forgecoin.p2ptest;
import static org.junit.Assert.*;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import org.junit.Test;
import org.junit.runner.RunWith;
/** Tests a repeatable native light-VM hash on actual ARM64 without mining. */
@RunWith(AndroidJUnit4.class)
public class NativeRandomXInstrumentedTest {
 @Test public void nativeRandomXDeterminismAndInputGate() {
  assertTrue("Native RandomX shared library must load",NativeRandomX.available());
  byte[] key="ForgeCoin Android QA only".getBytes(StandardCharsets.UTF_8);
  byte[] input="disposable-test-vector".getBytes(StandardCharsets.UTF_8);
  byte[] first=NativeRandomX.hash(key,input), second=NativeRandomX.hash(key,input);
  assertEquals(32,first.length);
  assertArrayEquals(first,second);
  assertFalse(Arrays.equals(first,new byte[32]));
  try { NativeRandomX.hash(new byte[0],input);fail("Expected invalid key rejection"); }
  catch(IllegalArgumentException expected) {}
 }
}
