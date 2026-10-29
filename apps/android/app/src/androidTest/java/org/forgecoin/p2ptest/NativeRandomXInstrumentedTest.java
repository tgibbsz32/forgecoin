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
 @Test public void referenceRandomXKnownAnswerVector() {
  assertTrue(NativeRandomX.available());
  byte[] key="test key 000".getBytes(StandardCharsets.US_ASCII);
  byte[] input="This is a test".getBytes(StandardCharsets.US_ASCII);
  byte[] hash=NativeRandomX.hash(key,input);
  StringBuilder hex=new StringBuilder();
  for(byte b:hash) hex.append(String.format(java.util.Locale.ROOT,"%02x",b & 255));
  // Source: external/randomx/src/tests/tests.cpp (upstream RandomX test_a).
  assertEquals("639183aae1bf4c9a35884cb46b09cad9175f04efd7684e7262a0ac1c2f0b4e3f",hex.toString());
 }
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
