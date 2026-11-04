using System;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace ForgeCoinDesktop
{
    /// <summary>
    /// Offline, deterministic input validation. This does NOT validate the
    /// network-specific FRG address prefix/checksum, authorize a release,
    /// transfer funds or run a miner. Native wallet RPC must independently
    /// validate each destination before any transfer is signed.
    /// </summary>
    internal static class FrgWalletInput
    {
        private const decimal AtomsPerCoin = 100000000m;
        private static readonly Regex AmountPattern = new Regex(
            @"^[0-9]+(?:\.[0-9]{1,8})?$", RegexOptions.CultureInvariant);
        private static readonly Regex AddressPattern = new Regex(
            @"^[1-9A-HJ-NP-Za-km-z]{90,140}$", RegexOptions.CultureInvariant);
        private static readonly Regex TxIdPattern = new Regex(
            @"^[0-9a-fA-F]{64}$", RegexOptions.CultureInvariant);
        private static readonly Regex SeedWordPattern = new Regex(
            @"^[a-zA-Z]+$", RegexOptions.CultureInvariant);

        public static long ParseAmountAtoms(string text)
        {
            if (String.IsNullOrEmpty(text) || text.Length > 64 ||
                !AmountPattern.IsMatch(text))
                throw new ArgumentException(
                    "Enter a positive FRG amount with at most eight decimal places.");
            decimal amount;
            if (!Decimal.TryParse(text, NumberStyles.AllowDecimalPoint,
                                  CultureInfo.InvariantCulture, out amount))
                throw new ArgumentException("FRG amount cannot be represented.");
            decimal atoms = amount * AtomsPerCoin;
            if (atoms < 1m || atoms > (decimal)Int64.MaxValue ||
                atoms != Decimal.Truncate(atoms))
                throw new ArgumentException("Amount is outside the exact FRG atomic range.");
            return Decimal.ToInt64(atoms);
        }

        public static bool LooksLikePublicAddress(string address)
        {
            return !String.IsNullOrEmpty(address) && AddressPattern.IsMatch(address);
        }

        public static bool IsTransactionId(string hash)
        {
            return !String.IsNullOrEmpty(hash) && TxIdPattern.IsMatch(hash);
        }

        public static string WalletName(string name)
        {
            if (name == null) throw new ArgumentException("Enter a wallet filename.");
            string cleaned = name.Trim();
            if (cleaned.Length == 0 || cleaned.Length > 80 ||
                cleaned.EndsWith(".", StringComparison.Ordinal) ||
                cleaned.EndsWith(" ", StringComparison.Ordinal) ||
                cleaned == "." || cleaned == ".." ||
                cleaned.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 ||
                cleaned.IndexOfAny(new char[] { '/', '\\', ':', '*', '?', '"', '<', '>', '|' }) >= 0 ||
                cleaned.StartsWith(".", StringComparison.Ordinal))
                throw new ArgumentException("Use a simple wallet filename without folders or special characters.");
            // Windows device files are unsafe even with an extension.
            string stem = cleaned.Split('.')[0].ToUpperInvariant();
            if (stem == "CON" || stem == "PRN" || stem == "AUX" ||
                stem == "NUL" || Regex.IsMatch(stem, @"^(?:COM|LPT)[1-9]$"))
                throw new ArgumentException("Reserved Windows device names cannot be wallets.");
            return cleaned;
        }

        public static string NormalizeEnglishMnemonic(string text)
        {
            // Never put mnemonic text into an exception, log or diagnostics.
            if (String.IsNullOrWhiteSpace(text) || text.Length > 4096)
                throw new ArgumentException("Enter exactly 25 English recovery words.");
            string[] words = text.Trim().Split(
                new char[] { ' ', '\r', '\n', '\t' },
                StringSplitOptions.RemoveEmptyEntries);
            if (words.Length != 25)
                throw new ArgumentException("ForgeCoin native wallets require exactly 25 recovery words.");
            for (int i = 0; i < words.Length; i++)
            {
                if (words[i].Length < 2 || words[i].Length > 32 ||
                    !SeedWordPattern.IsMatch(words[i]))
                    throw new ArgumentException(
                        "Recovery phrase contains a word with an invalid format.");
                words[i] = words[i].ToLowerInvariant();
            }
            return String.Join(" ", words);
        }
    }
}
