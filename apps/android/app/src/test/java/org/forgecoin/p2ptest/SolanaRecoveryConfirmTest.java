package org.forgecoin.p2ptest;
import org.junit.Test;
import static org.junit.Assert.*;
public class SolanaRecoveryConfirmTest {
 private static final String PHRASE="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
 @Test public void correctWordsAccepted(){assertTrue(SolanaRecoveryConfirmDialog.matches(PHRASE,"abandon","abandon"));}
 @Test public void wrongWordsRejected(){assertFalse(SolanaRecoveryConfirmDialog.matches(PHRASE,"about","abandon"));}
 @Test public void partialWordsRejected(){assertFalse(SolanaRecoveryConfirmDialog.matches(PHRASE,"","abandon"));}
 @Test public void invalidPhraseLengthRejected(){assertFalse(SolanaRecoveryConfirmDialog.matches("abandon about","abandon","about"));}
}
