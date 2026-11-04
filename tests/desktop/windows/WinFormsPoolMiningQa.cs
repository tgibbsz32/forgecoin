using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Security.Cryptography;
using System.Threading;
using System.Windows.Forms;

namespace ForgeCoinDesktop
{
    // Only /define:FRG_PRIVATE_UI_QA,FRG_PRIVATE_POOL_QA may compile this
    // harness, not the shipped application. No CPU/GPU hashing, no reachable
    // Stratum endpoint, no ForgeCoin daemon and no wallet secrets are used.
    internal static class WinFormsPoolMiningQa
    {
        private const string PinnedXmrigSha256 =
            "e5cd22ffe8725fbabf32ae2ba993d5b791e65e2ef159ad32ad260505f2e22480";
        private static int count;
        private static string stage = "preflight";

        private static void Check(bool ok, string context)
        {
            count++;
            if (!ok) throw new InvalidOperationException(context);
        }

        private static T Field<T>(MainForm form, string name) where T : class
        {
            FieldInfo field = typeof(MainForm).GetField(
                name, BindingFlags.NonPublic | BindingFlags.Instance);
            Check(field != null, "Expected GUI field is absent");
            return field.GetValue(form) as T;
        }

        private static TabControl FindTabs(Control root)
        {
            if (root is TabControl) return (TabControl)root;
            foreach (Control control in root.Controls)
            {
                TabControl tabs = FindTabs(control);
                if (tabs != null) return tabs;
            }
            return null;
        }

        private static void PortFree(int port)
        {
            TcpListener listener = new TcpListener(IPAddress.Loopback, port);
            try
            {
                listener.Start();
            }
            catch (SocketException)
            {
                throw new InvalidOperationException(
                    "Private miner QA endpoint already in use; will not attach to it.");
            }
            finally { listener.Stop(); }
        }

        private static void CopyPinnedXmrig(string source, string destination)
        {
            Check(File.Exists(source), "Local native XMRig executable absent");
            using (SHA256 sha = SHA256.Create())
            using (FileStream stream = File.OpenRead(source))
            {
                string digest = BitConverter.ToString(sha.ComputeHash(stream))
                    .Replace("-", "").ToLowerInvariant();
                Check(digest == PinnedXmrigSha256,
                      "Native XMRig binary does not match the private QA hash pin");
            }
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(source, destination, false);
        }

        private static bool WaitUntil(Func<bool> predicate, int timeoutMs)
        {
            Stopwatch clock = Stopwatch.StartNew();
            while (clock.ElapsedMilliseconds < timeoutMs)
            {
                Application.DoEvents();
                if (predicate()) return true;
                Thread.Sleep(85);
            }
            return predicate();
        }

        [STAThread]
        public static int Main(string[] args)
        {
            string root = Path.Combine(Path.GetTempPath(),
                "frg-windows-gui-qa-" + Guid.NewGuid().ToString("N"));
            string bin = Path.Combine(root, "bin");
            MainForm form = null;
            try
            {
                Check(args.Length == 1, "Provide the verified local XMRig executable");
                PortFree(39483);
                PortFree(49690);
                string minerBinary = Path.Combine(bin, "xmrig", "xmrig.exe");
                CopyPinnedXmrig(args[0], minerBinary);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_ROOT", root);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_BIN", bin);
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                form = new MainForm();
                form.Show();
                Application.DoEvents();
                stage = "GUI startup";
                var tabs = FindTabs(form);
                Check(tabs != null, "Pool QA tabs absent");
                TabPage page = null;
                foreach (TabPage entry in tabs.TabPages)
                    if (entry.Text == "Pool Mining") page = entry;
                Check(page != null, "Pool Mining tab absent");
                tabs.SelectedTab = page;
                Application.DoEvents();

                var poolUrl = Field<TextBox>(form, "poolUrlBox");
                var user = Field<TextBox>(form, "poolUserBox");
                var worker = Field<TextBox>(form, "poolWorkerBox");
                var password = Field<TextBox>(form, "poolPassBox");
                var start = Field<Button>(form, "startPoolButton");
                var stop = Field<Button>(form, "stopPoolButton");
                var solo = Field<Button>(form, "startMiningButton");
                var send = Field<Button>(form, "sendButton");
                var state = Field<Label>(form, "poolState");
                var accepted = Field<Label>(form, "poolAcceptedValue");
                var rejected = Field<Label>(form, "poolRejectedValue");
                var rate = Field<Label>(form, "poolHashRateValue");
                Check(start.Enabled && !stop.Enabled,
                      "Private QA start is not available in test-only build");
                Check(!solo.Enabled && !send.Enabled,
                      "QA build must keep solo mining and transfers locked");
                poolUrl.Text = "127.0.0.1:49690"; // intentionally unused
                user.Text = new string('1', 95); // nonfunded dummy, syntactic only
                worker.Text = "private-qa";
                password.Text = "x";

                stage = "start click";
                start.PerformClick();
                Check(WaitUntil(() => Field<Process>(form, "poolMiner") != null, 3000),
                      "GUI did not create a native XMRig process");
                Process miner = Field<Process>(form, "poolMiner");
                Check(miner != null && !miner.HasExited,
                      "Private XMRig exited before disconnected API verification");
                string arguments = miner.StartInfo.Arguments;
                Check(arguments.Contains("--no-cpu") &&
                      arguments.Contains("--no-opencl") &&
                      arguments.Contains("--no-cuda"),
                      "Test-only XMRig CPU/GPU mining suppression missing");
                Check(arguments.Contains("127.0.0.1:49690"),
                      "QA must target the intentionally disconnected loopback pool");
                Check(arguments.Contains("--api-id="),
                      "Native XMRig process identity must be configured");
                var instance = Field<string>(form, "poolApiId");
                Check(instance != null && instance.Length == 24,
                      "GUI must use 24-character XMRig-compatible API identity");
                Check(!start.Enabled && stop.Enabled,
                      "Pool GUI start/stop button state incorrect after start");

                stage = "disconnected native API";
                Check(WaitUntil(() =>
                {
                    form.Refresh();
                    return state.Text == "Connecting" &&
                           accepted.Text == "0" &&
                           rejected.Text == "0";
                }, 14000),
                "Real disconnected XMRig must say Connecting and zero accepted/rejected shares");
                Check(rate.Text.StartsWith("0") && state.Text != "Mining" &&
                      state.Text != "Hashing",
                      "Disconnected XMRig incorrectly represented as FRG pool hashing");

                stage = "stop click";
                stop.PerformClick();
                Check(WaitUntil(() => miner.HasExited, 4000),
                      "GUI Stop must terminate the exact private XMRig process");
                Check(Field<Process>(form, "poolMiner") == null,
                      "GUI retained a dead native miner process");
                Check(Field<string>(form, "poolApiId") == null,
                      "Process identity must be erased after Stop");
                Check(state.Text == "Stopped" && !stop.Enabled && start.Enabled,
                      "Pool GUI controls not reset after stop");

                stage = "GUI shutdown";
                form.Close();
                form.Dispose();
                form = null;
                Console.WriteLine("PASS: " + count +
                    " real WinForms XMRig offline pool GUI assertions; " +
                    "Start -> verified disconnected API -> no shares/hash -> Stop");
                Console.WriteLine(
                    "PASS: no public pool, no daemon, no CPU/GPU hash, no wallet, no Oracle");
                return 0;
            }
            catch (Exception failure)
            {
                // Never display the user's wallet, password, pool input,
                // arbitrary native process output or a stack trace.
                Console.Error.WriteLine("FAIL: native pool GUI QA: " +
                    failure.GetType().Name + " at stage " + stage);
                return 1;
            }
            finally
            {
                if (form != null)
                {
                    try { form.Close(); form.Dispose(); } catch { }
                }
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_ROOT", null);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_BIN", null);
                try { Directory.Delete(root, true); } catch { }
            }
        }
    }
}
