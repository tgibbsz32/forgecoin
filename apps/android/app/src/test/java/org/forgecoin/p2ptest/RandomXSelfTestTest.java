package org.forgecoin.p2ptest;

import org.junit.Test;
import static org.junit.Assert.*;

public final class RandomXSelfTestTest {
    @Test public void acceptedKnownVectorIsExactly32Bytes() {
        byte[] exact = RandomXSelfTest.knownAnswerForUnitTest();
        assertEquals(32, exact.length);
        assertTrue(RandomXSelfTest.isKnownAnswer(exact));
    }

    @Test public void randomOrMalformedHashIsRejected() {
        assertFalse(RandomXSelfTest.isKnownAnswer(null));
        assertFalse(RandomXSelfTest.isKnownAnswer(new byte[0]));
        assertFalse(RandomXSelfTest.isKnownAnswer(new byte[31]));
        assertFalse(RandomXSelfTest.isKnownAnswer(new byte[33]));
        assertFalse(RandomXSelfTest.isKnownAnswer(new byte[32]));
    }

    @Test public void oneByteMismatchFailsConstantTimeComparison() {
        byte[] expected = RandomXSelfTest.knownAnswerForUnitTest();
        for (int i = 0; i < expected.length; i++) {
            byte[] changed = expected.clone();
            changed[i] ^= 1;
            assertFalse("corrupted byte " + i,
                        RandomXSelfTest.isKnownAnswer(changed));
        }
    }

    @Test public void returnedReferenceCannotBeModifiedByCaller() {
        byte[] first = RandomXSelfTest.knownAnswerForUnitTest();
        first[0] ^= 1;
        assertTrue(RandomXSelfTest.isKnownAnswer(
            RandomXSelfTest.knownAnswerForUnitTest()));
    }
}
