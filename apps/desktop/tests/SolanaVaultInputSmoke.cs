using System;
using System.IO;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using ForgeCoinDesktop;
// Standalone smoke test: compile alongside SolanaVault.cs, without wallet secrets.
internal static class SolanaVaultInputSmoke
{
    private static int checks;
    private static void ExpectReject(string json)
    {
        bool rejected = false;
        try { SolanaVault.AddressFromKeypair(json); }
        catch (InvalidDataException) { rejected = true; }
        if (!rejected) throw new Exception("Malformed keypair unexpectedly accepted.");
        checks++;
    }
    private static string Build(object replacement)
    {
        object[] bytes = new object[64];
        for (int i = 0; i < bytes.Length; i++) bytes[i] = 0;
        bytes[0] = replacement;
        return new JavaScriptSerializer().Serialize(bytes);
    }
    public static int Main()
    {
        try
        {
            ExpectReject(Build("7"));
            ExpectReject(Build(true));
            ExpectReject(Build(3.5));
            ExpectReject(Build(-1));
            ExpectReject(Build(256));
            ExpectReject("[]");
            Console.WriteLine("Solana vault canonical JSON byte inputs: " + checks + " negative tests passed.");
            Console.WriteLine("NOTE: This does not verify Ed25519 keypair derivation or wallet custody.");
            return 0;
        }
        catch (Exception e) { Console.Error.WriteLine(e); return 1; }
    }
}
