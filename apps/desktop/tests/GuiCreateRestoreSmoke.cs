using System;
using System.Collections;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

internal static class ForgeCoinGuiSmoke
{
    static readonly BindingFlags Priv = BindingFlags.Instance | BindingFlags.NonPublic;
    static object Get(object instance, string name) { return instance.GetType().GetField(name, Priv).GetValue(instance); }
    static void Call(object instance, string name)
    {
        try { instance.GetType().GetMethod(name, Priv).Invoke(instance, new object[] { null, EventArgs.Empty }); }
        catch (TargetInvocationException e) { throw new Exception("GUI handler failed: " + name + " / " + e.InnerException.GetType().Name); }
    }
    static TextBox FindSecretInput(Control parent)
    {
        foreach (Control c in parent.Controls)
        {
            TextBox t = c as TextBox;
            if (t != null && t.UseSystemPasswordChar) return t;
            TextBox nested = FindSecretInput(c);
            if (nested != null) return nested;
        }
        return null;
    }
    [STAThread]
    public static int Main(string[] args)
    {
        if (args.Length != 2) return 70;
        string exe=args[0],prefix=args[1];
        if (!File.Exists(exe) || !prefix.StartsWith("ui-smoke-20261026-",StringComparison.Ordinal)) return 71;
        string wallets=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"ForgeCoin","wallets-mainnet-20261026");
        string first=prefix+"-original", second=prefix+"-restored";
        foreach (string name in new string[]{first,second})
        {
            if (File.Exists(Path.Combine(wallets,name)) || File.Exists(Path.Combine(wallets,name+".keys")))
                throw new Exception("Refuse to overwrite an existing wallet");
        }
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Form gui=null;
        string seed = null;
        bool appearedSeed = false;
        bool appearedRestore = false;
        string pass="DISPOSABLE-LOCAL-TEST-ONLY-NotTreasury-20261026";
        System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer();
        try
        {
            var assembly=Assembly.LoadFrom(exe);
            var type=assembly.GetType("ForgeCoinDesktop.MainForm",true);
            gui=(Form)Activator.CreateInstance(type,true);
            ((TextBox)Get(gui,"walletNameBox")).Text=first;
            ((TextBox)Get(gui,"passwordBox")).Text=pass;
            timer.Interval=130;
            timer.Tick+=delegate {
                foreach(Form f in Application.OpenForms)
                {
                    if (f==gui) continue;
                    if (f.Text=="ForgeCoin Recovery Seed")
                    {
                        appearedSeed=true;
                        if(f.AcceptButton!=null) f.AcceptButton.PerformClick();
                    }
                    else if (f.Text.StartsWith("Restore ForgeCoin wallet",StringComparison.Ordinal))
                    {
                        appearedRestore=true;
                        TextBox input=FindSecretInput(f);
                        if(input==null || seed==null) throw new Exception("Secure recovery input or disposable seed missing");
                        input.Text=seed;
                        if(f.AcceptButton!=null) f.AcceptButton.PerformClick();
                    }
                    else if (f.Text=="ForgeCoin")
                    {
                        throw new Exception("GUI emitted an error dialog during create/restore test");
                    }
                }
            };
            gui.Show();
            Application.DoEvents();
            timer.Start();
            Call(gui,"CreateWallet");
            if(!(bool)Get(gui,"walletOpen"))throw new Exception("CreateWallet failed to open a wallet");
            if(!appearedSeed)throw new Exception("CreateWallet did not display the recovery seed dialog");
            string firstAddress=((TextBox)Get(gui,"addressBox")).Text;
            if(firstAddress.Length!=97)throw new Exception("GUI did not display a valid-length public address");
            var rpc=type.GetMethod("Rpc",Priv);
            var response=(IDictionary)rpc.Invoke(gui,new object[]{"http://127.0.0.1:39483/json_rpc","query_key",
                new Dictionary<string,object>{{"key_type","mnemonic"}}});
            seed=Convert.ToString(response["key"]);
            if(seed.Split(new[]{' '},StringSplitOptions.RemoveEmptyEntries).Length!=25)
                throw new Exception("Disposable mnemonic not 25 words");
            Console.WriteLine("PASS GUI CreateWallet: address displayed; seed dialog opened; 25-word disposable mnemonic confirmed (secret withheld)");
            Call(gui,"CloseWallet");
            if((bool)Get(gui,"walletOpen"))throw new Exception("CloseWallet did not reset state");
            ((TextBox)Get(gui,"walletNameBox")).Text=second;
            ((TextBox)Get(gui,"passwordBox")).Text=pass;
            Call(gui,"RestoreWallet");
            if(!(bool)Get(gui,"walletOpen"))throw new Exception("RestoreWallet failed");
            if(!appearedRestore)throw new Exception("RestoreWallet modal did not open");
            string recovered=((TextBox)Get(gui,"addressBox")).Text;
            if(recovered!=firstAddress)throw new Exception("Restored wallet public address differs");
            Console.WriteLine("PASS GUI RestoreWallet: identical public receiving address verified; no seed exposed");
            Call(gui,"CloseWallet");
            seed=null;
            Console.WriteLine("PASS GUI wallet lifecycle create, backup dialog, close, restore, compare and close");
            return 0;
        }
        finally
        {
            seed=null;
            timer.Stop();
            timer.Dispose();
            if(gui!=null){gui.Close();gui.Dispose();}
        }
    }
}
