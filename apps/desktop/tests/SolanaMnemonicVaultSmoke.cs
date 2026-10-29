using System;
using ForgeCoinDesktop;
internal static class SolanaMnemonicVaultSmoke
{
 static int Main(string[] args){
  try{
   var words=SolanaBip39Mnemonic.LoadWords(args[0]);
   const string phrase="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
   const string password="Test-Only-Vault-Password-2026!";
   string encrypted=SolanaMnemonicVault.EncryptFromPhrase(phrase,"",password,words);
   var restored=SolanaVault.Decrypt(encrypted,password);
   if(restored.Mnemonic!=phrase)throw new Exception("Mnemonic mismatch");
   string again=SolanaMnemonicVault.EncryptFromPhrase(restored.Mnemonic,"",password,words);
   if(SolanaVault.PublicAddress(again)!=restored.Address)throw new Exception("Recovery address mismatch");
   if(SolanaVault.PublicAddress(encrypted)!=restored.Address)throw new Exception("Vault public address mismatch");
   bool rejected=false;try{SolanaMnemonicVault.EncryptFromPhrase(phrase.Replace("about","zoo"),"",password,words);}catch(ArgumentException){rejected=true;}
   if(!rejected)throw new Exception("Invalid checksum accepted");
   Console.WriteLine("SOLANA_MNEMONIC_ENCRYPTED_VAULT_RECOVERY_ROUNDTRIP_OK");
   return 0;
  }catch(Exception e){Console.Error.WriteLine(e);return 1;}
 }
}
