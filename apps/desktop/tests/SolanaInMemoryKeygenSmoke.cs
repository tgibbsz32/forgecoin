using System;
using ForgeCoinDesktop;
internal class SolanaInMemoryKeygenSmoke
{
 static void Main()
 {
  const string password="Disposable-Test-Password-Only-2026!";
  string a=SolanaVault.GenerateEncryptedKeypairInMemory(password);
  string b=SolanaVault.GenerateEncryptedKeypairInMemory(password);
  var first=SolanaVault.Decrypt(a,password);
  var second=SolanaVault.Decrypt(b,password);
  if(first.Address==second.Address)throw new Exception("Generated identical keypairs");
  if(first.Mnemonic!="")throw new Exception("Invented mnemonic");
  if(SolanaVault.AddressFromKeypair(first.KeypairJson)!=first.Address)throw new Exception("Invalid keypair");
  bool rejected=false;
  try{SolanaVault.Decrypt(a,"wrong-password-for-test");}catch(System.Security.Cryptography.CryptographicException){rejected=true;}
  if(!rejected)throw new Exception("Wrong password accepted");
  Console.WriteLine("IN_MEMORY_KEYGEN_ENCRYPTED_ROUNDTRIP_OK");
 }
}
