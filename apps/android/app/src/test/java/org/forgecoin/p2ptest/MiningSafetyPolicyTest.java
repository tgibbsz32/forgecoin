package org.forgecoin.p2ptest;

import org.junit.Test;
import static org.junit.Assert.*;

/** Pure tests: no Android device, network, wallets or actual CPU mining. */
public class MiningSafetyPolicyTest {
    private static MiningSafetyPolicy.Recommendation eval(
            int cpu, int pct, int battery, boolean charging,
            boolean powerSaver, int thermal, boolean fgs,
            boolean screen, boolean optIn, boolean nativeReady) {
        return MiningSafetyPolicy.evaluate(cpu, pct, battery, charging,
            powerSaver, thermal, fgs, screen, optIn, nativeReady);
    }

    @Test public void previewNativeMinerAlwaysBlocked() {
        MiningSafetyPolicy.Recommendation r = eval(8, 100, 100, true,
            false, 0, true, true, true, false);
        assertFalse(r.eligible);
        assertEquals(0, r.threads);
        assertTrue(r.reason.contains("not approved"));
    }

    @Test public void severeCriticalEmergencyShutdownAllStop() {
        for (int thermal = 3; thermal <= 6; thermal++) {
            MiningSafetyPolicy.Recommendation r = eval(8, 100, 99, true,
                false, thermal, true, true, false, true);
            assertFalse("thermal=" + thermal, r.eligible);
            assertEquals(0, r.threads);
        }
    }

    @Test public void unknownThermalStateFailsClosed() {
        for (int thermal : new int[] {-1, -2, 7, Integer.MAX_VALUE}) {
            assertFalse(eval(8, 60, 99, true, false, thermal,
                true, true, false, true).eligible);
        }
    }

    @Test public void powerSaverAndLowBatteryPreventMining() {
        assertFalse(eval(8, 50, 80, false, true, 0,
            true, true, false, true).eligible);
        assertFalse(eval(8, 50, 19, false, false, 0,
            true, true, false, true).eligible);
        assertTrue(eval(8, 50, 20, false, false, 0,
            true, true, false, true).eligible);
        assertTrue(eval(8, 50, 19, true, false, 0,
            true, true, false, true).eligible);
        assertFalse(eval(8, 50, -1, true, false, 0,
            true, true, false, true).eligible);
    }

    @Test public void screenOffNeedsUserOptInAndForegroundService() {
        assertFalse(eval(8, 65, 90, true, false, 0,
            true, false, false, true).eligible);
        assertFalse(eval(8, 65, 90, true, false, 0,
            false, false, true, true).eligible);
        assertTrue(eval(8, 65, 90, true, false, 0,
            true, false, true, true).eligible);
    }

    @Test public void highLoadPreservesOneCoreAndCapsUnderWarming() {
        assertEquals(7, eval(8, 100, 90, true, false, 0,
            true, true, false, true).threads);
        assertEquals(4, eval(8, 100, 90, true, false, 1,
            true, true, false, true).threads);
        assertEquals(2, eval(8, 100, 90, true, false, 2,
            true, true, false, true).threads);
        assertEquals(1, eval(8, 1, 90, true, false, 0,
            true, true, false, true).threads);
        assertFalse(eval(1, 100, 90, true, false, 0,
            true, true, false, true).eligible);
    }

    @Test public void invalidIntensityNeverStartsAndResultIsAdvisory() {
        for (int percent : new int[] {-1, 0, 101, Integer.MAX_VALUE}) {
            MiningSafetyPolicy.Recommendation r = eval(8, percent, 90,
                true, false, 0, true, true, false, true);
            assertFalse(r.eligible);
            assertEquals(0, r.threads);
        }
        assertTrue(eval(4, 25, 90, true, false, 0,
            true, true, false, true).reason.contains("preflight only"));
    }
}
