using System;
using ForgeCoinDesktop;

internal static class FrgWalletInputTests
{
    private static int count;
    private static void Check(bool condition, string reason)
    {
        count++;
        if (!condition) throw new Exception("FAIL: " + reason);
    }
    private static void RejectAmount(string s)
    {
        bool rejected = false;
        try { FrgWalletInput.ParseAmountAtoms(s); }
        catch (ArgumentException) { rejected = true; }
        Check(rejected, "amount must reject invalid string");
    }
    private static void RejectMnemonic(string s)
    {
        bool rejected = false;
        try { FrgWalletInput.NormalizeEnglishMnemonic(s); }
        catch (ArgumentException e)
        {
            rejected = true;
            Check(!e.Message.Contains("PRIVATEWORD"), "mnemonic must never enter error");
        }
        Check(rejected, "mnemonic must reject invalid word count/format");
    }
    private static void RejectWalletName(string s)
    {
        bool rejected = false;
        try { FrgWalletInput.WalletName(s); }
        catch (ArgumentException) { rejected = true; }
        Check(rejected, "wallet filename rejection");
    }

    public static int Main()
    {
        Check(FrgWalletInput.ParseAmountAtoms("0.00000001") == 1, "single atom");
        Check(FrgWalletInput.ParseAmountAtoms("1") == 100000000, "one FRG");
        Check(FrgWalletInput.ParseAmountAtoms("1.23456789") == 123456789, "exact 8 decimals");
        Check(FrgWalletInput.ParseAmountAtoms("0001.00000001") == 100000001, "leading zero allowed");
        Check(FrgWalletInput.ParseAmountAtoms("92233720368.54775807") == Int64.MaxValue, "maximum signed atoms");
        foreach (string value in new string[] {
            "", "0", "-1", "+1", ".1", "1.", "1e0", "1,000",
            "0.000000001", "1.000000009", "92233720368.54775808",
            "NaN", "Infinity", "1 2", " 1.0 ", "0xFF"
        }) RejectAmount(value);
        Check(FrgWalletInput.IsTransactionId(new string('a',64)), "valid hash");
        Check(!FrgWalletInput.IsTransactionId(new string('z',64)), "nonhex hash");
        Check(!FrgWalletInput.IsTransactionId(new string('a',63)), "short hash");
        Check(FrgWalletInput.LooksLikePublicAddress(new string('4',95)), "plausible public Base58");
        Check(!FrgWalletInput.LooksLikePublicAddress(new string('4',94) + "0"), "invalid base58 0");
        Check(!FrgWalletInput.LooksLikePublicAddress("seed words"), "seed is not public address");

        string[] words = new string[25];
        for (int i = 0; i < words.Length; i++) words[i] = "PRIVATEWORD";
        string joined = String.Join("\t", words);
        string normalized = FrgWalletInput.NormalizeEnglishMnemonic(joined);
        Check(normalized.Split(' ').Length == 25, "25 normalized seed words");
        Check(normalized.StartsWith("privateword privateword"), "lower-case normalized");
        RejectMnemonic("PRIVATEWORD");
        RejectMnemonic(String.Join(" ", new string[0]));
        words[8] = "PRIVATEWORD9";
        RejectMnemonic(String.Join(" ", words));

        Check(FrgWalletInput.WalletName("qa-wallet01") == "qa-wallet01", "safe name");
        foreach (string name in new string[] {
            "", "..", ".hidden", "CON", "CON.txt", "NUL", "LPT1.keys",
            "../wallet", "..\\wallet", "wallet:bad", "wallet.", "WALLET?",
            new string('x',81)
        }) RejectWalletName(name);

        Console.WriteLine("PASS: " + count + " desktop FRG wallet input assertions (no network, files or secrets)");
        return 0;
    }
}
