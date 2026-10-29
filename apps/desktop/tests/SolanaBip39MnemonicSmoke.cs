using System;
using ForgeCoinDesktop;
internal static class SolanaBip39MnemonicSmoke
{
 static int Main(string[] args)
 {
  try {
   string[] words=SolanaBip39Mnemonic.LoadWords(args[0]);
   byte[] zeros=new byte[16];
   string standard="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
   if(SolanaBip39Mnemonic.FromEntropy(zeros,words)!=standard)throw new Exception("Reference mnemonic mismatch");
   if(!SolanaBip39Mnemonic.ValidChecksum(standard,words))throw new Exception("Known checksum rejected");
   if(SolanaBip39Mnemonic.ValidChecksum(standard.Replace("about","zoo"),words))throw new Exception("Bad checksum accepted");
   string generated=SolanaBip39Mnemonic.Generate12Words(words);
   if(!SolanaBip39Mnemonic.ValidChecksum(generated,words))throw new Exception("Generated checksum invalid");
   Console.WriteLine("BIP39_MNEMONIC_VECTOR_CHECKSUM_AND_GENERATION_OK");
   return 0;
  }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}
 }
}
