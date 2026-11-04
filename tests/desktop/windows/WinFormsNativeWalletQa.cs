using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

namespace ForgeCoinDesktop
{
    // Native, isolated, REAL Windows Forms button acceptance. Compile with:
    // /define:FRG_PRIVATE_UI_QA /main:ForgeCoinDesktop.NativeWalletGuiQa
    //
    // The *only* permitted wallet sidecar is the hash-pinned private 20261026
    // candidate. There is NO daemon binary or external network. Every wallet
    // file is created under an owned temporary QA folder, never %LOCALAPPDATA%.
    internal static class NativeWalletGuiQa
    {
        private const string WalletPin =
            "739eefe916f9a93017c870dde63b45c8db532d43226dc888395860122c3e851b";
        private static int checks;

        private static void Check(bool condition, string description)
        {
            checks++;
            if (!condition) throw new InvalidOperationException(description);
        }

        private static T Field<T>(MainForm form, string name) where T : class
        {
            var field = typeof(MainForm).GetField(name,
                BindingFlags.Instance | BindingFlags.NonPublic);
            Check(field != null, "Missing GUI control");
            return field.GetValue(form) as T;
        }

        private static string GetAddress(MainForm form)
        {
            var rpc = typeof(MainForm).GetMethod("Rpc",
                BindingFlags.Instance | BindingFlags.NonPublic);
            Check(rpc != null, "Local authenticated wallet RPC missing");
            IDictionary result = (IDictionary)rpc.Invoke(form, new object[] {
                "http://127.0.0.1:39484/json_rpc",
                "get_address",
                new Dictionary<string, object> { {"account_index", 0} },
                6000
            });
            Check(result != null && result.Contains("address"),
                  "Native wallet did not return an address");
            string address = Convert.ToString(result["address"]);
            Check(FrgWalletInput.LooksLikePublicAddress(address),
                  "Native wallet returned invalid public address syntax");
            return address;
        }

        private static void EnsureLoopbackPortUnused(int port)
        {
            TcpListener listener = null;
            try
            {
                listener = new TcpListener(IPAddress.Loopback, port);
                listener.Start();
            }
            catch (SocketException)
            {
                throw new InvalidOperationException(
                    "Another local wallet/daemon service occupies the QA endpoint");
            }
            finally
            {
                if (listener != null) listener.Stop();
            }
        }

        private static void CopyPinnedWallet(string binaryRoot, string qaBin)
        {
            string source = Path.Combine(binaryRoot, "forge-wallet-rpc.exe");
            Check(File.Exists(source), "Candidate FRG wallet executable missing");
            using (var sha = SHA256.Create())
            using (var file = File.OpenRead(source))
            {
                string digest = BitConverter.ToString(sha.ComputeHash(file))
                    .Replace("-", "").ToLowerInvariant();
                Check(digest == WalletPin, "Unpinned native wallet binary rejected");
            }
            foreach (string file in new [] {
                "forge-wallet-rpc.exe", "libiconv-2.dll", "libicuin78.dll",
                "libicuuc78.dll", "libicudt78.dll", "libgcc_s_seh-1.dll",
                "libstdc++-6.dll", "libwinpthread-1.dll"
            })
            {
                string sourceFile = Path.Combine(binaryRoot, file);
                Check(File.Exists(sourceFile), "Required private QA runtime missing");
                File.Copy(sourceFile, Path.Combine(qaBin, file), false);
            }
            Check(!File.Exists(Path.Combine(qaBin, "forged.exe")),
                  "Offline wallet GUI QA must not ship a daemon");
        }

        private static TextBox SearchTextbox(Control root)
        {
            if (root is TextBox) return (TextBox)root;
            foreach (Control child in root.Controls)
            {
                var result = SearchTextbox(child);
                if (result != null) return result;
            }
            return null;
        }

        private static Button SearchButton(Control root, string caption)
        {
            if (root is Button && root.Text == caption) return (Button)root;
            foreach (Control child in root.Controls)
            {
                var result = SearchButton(child, caption);
                if (result != null) return result;
            }
            return null;
        }

        [STAThread]
        public static int Main(string[] args)
        {
            string temporary = Path.Combine(Path.GetTempPath(),
                "frg-windows-gui-qa-" + Guid.NewGuid().ToString("N"));
            string qaBin = Path.Combine(temporary, "bin");
            MainForm form = null;
            try
            {
                Check(args.Length == 1, "Require the private candidate binary folder");
                EnsureLoopbackPortUnused(39481);
                EnsureLoopbackPortUnused(39484);
                Directory.CreateDirectory(qaBin);
                CopyPinnedWallet(args[0], qaBin);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_ROOT", temporary);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_BIN", qaBin);
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                string password = Guid.NewGuid().ToString("N") + "Qa";
                string seed = null;
                form = new MainForm();
                form.Show();
                Application.DoEvents();
                var name = Field<TextBox>(form, "walletNameBox");
                var pass = Field<TextBox>(form, "passwordBox");
                var create = Field<Button>(form, "createWalletButton");
                var close = Field<Button>(form, "closeWalletButton");
                var restore = Field<Button>(form, "restoreWalletButton");
                var send = Field<Button>(form, "sendButton");
                var solo = Field<Button>(form, "startMiningButton");
                var pool = Field<Button>(form, "startPoolButton");
                Check(!send.Enabled && !solo.Enabled && !pool.Enabled,
                      "Native public spend/mining controls must remain locked");
                name.Text = "private_gui_qa_original";
                pass.Text = password;

                bool seedDialogSeen = false;
                using (var timer = new System.Windows.Forms.Timer { Interval = 70 })
                {
                    timer.Tick += delegate
                    {
                        foreach (Form modal in Application.OpenForms)
                        {
                            if (modal.Text != "ForgeCoin Recovery Seed") continue;
                            TextBox words = SearchTextbox(modal);
                            Check(words != null, "GUI seed dialog did not display a textbox");
                            seed = FrgWalletInput.NormalizeEnglishMnemonic(words.Text);
                            var done = SearchButton(modal, "I saved it");
                            Check(done != null, "Seed backup dialog has no completion button");
                            seedDialogSeen = true;
                            timer.Stop();
                            done.PerformClick();
                            break;
                        }
                    };
                    timer.Start();
                    create.PerformClick(); // actual GUI Create button; native RPC
                    timer.Stop();
                }
                Check(seedDialogSeen && seed != null && seed.Split(' ').Length == 25,
                      "GUI never displayed native 25-word wallet backup");
                Check(Field<Process>(form, "walletRpc") != null,
                      "GUI failed to start private authenticated native wallet");
                Check(!File.Exists(Path.Combine(temporary,
                    "rpc-private", "wallet-rpc-legacy.conf")),
                    "Private QA must not generate a legacy RPC credential");
                var configFolder = Path.Combine(temporary, "rpc-private");
                Check(Directory.Exists(configFolder) &&
                      Directory.GetFiles(configFolder, "*.conf").Length == 0,
                      "Sensitive startup RPC config was not deleted after authentication");
                string addressOriginal = GetAddress(form);
                Check(!send.Enabled && !solo.Enabled && !pool.Enabled,
                      "Creating disposable wallet improperly enabled mainnet payments/mining");

                close.PerformClick();
                Check(!(bool)Field<object>(form, "walletOpen"),
                      "GUI did not close disposable native wallet");

                name.Text = "private_gui_qa_restored";
                pass.Text = password;
                bool restoreDialogSeen = false;
                using (var timer = new System.Windows.Forms.Timer { Interval = 70 })
                {
                    timer.Tick += delegate
                    {
                        foreach (Form modal in Application.OpenForms)
                        {
                            if (modal.Text != "Restore a disposable FRG test wallet")
                                continue;
                            TextBox seedInput = SearchTextbox(modal);
                            Check(seedInput != null && seedInput.UseSystemPasswordChar,
                                  "Recovery seed should be concealed by default");
                            seedInput.Text = seed; // disposable seed, in-memory only
                            Button submit = SearchButton(modal, "Restore test wallet");
                            Check(submit != null, "GUI restore confirmation absent");
                            restoreDialogSeen = true;
                            timer.Stop();
                            submit.PerformClick();
                            break;
                        }
                    };
                    timer.Start();
                    restore.PerformClick(); // actual GUI Restore button; native RPC
                    timer.Stop();
                }
                Check(restoreDialogSeen, "GUI native 25-word restore dialog did not open");
                Check((bool)Field<object>(form, "walletOpen"), "GUI failed to open restored wallet");
                string addressRestored = GetAddress(form);
                Check(String.Equals(addressOriginal, addressRestored,
                                    StringComparison.Ordinal),
                      "GUI recovery did not reproduce the original native public address");

                close.PerformClick();
                Check(!(bool)Field<object>(form, "walletOpen"), "Restored wallet remained open");
                Check(!send.Enabled && !solo.Enabled && !pool.Enabled,
                      "GUI unexpectedly authorized native mining or transfers");
                seed = null;
                pass.Clear();
                form.Close();
                form.Dispose();
                form = null;
                // No daemon, public peers, chain or mining created.
                Check(!Directory.Exists(Path.Combine(temporary, "blockchain")) ||
                      Directory.GetFiles(Path.Combine(temporary, "blockchain")).Length == 0,
                      "GUI test unexpectedly created local blockchain data");
                Console.WriteLine("PASS: " + checks + " real GUI and native wallet acceptance checks; " +
                    "Create -> 25-word backup -> Close -> Restore -> matching address; " +
                    "no seeds/addresses logged, no mining, transfers, daemon or Oracle");
                return 0;
            }
            catch (Exception failure)
            {
                // This diagnostic is intentionally limited to a type/name.
                // Native RPC errors, passwords, addresses and mnemonic text
                // must never be written to logs.
                Console.Error.WriteLine("FAIL: private native GUI wallet acceptance: " +
                                        failure.GetType().Name);
                return 1;
            }
            finally
            {
                if (form != null) {
                    try { form.Close(); form.Dispose(); } catch { }
                }
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_ROOT", null);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_BIN", null);
                try { Directory.Delete(temporary, true); } catch { }
            }
        }
    }
}
