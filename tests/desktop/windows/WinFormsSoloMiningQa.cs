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
using System.Threading;
using System.Windows.Forms;
using System.Web.Script.Serialization;

namespace ForgeCoinDesktop
{
    // Actual GUI -> native daemon -> RandomX START/STATUS/STOP integration.
    // Compile ONLY with BOTH private test flags:
    // /define:FRG_PRIVATE_UI_QA,FRG_PRIVATE_MINING_QA
    // /main:ForgeCoinDesktop.WinFormsSoloMiningQa
    //
    // Never include this test entrypoint or flags in normal/public packages.
    // Runtime executes only the hash-pinned daemon inside an isolated Temp
    // directory, strictly offline and loopback-only with no P2P peers.
    internal static class WinFormsSoloMiningQa
    {
        private const string ExpectedDaemon =
            "3efaf014c7fdfcea167630f1884abee2defd40f28f1e725b6c0a8fcede5b5c37";
        private const string ExpectedGenesis =
            "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c";
        // Public address from native isolated wallet QA. No secret material.
        private const string DisposablePayout =
            "YnJ4sygA2VbA4nvoXssZcSKh4fwsw4g3DaujrVCDXSwWGuXwnYTfNsKPVunwuAf8joPEWfePpMh6CEsyEqMpQz2i2uFy112XA";

        private static int checks;
        private static string stage = "setup";

        private static void Check(bool condition, string message)
        {
            checks++;
            if (!condition) throw new InvalidOperationException(message);
        }

        private static T Field<T>(MainForm form, string name) where T : class
        {
            FieldInfo info = typeof(MainForm).GetField(name,
                BindingFlags.NonPublic | BindingFlags.Instance);
            Check(info != null, "Expected WinForms control was not found");
            return info.GetValue(form) as T;
        }

        private static TabControl Tabs(Control root)
        {
            TabControl tab = root as TabControl;
            if (tab != null) return tab;
            foreach (Control child in root.Controls)
            {
                tab = Tabs(child);
                if (tab != null) return tab;
            }
            return null;
        }

        private static void SelectTab(TabControl tabs, string name)
        {
            foreach (TabPage tab in tabs.TabPages)
                if (tab.Text == name)
                {
                    tabs.SelectedTab = tab;
                    Application.DoEvents();
                    return;
                }
            throw new InvalidOperationException("Expected mining QA tab not found");
        }

        private static void CheckPortsFree()
        {
            foreach (int port in new int[] { 39480, 39481, 39484 })
            {
                TcpListener test = new TcpListener(IPAddress.Loopback, port);
                try { test.Start(); }
                catch (SocketException)
                {
                    throw new InvalidOperationException("A native port was already occupied");
                }
                finally { test.Stop(); }
            }
        }

        private static void CopyVerifiedDaemon(string sourceRoot, string target)
        {
            string exe = Path.Combine(sourceRoot, "forged.exe");
            Check(File.Exists(exe), "Native candidate is absent");
            using (SHA256 sha = SHA256.Create())
            using (FileStream input = File.OpenRead(exe))
            {
                string digest = BitConverter.ToString(sha.ComputeHash(input))
                    .Replace("-", "").ToLowerInvariant();
                Check(digest == ExpectedDaemon, "Daemon hash pin mismatch");
            }
            string[] names = {
                "forged.exe", "libiconv-2.dll", "libicuin78.dll",
                "libicuuc78.dll", "libicudt78.dll", "libgcc_s_seh-1.dll",
                "libstdc++-6.dll", "libwinpthread-1.dll"
            };
            foreach (string name in names)
            {
                string full = Path.Combine(sourceRoot, name);
                Check(File.Exists(full), "Native runtime support missing");
                File.Copy(full, Path.Combine(target, name), false);
            }
            Check(!File.Exists(Path.Combine(target, "forge-wallet-rpc.exe")),
                  "This private mining QA must not include wallet custody");
            Check(!File.Exists(Path.Combine(target, "xmrig.exe")),
                  "This private solo QA must not run a pool miner");
        }

        private static IDictionary ReadRpc(string path, bool jsonRpc,
                                           string method, object parameters)
        {
            var data = jsonRpc
                ? new Dictionary<string, object> {
                    { "jsonrpc", "2.0" }, { "id", "isolated-gui-mining-qa" },
                    { "method", method }, { "params", parameters }
                  }
                : (object)parameters;
            byte[] body = Encoding.UTF8.GetBytes(
                new JavaScriptSerializer().Serialize(data));
            var req = (HttpWebRequest)WebRequest.Create(
                "http://127.0.0.1:39481/" + path);
            req.Proxy = null;
            req.AllowAutoRedirect = false;
            req.KeepAlive = false;
            req.ServicePoint.Expect100Continue = false;
            req.Timeout = 4500;
            req.ReadWriteTimeout = 4500;
            req.Method = "POST";
            req.ContentType = "application/json";
            req.ContentLength = body.Length;
            using (Stream stream = req.GetRequestStream())
                stream.Write(body, 0, body.Length);
            using (var response = (HttpWebResponse)req.GetResponse())
            using (var reader = new StreamReader(response.GetResponseStream()))
            {
                Check(response.StatusCode == HttpStatusCode.OK,
                      "Offline native RPC status was not HTTP 200");
                IDictionary reply = new JavaScriptSerializer()
                    .DeserializeObject(reader.ReadToEnd()) as IDictionary;
                Check(reply != null && (!reply.Contains("error") ||
                      reply["error"] == null), "Native offline RPC returned an error");
                if (jsonRpc)
                {
                    Check(reply.Contains("result") && reply["result"] is IDictionary,
                          "Native offline JSON-RPC had no result");
                    return (IDictionary)reply["result"];
                }
                return reply;
            }
        }

        private static IDictionary Info()
        {
            return ReadRpc("get_info", false, null,
                           new Dictionary<string, object>());
        }

        private static IDictionary Mining()
        {
            return ReadRpc("mining_status", false, null,
                           new Dictionary<string, object>());
        }

        private static bool WaitUntil(Func<bool> condition, int seconds,
                                      Process child)
        {
            Stopwatch clock = Stopwatch.StartNew();
            while (clock.Elapsed.TotalSeconds < seconds)
            {
                Application.DoEvents();
                Check(child != null && !child.HasExited,
                      "Private native daemon ended unexpectedly");
                try { if (condition()) return true; }
                catch (WebException) { }
                catch (IOException) { }
                Thread.Sleep(250);
            }
            return false;
        }

        [STAThread]
        public static int Main(string[] args)
        {
            string basePath = Path.Combine(Path.GetTempPath(),
                "frg-windows-gui-qa-" + Guid.NewGuid().ToString("N"));
            string qaBin = Path.Combine(basePath, "bin");
            MainForm form = null;
            try
            {
                Check(args.Length == 1, "The pinned private binary directory is required");
                CheckPortsFree();
                Directory.CreateDirectory(qaBin);
                CopyVerifiedDaemon(args[0], qaBin);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_ROOT", basePath);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_BIN", qaBin);
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);

                stage = "form";
                form = new MainForm();
                form.Show();
                Application.DoEvents();

                TabControl tabs = Tabs(form);
                Check(tabs != null && tabs.TabPages.Count >= 7,
                      "Desktop mining tabs missing");
                var startNode = Field<Button>(form, "startNodeButton");
                var stopNode = Field<Button>(form, "stopNodeButton");
                var offline = Field<CheckBox>(form, "bootstrapModeBox");
                var start = Field<Button>(form, "startMiningButton");
                var stop = Field<Button>(form, "stopMiningButton");
                var miningDetail = Field<Label>(form, "miningDetailLabel");
                var reward = Field<TextBox>(form, "miningAddressBox");
                var threads = Field<NumericUpDown>(form, "miningThreads");
                var pool = Field<Button>(form, "startPoolButton");
                Check(!start.Enabled && !pool.Enabled,
                      "Startup unexpectedly allowed native mining");

                stage = "private_node";
                SelectTab(tabs, "Node");
                offline.Checked = true;
                Check(startNode.Enabled, "Private offline node opt-in did not work");
                startNode.PerformClick();
                Process node = Field<Process>(form, "daemon");
                Check(node != null && !node.HasExited,
                      "WinForms did not start the isolated daemon");
                string flags = node.StartInfo.Arguments;
                Check(flags.Contains("--offline") &&
                      flags.Contains("--out-peers 0") &&
                      flags.Contains("--in-peers 0") &&
                      flags.Contains("--p2p-bind-ip 127.0.0.1") &&
                      flags.Contains("--rpc-bind-ip 127.0.0.1"),
                      "Daemon is not restricted to offline localhost mode");
                Check(WaitUntil(delegate
                {
                    IDictionary info = Info();
                    return Convert.ToInt64(info["height"]) == 1;
                }, 30, node), "Offline genesis node did not reach height 1");
                IDictionary state = Info();
                Check(Convert.ToInt64(state["height"]) == 1,
                      "QA chain is not at frozen genesis");
                Check(Convert.ToString(state["nettype"]) == "mainnet",
                      "QA native daemon uses the wrong network identity");
                Check(Convert.ToInt64(state["incoming_connections_count"]) == 0 &&
                      Convert.ToInt64(state["outgoing_connections_count"]) == 0,
                      "Private offline QA had a nonlocal peer connection");
                IDictionary header = ReadRpc("json_rpc", true,
                    "get_block_header_by_height",
                    new Dictionary<string, object> { { "height", 0 } });
                IDictionary genesis = header["block_header"] as IDictionary;
                Check(genesis != null && Convert.ToString(genesis["hash"]) == ExpectedGenesis,
                      "Isolated native node genesis hash mismatch");
                Console.WriteLine("PASS: GUI started pinned native ForgeCoin daemon at frozen genesis, localhost offline, zero peers");

                stage = "solo_start";
                SelectTab(tabs, "Solo Mining");
                reward.Text = DisposablePayout;
                threads.Value = Math.Min(2, (int)threads.Maximum);
                Console.WriteLine("QA_SOLO_UI_ENABLED=" + start.Enabled);
                Check(start.Enabled, "Private GUI solo mining control not enabled");
                start.PerformClick();
                Console.WriteLine("QA_SOLO_START_CLICK_RETURNED");
                Check(WaitUntil(delegate {
                    Check(miningDetail.Text.IndexOf("rejected",
                        StringComparison.OrdinalIgnoreCase) < 0,
                        "Native GUI solo start was rejected");
                    return stop.Enabled;
                }, 65, node),
                      "WinForms did not confirm the asynchronous native mining start");
                Check(WaitUntil(delegate
                {
                    IDictionary status = Mining();
                    return status.Contains("active") &&
                           Convert.ToBoolean(status["active"]);
                }, 20, node), "Native RandomX mining did not enter active state");
                Console.WriteLine("PASS: WinForms Start Mining invoked native RandomX start_mining, mining_status.active=true");

                stage = "hashing";
                bool measured = WaitUntil(delegate
                {
                    IDictionary status = Mining();
                    if (Convert.ToInt64(Info()["incoming_connections_count"]) != 0 ||
                        Convert.ToInt64(Info()["outgoing_connections_count"]) != 0)
                        throw new InvalidOperationException(
                            "A peer appeared during private QA mining");
                    if (!status.Contains("speed")) return false;
                    return Convert.ToDouble(status["speed"]) > 0.0;
                }, 35, node);
                Check(measured, "Native RandomX hashrate did not become positive");
                Console.WriteLine("PASS: isolated native RandomX reported positive hashing speed through desktop GUI");

                stage = "solo_stop";
                stop.PerformClick();
                Check(WaitUntil(delegate
                {
                    IDictionary status = Mining();
                    return status.Contains("active") &&
                           !Convert.ToBoolean(status["active"]);
                }, 15, node), "Native RandomX mining did not stop");
                Check(!stop.Enabled, "Stop Mining remained enabled after stopping");
                Check(!pool.Enabled, "Isolated solo QA must not enable public pool mining");
                Console.WriteLine("PASS: WinForms Stop Mining stopped native RandomX; public pool and wallet spend controls untouched");

                stage = "shutdown";
                SelectTab(tabs, "Node");
                stopNode.PerformClick();
                Check(node.HasExited || node.WaitForExit(6000),
                      "GUI did not terminate its private native daemon");
                form.Close();
                form.Dispose();
                form = null;
                Console.WriteLine("PASS: " + checks + " offline real WinForms solo QA checks; no external peer, pool, wallet or Oracle");
                return 0;
            }
            catch (Exception ex)
            {
                // A native error may include a wallet address; never emit
                // exception details or private directory names.
                Console.Error.WriteLine("FAIL: isolated GUI solo RandomX QA at " +
                                        stage + " (" + ex.GetType().Name + ")");
                return 1;
            }
            finally
            {
                if (form != null) {
                    try
                    {
                        // Never invoke a modal "Stop node?" confirmation in
                        // a headless test failure path. Kill only the daemon
                        // process owned by this disposable MainForm instance.
                        FieldInfo ownedField = typeof(MainForm).GetField(
                            "daemon", BindingFlags.Instance |
                                      BindingFlags.NonPublic);
                        Process owned = ownedField == null ? null :
                            ownedField.GetValue(form) as Process;
                        if (owned != null && !owned.HasExited)
                        {
                            owned.Kill();
                            owned.WaitForExit(7000);
                        }
                        form.Close(); form.Dispose();
                    }
                    catch { }
                }
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_ROOT", null);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_BIN", null);
                try { Directory.Delete(basePath, true); } catch { }
            }
        }
    }
}
