using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

namespace ForgeCoinDesktop
{
    // Encrypted export format v1: PBKDF2-SHA256, AES-256-CBC and encrypt-then-HMAC-SHA256.
    // No plaintext keypairs, mnemonics or passwords are written to the application vault.
    // Do not change this format without migrations and independent cryptographic review.
    internal static class SolanaVault
    {
        [DllImport("libsodium-26.dll", CallingConvention = CallingConvention.Cdecl)]
        private static extern int sodium_init();
        [DllImport("libsodium-26.dll", CallingConvention = CallingConvention.Cdecl)]
        private static extern int crypto_sign_seed_keypair(byte[] publicKey, byte[] secretKey, byte[] seed);
        private const string Format = "forgecoin-solana-aes256-hmac-v1";
        private const int Iterations = 300000;
        private const string Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
        private static readonly JavaScriptSerializer Json = new JavaScriptSerializer();

        internal sealed class WalletSecret
        {
            public string Address;
            public string KeypairJson;
            public string Mnemonic;
        }

        // Development-only in-memory keypair primitive. NOT a mnemonic wallet.
        // The caller must preserve an encrypted backup and must not use this
        // primitive for production custody until audited recovery exists.
        internal static string GenerateEncryptedKeypairInMemory(string password)
        {
            if (password == null || password.Length < 12)
                throw new ArgumentException("Use an encryption password of at least 12 characters.");
            byte[] seed = RandomBytes(32);
            byte[] pub = new byte[32];
            byte[] secret = new byte[64];
            try
            {
                if (sodium_init() < 0 || crypto_sign_seed_keypair(pub, secret, seed) != 0)
                    throw new CryptographicException("Ed25519 generation unavailable.");
                int[] values = new int[64];
                for (int i = 0; i < 64; i++) values[i] = secret[i];
                try
                {
                    // Empty mnemonic is intentional: no invented recovery words.
                    return Encrypt(Json.Serialize(values), "", password);
                }
                finally { Array.Clear(values, 0, values.Length); }
            }
            catch (DllNotFoundException)
            {
                throw new CryptographicException("Required Ed25519 library unavailable.");
            }
            catch (EntryPointNotFoundException)
            {
                throw new CryptographicException("Incompatible Ed25519 library.");
            }
            finally
            {
                Array.Clear(seed, 0, seed.Length);
                Array.Clear(pub, 0, pub.Length);
                Array.Clear(secret, 0, secret.Length);
            }
        }

        internal static string Encode58(byte[] bytes)
        {
            if (bytes == null || bytes.Length == 0) throw new ArgumentException("Empty public key");
            int leading = 0;
            while (leading < bytes.Length && bytes[leading] == 0) leading++;
            List<int> digits = new List<int>();
            for (int i = leading; i < bytes.Length; i++)
            {
                int carry = bytes[i];
                for (int j = 0; j < digits.Count; j++)
                {
                    int n = digits[j] * 256 + carry;
                    digits[j] = n % 58;
                    carry = n / 58;
                }
                while (carry > 0)
                {
                    digits.Add(carry % 58);
                    carry /= 58;
                }
            }
            StringBuilder value = new StringBuilder(new string('1', leading));
            for (int i = digits.Count - 1; i >= 0; i--) value.Append(Alphabet[digits[i]]);
            return value.ToString();
        }

        internal static string AddressFromKeypair(string keypairJson)
        {
            object parsed = Json.DeserializeObject(keypairJson);
            IList items = parsed as IList;
            if (items == null || items.Count != 64)
                throw new InvalidDataException("Solana keypair must contain exactly 64 byte values.");
            byte[] pub = new byte[32];
            byte[] seed = new byte[32];
            for (int i = 0; i < 64; i++)
            {
                // Reject booleans, floating-point values, strings and coercible JSON
                // data: a keypair is a canonical JSON array of integral bytes.
                if (!(items[i] is int) && !(items[i] is long))
                    throw new InvalidDataException("Keypair must contain integer JSON bytes.");
                long number = Convert.ToInt64(items[i]);
                if (number < 0 || number > 255)
                    throw new InvalidDataException("Invalid keypair byte.");
                if (i >= 32) pub[i - 32] = (byte)number;
                else seed[i] = (byte)number;
            }
            byte[] derivedPublic = new byte[32];
            byte[] derivedSecret = new byte[64];
            try
            {
                if (sodium_init() < 0 || crypto_sign_seed_keypair(derivedPublic, derivedSecret, seed) != 0)
                    throw new CryptographicException("Ed25519 key verification unavailable.");
                if (!FixedEquals(pub, derivedPublic))
                    throw new InvalidDataException("Solana public key does not match private seed.");
                return Encode58(pub);
            }
            catch (DllNotFoundException)
            {
                throw new CryptographicException("Required reviewed Ed25519 library is missing; wallet import is disabled.");
            }
            catch (EntryPointNotFoundException)
            {
                throw new CryptographicException("Incompatible Ed25519 library; wallet import is disabled.");
            }
            finally
            {
                Array.Clear(seed, 0, seed.Length);
                Array.Clear(derivedSecret, 0, derivedSecret.Length);
                Array.Clear(derivedPublic, 0, derivedPublic.Length);
            }
        }

        private static byte[] RandomBytes(int count)
        {
            byte[] result = new byte[count];
            using (RandomNumberGenerator rng = RandomNumberGenerator.Create()) rng.GetBytes(result);
            return result;
        }
        private static byte[] Combine(params byte[][] pieces)
        {
            int length = 0;
            foreach (byte[] p in pieces) length = checked(length + p.Length);
            byte[] result = new byte[length];
            int cursor = 0;
            foreach (byte[] p in pieces)
            {
                Buffer.BlockCopy(p, 0, result, cursor, p.Length);
                cursor += p.Length;
            }
            return result;
        }
        private static byte[] MacPayload(string address, byte[] salt, byte[] iv, byte[] ciphertext)
        {
            return Combine(Encoding.UTF8.GetBytes(Format + "|" + address + "|"), salt, iv, ciphertext);
        }
        private static bool FixedEquals(byte[] expected, byte[] actual)
        {
            if (expected == null || actual == null || expected.Length != actual.Length) return false;
            int difference = 0;
            for (int i = 0; i < expected.Length; i++) difference |= expected[i] ^ actual[i];
            return difference == 0;
        }
        private static IDictionary DecodeHeader(string encoded)
        {
            if (encoded == null || encoded.Length > 100000)
                throw new InvalidDataException("Invalid or oversized encrypted Solana backup.");
            IDictionary vault = Json.DeserializeObject(encoded) as IDictionary;
            if (vault == null || !vault.Contains("format") || Convert.ToString(vault["format"]) != Format ||
                !vault.Contains("iterations") || Convert.ToInt32(vault["iterations"]) != Iterations)
                throw new InvalidDataException("Unsupported encrypted Solana backup format.");
            return vault;
        }
        internal static string PublicAddress(string encodedVault)
        {
            IDictionary vault = DecodeHeader(encodedVault);
            return Convert.ToString(vault["address"]);
        }
        internal static string Encrypt(string keypairJson, string mnemonic, string password)
        {
            if (password == null || password.Length < 12)
                throw new ArgumentException("Use an encryption password of at least 12 characters.");
            string address = AddressFromKeypair(keypairJson);
            if (mnemonic == null) mnemonic = "";
            string payload = Json.Serialize(new Dictionary<string, object> {
                { "keypair", keypairJson }, { "mnemonic", mnemonic }
            });
            byte[] salt = RandomBytes(32);
            byte[] iv = RandomBytes(16);
            byte[] keys = null;
            byte[] ciphertext;
            byte[] tag;
            try
            {
                using (Rfc2898DeriveBytes kdf = new Rfc2898DeriveBytes(
                    password, salt, Iterations, HashAlgorithmName.SHA256))
                    keys = kdf.GetBytes(64);
                using (Aes aes = Aes.Create())
                {
                    aes.KeySize = 256; aes.BlockSize = 128;
                    aes.Mode = CipherMode.CBC; aes.Padding = PaddingMode.PKCS7;
                    byte[] encKey = new byte[32]; Buffer.BlockCopy(keys, 0, encKey, 0, 32);
                    aes.Key = encKey;
                    aes.IV = iv;
                    Array.Clear(encKey, 0, encKey.Length);
                    using (ICryptoTransform cipher = aes.CreateEncryptor())
                        ciphertext = cipher.TransformFinalBlock(Encoding.UTF8.GetBytes(payload), 0,
                            Encoding.UTF8.GetByteCount(payload));
                }
                byte[] macKey = new byte[32]; Buffer.BlockCopy(keys, 32, macKey, 0, 32);
                using (HMACSHA256 mac = new HMACSHA256(macKey))
                    tag = mac.ComputeHash(MacPayload(address, salt, iv, ciphertext));
                Array.Clear(macKey, 0, macKey.Length);
            }
            finally { if (keys != null) Array.Clear(keys, 0, keys.Length); }
            return Json.Serialize(new Dictionary<string, object> {
                { "format", Format }, { "iterations", Iterations }, { "address", address },
                { "salt", Convert.ToBase64String(salt) }, { "iv", Convert.ToBase64String(iv) },
                { "ciphertext", Convert.ToBase64String(ciphertext) }, { "mac", Convert.ToBase64String(tag) }
            });
        }
        internal static WalletSecret Decrypt(string encodedVault, string password)
        {
            IDictionary header = DecodeHeader(encodedVault);
            string address = Convert.ToString(header["address"]);
            byte[] salt = Convert.FromBase64String(Convert.ToString(header["salt"]));
            byte[] iv = Convert.FromBase64String(Convert.ToString(header["iv"]));
            byte[] ciphertext = Convert.FromBase64String(Convert.ToString(header["ciphertext"]));
            byte[] tag = Convert.FromBase64String(Convert.ToString(header["mac"]));
            if (salt.Length != 32 || iv.Length != 16 || ciphertext.Length == 0 ||
                ciphertext.Length > 65536 || tag.Length != 32)
                throw new InvalidDataException("Malformed encrypted Solana backup.");
            byte[] keys = null;
            try
            {
                using (Rfc2898DeriveBytes kdf = new Rfc2898DeriveBytes(
                    password, salt, Iterations, HashAlgorithmName.SHA256))
                    keys = kdf.GetBytes(64);
                byte[] macKey = new byte[32]; Buffer.BlockCopy(keys, 32, macKey, 0, 32);
                byte[] expected;
                using (HMACSHA256 mac = new HMACSHA256(macKey))
                    expected = mac.ComputeHash(MacPayload(address, salt, iv, ciphertext));
                Array.Clear(macKey, 0, macKey.Length);
                if (!FixedEquals(expected, tag))
                    throw new CryptographicException("Incorrect password or modified backup.");
                string plaintext;
                using (Aes aes = Aes.Create())
                {
                    aes.KeySize = 256; aes.BlockSize = 128;
                    aes.Mode = CipherMode.CBC; aes.Padding = PaddingMode.PKCS7;
                    byte[] encKey = new byte[32]; Buffer.BlockCopy(keys, 0, encKey, 0, 32);
                    aes.Key = encKey; aes.IV = iv;
                    using (ICryptoTransform decrypt = aes.CreateDecryptor())
                        plaintext = Encoding.UTF8.GetString(decrypt.TransformFinalBlock(
                            ciphertext, 0, ciphertext.Length));
                    Array.Clear(encKey, 0, encKey.Length);
                }
                IDictionary content = Json.DeserializeObject(plaintext) as IDictionary;
                if (content == null || !content.Contains("keypair"))
                    throw new InvalidDataException("Corrupt decrypted wallet.");
                string keypair = Convert.ToString(content["keypair"]);
                if (AddressFromKeypair(keypair) != address)
                    throw new CryptographicException("Backup public address does not match secret.");
                return new WalletSecret { Address = address, KeypairJson = keypair,
                    Mnemonic = content.Contains("mnemonic") ? Convert.ToString(content["mnemonic"]) : "" };
            }
            finally { if (keys != null) Array.Clear(keys, 0, keys.Length); }
        }
        internal static void SaveNew(string path, string encryptedVault)
        {
            using (FileStream output = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (StreamWriter writer = new StreamWriter(output, new UTF8Encoding(false)))
                writer.Write(encryptedVault);
        }
    }
}
