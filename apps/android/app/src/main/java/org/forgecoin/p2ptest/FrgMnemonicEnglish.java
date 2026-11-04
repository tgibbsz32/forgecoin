package org.forgecoin.p2ptest;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.zip.CRC32;

/**
 * Native ForgeCoin Monero-derived English 25-word mnemonic preflight.
 *
 * Verifies the EXACT, ordered 1626-word dictionary, unique three-letter
 * prefixes, native CRC32 checksum and canonical eight 32-bit word triples.
 * It intentionally NEVER reconstructs/stores a secret spend key, creates a
 * wallet, sends a seed to a server or exposes any seed in errors/logs.
 *
 * Format acceptance is NOT proof of a valid wallet, safe key material or
 * ownership. Actual native wallet restore must independently authenticate
 * and validate the phrase after an approved encrypted custody flow exists.
 */
public final class FrgMnemonicEnglish {
    private static final int DICTIONARY_WORDS = 1626;
    private static final int PHRASE_WORDS = 25;
    private static final int BASE_WORDS = 24;
    private static final int PREFIX_LENGTH = 3;
    private static final long MAX_UINT32 = 0xffff_ffffL;

    private final List<String> words;
    private final Map<String, Integer> positions;

    private FrgMnemonicEnglish(List<String> input) {
        this.words = Collections.unmodifiableList(new ArrayList<>(input));
        Map<String, Integer> map = new HashMap<>();
        for (int i = 0; i < words.size(); i++)
            map.put(words.get(i), i);
        this.positions = Collections.unmodifiableMap(map);
    }

    public static FrgMnemonicEnglish load(InputStream dictionaryStream)
            throws IOException {
        if (dictionaryStream == null) throw new IOException("Native dictionary missing.");
        List<String> dictionary = new ArrayList<>(DICTIONARY_WORDS);
        Set<String> prefixes = new HashSet<>();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(dictionaryStream, StandardCharsets.UTF_8))) {
            String line, previous = null;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) continue;
                if (line.length() < PREFIX_LENGTH ||
                    line.length() > 32 || !line.matches("[a-z]+") ||
                    (previous != null && previous.compareTo(line) >= 0) ||
                    !prefixes.add(line.substring(0, PREFIX_LENGTH)) ||
                    dictionary.size() >= DICTIONARY_WORDS)
                    throw new IOException("Native FRG mnemonic dictionary is invalid.");
                dictionary.add(line);
                previous = line;
            }
        }
        if (dictionary.size() != DICTIONARY_WORDS ||
            !"abbey".equals(dictionary.get(0)) ||
            !"zoom".equals(dictionary.get(DICTIONARY_WORDS - 1)))
            throw new IOException("Native FRG mnemonic dictionary is incomplete.");
        return new FrgMnemonicEnglish(dictionary);
    }

    /**
     * Accept only full, canonical English words. The upstream native wallet
     * also supports 3-letter shorthand, but the app requires full words to
     * minimize transcription ambiguity until secure native restore exists.
     */
    public boolean isValid25WordPhrase(String phrase) {
        if (phrase == null || phrase.length() < 25 * 3 ||
            phrase.length() > 1024)
            return false;
        String[] parts = phrase.trim().toLowerCase(Locale.ROOT).split("\\s+");
        if (parts.length != PHRASE_WORDS) return false;

        int[] indices = new int[BASE_WORDS];
        for (int i = 0; i < parts.length; ++i) {
            Integer index = positions.get(parts[i]);
            if (index == null) return false;
            if (i < BASE_WORDS) indices[i] = index;
        }

        // Native electrum-words.cpp maps 3 dictionary positions to each
        // canonical 32-bit little-endian word. Reject overflow/redundancy.
        final long n = words.size();
        for (int i = 0; i < BASE_WORDS; i += 3) {
            long w1 = indices[i], w2 = indices[i + 1], w3 = indices[i + 2];
            long value = w1
                    + n * ((n - w1 + w2) % n)
                    + n * n * ((n - w2 + w3) % n);
            if (value > MAX_UINT32 || value % n != w1)
                return false;
        }

        // Native Monero/FRG English checksum:
        // CRC32 of 3-letter prefixes for 24 words, choose one of the
        // original 24 words at CRC32 % 24 as the twenty-fifth checksum word.
        byte[] prefixes = new byte[BASE_WORDS * PREFIX_LENGTH];
        for (int i = 0; i < BASE_WORDS; ++i) {
            String word = words.get(indices[i]);
            for (int j = 0; j < PREFIX_LENGTH; ++j)
                prefixes[i * PREFIX_LENGTH + j] = (byte)word.charAt(j);
        }
        CRC32 crc = new CRC32();
        crc.update(prefixes, 0, prefixes.length);
        int checksumIndex = (int)(crc.getValue() % BASE_WORDS);
        java.util.Arrays.fill(prefixes, (byte)0);
        return parts[BASE_WORDS].equals(parts[checksumIndex]);
    }

    int dictionarySizeForTests() {
        return words.size();
    }
}
