package org.forgecoin.p2ptest;
import static org.junit.Assert.*;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
/** Verify the ARM64 .so was actually loaded on an Android target. */
@RunWith(AndroidJUnit4.class)
public class NativeRuntimeProbeInstrumentedTest {
    @Test public void jniProbeLoadsAndRemainsFailClosed() {
        assertTrue("ARM64 native JNI probe library missing", NativeRuntimeProbe.isLoaded());
        String status=NativeRuntimeProbe.status();
        assertTrue(status, status.contains("JNI probe ABI: arm64-v8a"));
        assertTrue(status, status.contains("Native FRG wallet: NOT LINKED"));
        assertTrue(status, status.contains("Native RandomX miner: NOT LINKED"));
        assertTrue(status, status.contains("FRG chain acceptance: NOT VERIFIED"));
    }
}
