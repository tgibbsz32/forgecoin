using System;
using System.Security.Cryptography;
using System.Text;
namespace ForgeCoinDesktop
{
    // SLIP-0010 Ed25519 hardened key derivation, with explicit BIP44 Solana path.
    // This does not imply compatibility with every Solana wallet derivation convention.
    internal static class SolanaSlip10
    {
        internal static byte[] DeriveSeed(string mnemonic,string passphrase,uint account=0)
        {
            byte[] bip39=SolanaBip39Seed.Derive(mnemonic,passphrase);
            byte[] chain=null,key=null;
            try {
                byte[] master;
                using(var h=new HMACSHA512(Encoding.ASCII.GetBytes("ed25519 seed")))master=h.ComputeHash(bip39);
                key=new byte[32];chain=new byte[32];
                Buffer.BlockCopy(master,0,key,0,32);Buffer.BlockCopy(master,32,chain,0,32);Array.Clear(master,0,master.Length);
                uint[] path={44,501,account,0};
                foreach(uint part in path){
                    uint index=part|0x80000000u;
                    byte[] input=new byte[37];input[0]=0;Buffer.BlockCopy(key,0,input,1,32);
                    input[33]=(byte)(index>>24);input[34]=(byte)(index>>16);input[35]=(byte)(index>>8);input[36]=(byte)index;
                    byte[] result;
                    using(var h=new HMACSHA512(chain))result=h.ComputeHash(input);
                    Buffer.BlockCopy(result,0,key,0,32);Buffer.BlockCopy(result,32,chain,0,32);
                    Array.Clear(input,0,input.Length);Array.Clear(result,0,result.Length);
                }
                return (byte[])key.Clone();
            } finally {Array.Clear(bip39,0,bip39.Length);if(key!=null)Array.Clear(key,0,key.Length);if(chain!=null)Array.Clear(chain,0,chain.Length);}
        }
    }
}
