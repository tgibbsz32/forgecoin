# Android Solana recovery confirmation component — 2026-10-29

## Completed
Added `SolanaRecoveryConfirmDialog`, an Android dialog component that displays a 12-word mnemonic with a backup warning, requests confirmation of words 4 and 9, and calls the supplied callback only on a match. It enables FLAG_SECURE while showing sensitive words. Added 4 JUnit tests for matching, mismatching, blank and wrong-length phrases.

## Verified
TREYS_DELL_RTX Android Studio JBR + SDK; `:app:testDebugUnitTest :app:assembleDebug :app:connectedDebugAndroidTest` completed BUILD SUCCESSFUL. Existing three connected API 36 emulator tests completed. The new confirmation logic has unit tests but the dialog interaction itself has not been exercised through Android UI automation.

## Security and release caveats
The component is **not wired to MainActivity** and cannot create a production wallet. FLAG_SECURE is left enabled until activity exit; this is conservative but needs lifecycle design. Mnemonic values are Java strings and remain subject to managed-memory exposure; dialog confirmation alone does not ensure users actually retain a correct backup. A complete flow must test display->backup confirmation->encrypted storage, cancellation, process death, screen capture restrictions and restoration on a second device. As implemented in PR #174, the lifecycle creates an encrypted record before confirmation, so integrating this UI without restructuring would create unconfirmed wallets. Do not enable Create/Restore controls until that is fixed, and add device lock/biometric protection, physical Android phone tests, audit and native FRG 25-word wallet work. No mint, sale, Oracle activation or actual owner wallet.
