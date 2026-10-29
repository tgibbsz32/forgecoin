using System;
using ForgeCoinDesktop;
internal static class SolanaBip39SeedSmoke
{
    private static string Hex(byte[] data) { return BitConverter.ToString(data).Replace("-", "").ToLowerInvariant(); }
    public static int Main()
    {
        const string phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
        const string expected = "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04";
        byte[] seed = SolanaBip39Seed.Derive(phrase, "TREZOR");
        if (Hex(seed) != expected) throw new Exception("BIP39 standard vector mismatch.");
        byte[] other = SolanaBip39Seed.Derive(phrase, "");
        if (Hex(other) == expected) throw new Exception("Passphrase unexpectedly ignored.");
        Array.Clear(seed, 0, seed.Length);
        Array.Clear(other, 0, other.Length);
        Console.WriteLine("BIP39_PBKDF2_SHA512_VECTOR_OK");
        return 0;
    }
}
