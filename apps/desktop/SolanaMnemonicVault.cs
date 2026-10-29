using System;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
namespace ForgeCoinDesktop
{
    // In-memory 12-word mnemonic -> SLIP10 Ed25519 -> encrypted vault.
    // Keep this detached from production GUI controls until end-to-end review.
    internal static class SolanaMnemonicVault
    {
        internal static string EncryptFromPhrase(string phrase,string passphrase,string password,string[] words)
        {
            if(!SolanaBip39Mnemonic.ValidChecksum(phrase,words))
                throw new ArgumentException("BIP39 phrase checksum invalid.");
            byte[] seed=SolanaSlip10.DeriveSeed(phrase,passphrase);
            byte[] pub=new byte[32],secret=new byte[64];
            try {
                if(SolanaEd25519Interop.GenerateFromSeed(pub,secret,seed)!=0)
                    throw new CryptographicException("Ed25519 derivation unavailable.");
                int[] values=new int[64];
                for(int i=0;i<64;i++)values[i]=secret[i];
                try{return SolanaVault.Encrypt(new JavaScriptSerializer().Serialize(values),phrase,password);}
                finally{Array.Clear(values,0,values.Length);}
            } finally {
                Array.Clear(seed,0,seed.Length);Array.Clear(pub,0,pub.Length);Array.Clear(secret,0,secret.Length);
            }
        }
    }
    internal static class SolanaEd25519Interop
    {
        [System.Runtime.InteropServices.DllImport("libsodium-26.dll", CallingConvention=System.Runtime.InteropServices.CallingConvention.Cdecl)]
        private static extern int sodium_init();
        [System.Runtime.InteropServices.DllImport("libsodium-26.dll", CallingConvention=System.Runtime.InteropServices.CallingConvention.Cdecl)]
        private static extern int crypto_sign_seed_keypair(byte[] publicKey,byte[] privateKey,byte[] seed);
        internal static int GenerateFromSeed(byte[] pub,byte[] secret,byte[] seed)
        {
            if(sodium_init()<0)throw new CryptographicException("libsodium initialization failed");
            return crypto_sign_seed_keypair(pub,secret,seed);
        }
    }
}
