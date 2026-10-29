using System;
using System.Runtime.InteropServices;
using ForgeCoinDesktop;
internal static class SolanaSlip10Smoke
{
 [DllImport("libsodium-26.dll",CallingConvention=CallingConvention.Cdecl)]static extern int sodium_init();
 [DllImport("libsodium-26.dll",CallingConvention=CallingConvention.Cdecl)]static extern int crypto_sign_seed_keypair(byte[] pub,byte[] secret,byte[] seed);
 static string Hex(byte[] b){return BitConverter.ToString(b).Replace("-","").ToLowerInvariant();}
 static int Main(){
   string phrase="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
   byte[] a=SolanaSlip10.DeriveSeed(phrase,"");
   byte[] b=SolanaSlip10.DeriveSeed(phrase,"");
   byte[] c=SolanaSlip10.DeriveSeed(phrase,"",1);
   if(a.Length!=32 || Hex(a)!=Hex(b) || Hex(a)==Hex(c))throw new Exception("Invalid deterministic hardened derivation");
   if(sodium_init()<0)throw new Exception("Sodium unavailable");
   byte[] pub=new byte[32],secret=new byte[64];
   if(crypto_sign_seed_keypair(pub,secret,a)!=0)throw new Exception("Ed25519 unavailable");
   Console.WriteLine("SLIP10_DERIVATION_DETERMINISTIC_AND_ACCOUNT_SEPARATION_OK");
   const string knownPublicHex="f036276246a75b9de3349ed42b15e232f6518fc20f5fcd4f1d64e81f9bd258f7";
   if(Hex(pub)!=knownPublicHex)throw new Exception("Known address-derivation vector mismatch");
   Console.WriteLine("SLIP10_KNOWN_PUBLIC_KEY_VECTOR_OK");
   Array.Clear(a,0,a.Length);Array.Clear(b,0,b.Length);Array.Clear(c,0,c.Length);Array.Clear(secret,0,secret.Length);
   return 0;
 }
}
