using System;
using System.Collections;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using ForgeCoinDesktop;
internal static class SolanaVaultSmoke
{
    static int tests;
    static void Check(bool value, string label) {
        if(!value)throw new Exception("FAILED "+label);
        Console.WriteLine("PASS "+label);tests++;
    }
    static string Root;
    static object Field(MainForm f,string name) {
        return typeof(MainForm).GetField(name,BindingFlags.NonPublic|BindingFlags.Instance).GetValue(f);
    }
    static void Click(MainForm f,string method) {
        typeof(MainForm).GetMethod(method,BindingFlags.NonPublic|BindingFlags.Instance)
          .Invoke(f,new object[]{null,EventArgs.Empty});
        Application.DoEvents();
    }
    [STAThread]
    public static int Main()
    {
        Root=Path.Combine(Path.GetTempPath(),"frg-solanavault-smoke-"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Root);
        Environment.SetEnvironmentVariable("FORGECOIN_SOLANA_QA_ROOT",Path.Combine(Root,"wallets"));
        MainForm form=null;
        try {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            form=new MainForm();
            form.Show();Application.DoEvents();
            Check(form.IsHandleCreated,"actual WinForms desktop form launched");
            bool tab=false;
            foreach(Control c in form.Controls)tab=tab||HasSolTab(c);
            Check(tab,"actual GUI contains Solana/mFRG tab");
            ((TextBox)Field(form,"solWalletNameBox")).Text="smokeqa";
            ((TextBox)Field(form,"solPasswordBox")).Text="Test-only-encryption-2026-Strong";
            ((TextBox)Field(form,"solConfirmPasswordBox")).Text="Test-only-encryption-2026-Strong";
            Click(form,"SolanaCreate");
            string vaultFile=Path.Combine(Root,"wallets","smokeqa.frgsol");
            Check(File.Exists(vaultFile),"GUI created local encrypted Solana wallet file");
            string data=File.ReadAllText(vaultFile);
            Check(!data.Contains("keypair")&&!data.Contains("mnemonic")&&!data.Contains("Test-only-encryption"),
                "on-disk vault contains no plaintext private key, phrase, or password");
            string address=SolanaVault.PublicAddress(data);
            Check(address==((TextBox)Field(form,"solAddressBox")).Text && address.Length>=32,
                "GUI address equals encrypted vault public address");
            SolanaVault.WalletSecret unlocked=SolanaVault.Decrypt(data,"Test-only-encryption-2026-Strong");
            Check(unlocked.Address==address&&SolanaVault.AddressFromKeypair(unlocked.KeypairJson)==address,
                "encrypted keypair derives identical Solana address");
            Check(unlocked.Mnemonic.Split(' ').Length==12,"recovery phrase stored encrypted and contains 12 words");
            bool wrongRejected=false;
            try{SolanaVault.Decrypt(data,"Wrong-wallet-password");}catch(CryptographicException){wrongRejected=true;}
            Check(wrongRejected,"wrong vault password rejected with MAC verification");
            string backup=Path.Combine(Root,"offline-backup.frgsol");
            File.Copy(vaultFile,backup);
            Check(SolanaVault.Decrypt(File.ReadAllText(backup),"Test-only-encryption-2026-Strong").Address==address,
                "portable encrypted backup restores same public address");
            string changed=data.Replace("\"ciphertext\":\"","\"ciphertext\":\"X");
            bool tamperRejected=false;
            try {SolanaVault.Decrypt(changed,"Test-only-encryption-2026-Strong");}
            catch(Exception){tamperRejected=true;}
            Check(tamperRejected,"tampered vault ciphertext rejected");
            Click(form,"SolanaLockClick");
            Check(((TextBox)Field(form,"solAddressBox")).Text=="Wallet locked.",
                "Solana Lock clears wallet address and active handle");
            ((TextBox)Field(form,"solPasswordBox")).Text="Test-only-encryption-2026-Strong";
            Click(form,"SolanaOpen");
            Check(((TextBox)Field(form,"solAddressBox")).Text==address,
                "GUI wallet can reopen encrypted file after lock");
            Check(((ComboBox)Field(form,"solNetworkSelector")).SelectedIndex==0,
                "mainnet-beta is default display network");
            Check(((Label)Field(form,"solMfrgBalanceLabel")).Text=="Not issued on mainnet",
                "no nonexistent mainnet mFRG token balance presented as issued");
            Check(!Directory.Exists(Path.Combine(Root,"keygen-tmp")), // actual temp path is sibling with unique suffix
                "no fixed-name temporary private keypair directory");
            string parent=Path.GetDirectoryName(Path.Combine(Root,"wallets"));
            Check(Directory.GetDirectories(parent,"keygen-tmp-*").Length==0,
                "all temporary plaintext keypair creation folders removed");
            Console.WriteLine("PASS SOLANA_GUI_AND_VAULT_SMOKE="+tests);
            return 0;
        }catch(Exception ex){
            Console.Error.WriteLine("SOLANA_SMOKE_FAILED: "+ex.GetType().Name+": "+ex.Message);
            return 2;
        }finally {
            if(form!=null){form.Close();form.Dispose();}
            try { Directory.Delete(Root,true); }catch{}
            Environment.SetEnvironmentVariable("FORGECOIN_SOLANA_QA_ROOT",null);
        }
    }
    static bool HasSolTab(Control root) {
        TabControl t=root as TabControl;
        if(t!=null)foreach(TabPage page in t.TabPages)
          if(page.Text=="Solana / mFRG")return true;
        foreach(Control c in root.Controls)if(HasSolTab(c))return true;
        return false;
    }
}
