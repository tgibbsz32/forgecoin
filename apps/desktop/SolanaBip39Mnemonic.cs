using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace ForgeCoinDesktop
{
    // Offline BIP39 English mnemonic encoding/checksum. Not a complete Solana wallet.
    internal static class SolanaBip39Mnemonic
    {
        internal static string[] LoadWords(string path)
        {
            string[] words = File.ReadAllLines(path, Encoding.UTF8);
            if (words.Length != 2048) throw new InvalidDataException("BIP39 list must have 2048 words.");
            var unique = new HashSet<string>(StringComparer.Ordinal);
            foreach (string word in words)
                if (word != word.Trim() || word.Length == 0 || !unique.Add(word))
                    throw new InvalidDataException("Invalid BIP39 word list.");
            if (words[0] != "abandon" || words[2047] != "zoo")
                throw new InvalidDataException("Unexpected BIP39 word list.");
            return words;
        }
        internal static string FromEntropy(byte[] entropy, string[] words)
        {
            if (words == null || words.Length != 2048) throw new ArgumentException("Invalid word list.");
            if (entropy == null || !(entropy.Length == 16 || entropy.Length == 20 || entropy.Length == 24 || entropy.Length == 28 || entropy.Length == 32))
                throw new ArgumentException("BIP39 entropy must be 128–256 bits, in 32-bit increments.");
            byte[] hash;
            using (SHA256 sha = SHA256.Create()) hash = sha.ComputeHash(entropy);
            int entropyBits = entropy.Length * 8, checksumBits = entropyBits / 32;
            int wordCount = (entropyBits + checksumBits) / 11;
            var indices = new string[wordCount];
            for (int i = 0; i < wordCount; i++)
            {
                int index = 0;
                for (int bit = i * 11; bit < (i + 1) * 11; bit++)
                {
                    bool flag = bit < entropyBits
                        ? (entropy[bit / 8] & (1 << (7 - bit % 8))) != 0
                        : (hash[(bit - entropyBits) / 8] & (1 << (7 - (bit - entropyBits) % 8))) != 0;
                    index = (index << 1) | (flag ? 1 : 0);
                }
                indices[i] = words[index];
            }
            Array.Clear(hash, 0, hash.Length);
            return String.Join(" ", indices);
        }
        internal static bool ValidChecksum(string phrase, string[] words)
        {
            if (phrase == null || words == null || words.Length != 2048) return false;
            string[] tokens = phrase.Normalize(NormalizationForm.FormKD).Split(new[]{' '},StringSplitOptions.None);
            if (!(tokens.Length == 12 || tokens.Length == 15 || tokens.Length == 18 || tokens.Length == 21 || tokens.Length == 24)) return false;
            var lookup = new Dictionary<string,int>(StringComparer.Ordinal);
            for (int i=0;i<words.Length;i++)lookup[words[i]]=i;
            int totalBits=tokens.Length*11, entropyBits=totalBits*32/33;
            byte[] entropy = new byte[entropyBits/8];
            int bitPosition=0;
            foreach(string token in tokens)
            {
                int index;
                if(!lookup.TryGetValue(token,out index))return false;
                for(int j=10;j>=0;j--,bitPosition++)
                    if(bitPosition<entropyBits && ((index>>j)&1)!=0)
                        entropy[bitPosition/8]|=(byte)(1<<(7-bitPosition%8));
            }
            return String.Equals(phrase,FromEntropy(entropy,words),StringComparison.Ordinal);
        }
        internal static string Generate12Words(string[] words)
        {
            byte[] entropy = new byte[16];
            using(RandomNumberGenerator rng=RandomNumberGenerator.Create())rng.GetBytes(entropy);
            try {return FromEntropy(entropy,words);}
            finally {Array.Clear(entropy,0,entropy.Length);}
        }
    }
}
