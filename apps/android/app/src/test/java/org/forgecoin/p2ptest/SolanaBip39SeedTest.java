package org.forgecoin.p2ptest;

import org.junit.Test;
import static org.junit.Assert.*;
import java.util.Arrays;
public class SolanaBip39SeedTest {
    private static String hex(byte[] bytes) {
        StringBuilder b = new StringBuilder();
        for(byte x:bytes)b.append(String.format("%02x",x & 255));
        return b.toString();
    }
    @Test public void officialBip39Vector() throws Exception {
        byte[] seed=SolanaBip39Seed.derive("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about","TREZOR");
        assertEquals("c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04",hex(seed));
        Arrays.fill(seed,(byte)0);
    }
    @Test public void passphraseChangesSeed() throws Exception {
        String phrase="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
        byte[] a=SolanaBip39Seed.derive(phrase,"");
        byte[] b=SolanaBip39Seed.derive(phrase,"TREZOR");
        assertFalse(Arrays.equals(a,b));
        Arrays.fill(a,(byte)0);Arrays.fill(b,(byte)0);
    }
    @Test(expected=IllegalArgumentException.class) public void rejectsEmpty() throws Exception {
        SolanaBip39Seed.derive("  ","");
    }
}
