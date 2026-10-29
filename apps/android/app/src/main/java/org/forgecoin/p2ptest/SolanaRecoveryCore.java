package org.forgecoin.p2ptest;
import java.security.GeneralSecurityException;
/** Validated mnemonic recovery to a 32-byte hardened Solana seed; no UI or storage. */
public final class SolanaRecoveryCore {
 private SolanaRecoveryCore(){}
 public static byte[] recover(String phrase,String[] englishWords,int account) throws GeneralSecurityException {
  if(!SolanaMnemonicCheck.valid(phrase,englishWords))
    throw new IllegalArgumentException("Invalid BIP39 recovery phrase");
  // Empty BIP39 passphrase is explicit. Non-empty passphrases need separate UI.
  return SolanaSlip10.derive(phrase,"",account);
 }
}
