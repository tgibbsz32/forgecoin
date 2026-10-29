package org.forgecoin.p2ptest;
import org.junit.Test;
import static org.junit.Assert.*;
public class NativeRandomXInputTest {
 @Test public void invalidInputsRejectedWithoutNativeRuntime() {
  for(byte[] key:new byte[][]{null,new byte[0],new byte[129]})
   assertThrows(IllegalArgumentException.class,() -> NativeRandomX.hash(key,new byte[1]));
  for(byte[] input:new byte[][]{null,new byte[0],new byte[257]})
   assertThrows(IllegalArgumentException.class,() -> NativeRandomX.hash(new byte[1],input));
 }
 @Test public void noSoftwareFallbackWhenNativeLibraryMissing() {
  if(!NativeRandomX.available())
   assertThrows(IllegalStateException.class,() -> NativeRandomX.hash(new byte[1],new byte[1]));
 }
}
