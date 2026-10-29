using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Web.Script.Serialization;
using ForgeCoinDesktop;
internal static class SolanaEd25519Smoke
{
 [DllImport("libsodium-26.dll",CallingConvention=CallingConvention.Cdecl)]
 private static extern int sodium_init();
 [DllImport("libsodium-26.dll",CallingConvention=CallingConvention.Cdecl)]
 private static extern int crypto_sign_seed_keypair(byte[] pub,byte[] secret,byte[] seed);
 static void Main(){
  if(sodium_init()<0)throw new Exception("sodium failed");
  byte[] seed=new byte[32];for(int i=0;i<32;i++)seed[i]=(byte)i;
  byte[] pub=new byte[32],secret=new byte[64];
  if(crypto_sign_seed_keypair(pub,secret,seed)!=0)throw new Exception("derivation failed");
  var ser=new JavaScriptSerializer();
  var numbers=new int[64];for(int i=0;i<64;i++)numbers[i]=secret[i];
  string address=SolanaVault.AddressFromKeypair(ser.Serialize(numbers));
  if(String.IsNullOrEmpty(address))throw new Exception("missing address");
  numbers[32]^=1;
  bool rejected=false;try{SolanaVault.AddressFromKeypair(ser.Serialize(numbers));}catch(InvalidDataException){rejected=true;}
  if(!rejected)throw new Exception("mismatched seed and public key accepted");
  Console.WriteLine("ED25519_IMPORT_VALID_AND_TAMPERED_REJECTED");
  Array.Clear(secret,0,secret.Length);Array.Clear(seed,0,seed.Length);
 }
}
