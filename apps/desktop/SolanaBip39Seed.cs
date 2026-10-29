using System;
using System.Security.Cryptography;
using System.Text;

namespace ForgeCoinDesktop
{
    // BIP39 mnemonic -> seed only. No mnemonic validation, wallet path derivation,
    // or owner-wallet create/restore operation is authorized by this component.
    internal static class SolanaBip39Seed
    {
        internal static byte[] Derive(string mnemonic, string passphrase)
        {
            if (String.IsNullOrWhiteSpace(mnemonic))
                throw new ArgumentException("Mnemonic is required.");
            string normalizedPhrase = mnemonic.Normalize(NormalizationForm.FormKD);
            string normalizedSalt = ("mnemonic" + (passphrase ?? "")).Normalize(NormalizationForm.FormKD);
            byte[] password = Encoding.UTF8.GetBytes(normalizedPhrase);
            byte[] salt = Encoding.UTF8.GetBytes(normalizedSalt);
            try
            {
                using (var pbkdf = new Rfc2898DeriveBytes(password, salt, 2048, HashAlgorithmName.SHA512))
                    return pbkdf.GetBytes(64);
            }
            finally
            {
                Array.Clear(password, 0, password.Length);
                Array.Clear(salt, 0, salt.Length);
            }
        }
    }
}
