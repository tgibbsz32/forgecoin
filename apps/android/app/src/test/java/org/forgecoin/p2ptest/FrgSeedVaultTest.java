package org.forgecoin.p2ptest;

import org.junit.Test;
import static org.junit.Assert.*;

public class FrgSeedVaultTest {
    @Test public void acceptsTwentyFiveWordsForStructuralCheck() {
        String phrase = String.join(" ", java.util.Collections.nCopies(25, "example"));
        FrgSeedVault.validateRecoveryPhrase(phrase.toCharArray());
    }
    @Test public void rejectsTwentyFourWords() {
        String phrase = String.join(" ", java.util.Collections.nCopies(24, "example"));
        assertRejected(phrase);
    }
    @Test public void rejectsInvalidCharacters() {
        String phrase = String.join(" ", java.util.Collections.nCopies(24, "example")) + " 1234";
        assertRejected(phrase);
    }
    @Test public void rejectsEmptyPhrase() { assertRejected(" "); }
    private void assertRejected(String phrase) {
        try {
            FrgSeedVault.validateRecoveryPhrase(phrase.toCharArray());
            fail("Expected rejection");
        } catch (IllegalArgumentException expected) { }
    }
}
