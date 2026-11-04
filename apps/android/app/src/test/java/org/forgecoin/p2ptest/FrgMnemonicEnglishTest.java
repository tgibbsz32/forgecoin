package org.forgecoin.p2ptest;

import java.io.ByteArrayInputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Locale;
import java.util.zip.CRC32;
import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Public deterministic fixture only: native CryptoNote 32-byte input
 * 00,01,...,1f encoded into 25 English words. NOT a secure wallet seed.
 */
public final class FrgMnemonicEnglishTest {
    private static final String PUBLIC_NATIVE_FORMAT_FIXTURE =
        "amaze buffet cake entrance symptoms tiger lamb maze nestle " +
        "python dusted faxed update vague zinger boxes ornament renting " +
        "glass gained island nabbing afield calamity boxes";

    private static FrgMnemonicEnglish load() throws Exception {
        try (FileInputStream file = new FileInputStream(
                "src/main/assets/frg_english_mnemonic.txt")) {
            return FrgMnemonicEnglish.load(file);
        }
    }

    @Test public void fullDictionaryMatchesSelectedNativeLanguageShape()
            throws Exception {
        assertEquals(1626, load().dictionarySizeForTests());
    }

    @Test public void nativePublicTwentyFiveWordFormatIsAccepted()
            throws Exception {
        FrgMnemonicEnglish validator = load();
        assertTrue(validator.isValid25WordPhrase(PUBLIC_NATIVE_FORMAT_FIXTURE));
        assertTrue(validator.isValid25WordPhrase(
            PUBLIC_NATIVE_FORMAT_FIXTURE.toUpperCase(Locale.ROOT)));
        assertTrue(validator.isValid25WordPhrase(
            "  " + PUBLIC_NATIVE_FORMAT_FIXTURE.replace(" ", " \t  ") + "  "));
    }

    @Test public void damagedChecksumAndWordCountRejected() throws Exception {
        FrgMnemonicEnglish validator = load();
        String[] words = PUBLIC_NATIVE_FORMAT_FIXTURE.split(" ");
        words[24] = "zombie";
        assertFalse(validator.isValid25WordPhrase(String.join(" ", words)));
        assertFalse(validator.isValid25WordPhrase(
            PUBLIC_NATIVE_FORMAT_FIXTURE.substring(0,
                PUBLIC_NATIVE_FORMAT_FIXTURE.lastIndexOf(' '))));
        assertFalse(validator.isValid25WordPhrase(
            PUBLIC_NATIVE_FORMAT_FIXTURE + " extra"));
        assertFalse(validator.isValid25WordPhrase(null));
        assertFalse(validator.isValid25WordPhrase(""));
        assertFalse(validator.isValid25WordPhrase(
            PUBLIC_NATIVE_FORMAT_FIXTURE.replace("buffet", "buffe7")));
        assertFalse(validator.isValid25WordPhrase(
            PUBLIC_NATIVE_FORMAT_FIXTURE.replace("buffet", "buff")));
    }

    @Test public void tripleOverflowRejectedEvenWithMatchingChecksum()
            throws Exception {
        String[] parts = PUBLIC_NATIVE_FORMAT_FIXTURE.split(" ");
        parts[0] = "abbey";
        parts[1] = "abbey";
        parts[2] = "zoom"; // triggers > UINT32_MAX for 1626^2*1625
        CRC32 crc = new CRC32();
        StringBuilder concatenated = new StringBuilder();
        for (int i = 0; i < 24; i++)
            concatenated.append(parts[i].substring(0, 3));
        byte[] text = concatenated.toString().getBytes(StandardCharsets.US_ASCII);
        crc.update(text);
        parts[24] = parts[(int)(crc.getValue() % 24)];
        assertFalse(load().isValid25WordPhrase(String.join(" ", parts)));
    }

    @Test public void corruptDictionaryCannotBeAccepted() {
        try {
            FrgMnemonicEnglish.load(new ByteArrayInputStream(
                "abbey\nabbey\nzoom\n".getBytes(StandardCharsets.UTF_8)));
            fail("Duplicate/incomplete dictionary accepted");
        } catch (IOException expected) {
            assertFalse(expected.getMessage().contains("amaze"));
        }
        try {
            FrgMnemonicEnglish.load(new ByteArrayInputStream(
                "abbey\nzoom\n".getBytes(StandardCharsets.UTF_8)));
            fail("Incomplete dictionary accepted");
        } catch (IOException expected) {
            assertFalse(expected.getMessage().contains("amaze"));
        }
    }
}
