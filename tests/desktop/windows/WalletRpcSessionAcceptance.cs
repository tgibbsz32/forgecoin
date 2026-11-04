using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

namespace ForgeCoinDesktop
{
    /// <summary>
    /// Real Windows native wallet-RPC create / 25-word restore / restart
    /// acceptance with production WalletRpcSession (HTTP Digest).
    /// Disposable wallets only; no daemon, peers, mining, transfer or Oracle.
    /// Prints no wallet address, password, seed, RPC payload or private paths.
    /// </summary>
    internal static class WalletRpcSessionAcceptance
    {
        const string RpcUrl = "http://127.0.0.1:39484/json_rpc";
        static readonly JavaScriptSerializer Json = new JavaScriptSerializer();

        static void Check(bool check, string category)
        {
            if (!check) throw new InvalidOperationException("Native QA failed: " + category);
        }

        static IDictionary Call(WalletRpcSession session, string method,
                                IDictionary<string, object> parameters,
                                int timeout = 15000)
        {
            var request = new Dictionary<string, object> {
                { "jsonrpc", "2.0" }, { "id", "wallet-qa" },
                { "method", method }, { "params", parameters }
            };
            string data = session.PostJson(RpcUrl, Json.Serialize(request), timeout);
            var decoded = Json.DeserializeObject(data) as IDictionary;
            Check(decoded != null, "invalid response");
            if (decoded.Contains("error"))
                throw new InvalidOperationException("Native QA rejected RPC operation");
            return decoded.Contains("result") ? decoded["result"] as IDictionary : decoded;
        }

        static IDictionary Params(params object[] values)
        {
            var answer = new Dictionary<string, object>();
            for (int i = 0; i < values.Length; i += 2)
                answer.Add((string)values[i], values[i + 1]);
            return answer;
        }

        static string Address(WalletRpcSession session)
        {
            IDictionary r = Call(session, "get_address", Params("account_index", 0));
            string address = Convert.ToString(r["address"]);
            Check(FrgWalletInput.LooksLikePublicAddress(address),
                  "wallet returned invalid public address");
            return address;
        }

        static void ProbeReady(WalletRpcSession session, Process process)
        {
            for (int i = 0; i < 35; i++)
            {
                Check(process != null && !process.HasExited, "native wallet service exited");
                try {
                    IDictionary result = Call(session, "get_version", Params(), 1200);
                    if (result != null)
                    {
                        session.DeleteStartupConfig();
                        return;
                    }
                } catch (Exception) { }
                Thread.Sleep(175);
            }
            throw new InvalidOperationException("Native wallet authenticated readiness timeout");
        }

        static Process Launch(string exe, string walletDirectory,
                              string localDirectory, WalletRpcSession session)
        {
            var args = new StringBuilder();
            args.Append("--wallet-dir \"").Append(walletDirectory).Append("\"");
            args.Append(" --rpc-bind-ip 127.0.0.1 --rpc-bind-port 39484");
            args.Append(" --daemon-address 127.0.0.1:49574");
            args.Append(" --config-file \"").Append(session.ConfigFile).Append("\"");
            args.Append(" --no-dns --no-initial-sync --log-level 0");
            args.Append(" --log-file \"").Append(Path.Combine(localDirectory, "wallet.log")).Append("\"");
            var info = new ProcessStartInfo(exe, args.ToString()) {
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = localDirectory,
                RedirectStandardInput = false,
                RedirectStandardOutput = false,
                RedirectStandardError = false
            };
            return Process.Start(info);
        }

        static void Stop(Process process)
        {
            if (process == null) return;
            try {
                if (!process.HasExited) {
                    process.Kill();
                    process.WaitForExit(5000);
                }
            } catch { }
            process.Dispose();
        }

        static string RandomToken()
        {
            var bytes = new byte[32];
            using (RandomNumberGenerator rng = RandomNumberGenerator.Create())
                rng.GetBytes(bytes);
            string token = Convert.ToBase64String(bytes);
            Array.Clear(bytes, 0, bytes.Length);
            return token;
        }

        public static int Main(string[] args)
        {
            string directory = null;
            Process process = null;
            WalletRpcSession session = null;
            try
            {
                Check(args.Length == 1 && File.Exists(args[0]), "missing candidate binary");
                using (var listener = new TcpListener(IPAddress.Loopback, 39484)) {
                    listener.Start(); // Never kill or attach to an existing user's wallet RPC
                    listener.Stop();
                }
                directory = Path.Combine(Path.GetTempPath(),
                    "frg-disposable-authenticated-qa-" + Guid.NewGuid().ToString("N"));
                Directory.CreateDirectory(directory);
                string wallets = Path.Combine(directory, "wallets");
                Directory.CreateDirectory(wallets);
                string password = RandomToken();
                session = WalletRpcSession.Create(Path.Combine(directory, "auth"));
                process = Launch(args[0], wallets, directory, session);
                ProbeReady(session, process);
                Console.WriteLine("PASS: private native wallet started with user-only credential file and authenticated Digest");

                Call(session, "create_wallet", Params(
                    "filename", "disposable_original", "password", password,
                    "language", "English"), 15000);
                string created = Address(session);
                IDictionary result = Call(session, "query_key", Params("key_type", "mnemonic"));
                string words = Convert.ToString(result["key"]);
                Check(!String.IsNullOrWhiteSpace(words) &&
                      words.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries).Length == 25,
                      "wrong recovery phrase format");
                Call(session, "close_wallet", Params());
                Console.WriteLine("PASS: authenticated native wallet created a disposable 25-word FRG wallet");

                IDictionary restored = Call(session, "restore_deterministic_wallet",
                    Params("filename", "disposable_restored", "password", password,
                           "seed", words, "restore_height", 0, "language", "English"), 30000);
                words = null;
                Check(Convert.ToString(restored["address"]) == created,
                      "recovery address mismatch");
                Check(Address(session) == created, "opened restored wallet mismatch");
                Call(session, "close_wallet", Params());
                Console.WriteLine("PASS: native 25-word wallet recovery preserved the same public address");

                bool wrongPasswordRejected = false;
                try {
                    Call(session, "open_wallet", Params("filename", "disposable_restored",
                                                     "password", "disposable-intentionally-wrong"),
                         10000);
                } catch (InvalidOperationException) {
                    wrongPasswordRejected = true;
                }
                Check(wrongPasswordRejected, "wrong wallet password accepted");
                Call(session, "open_wallet", Params(
                    "filename", "disposable_restored", "password", password));
                Check(Address(session) == created, "wallet disk reopen mismatch");
                Call(session, "close_wallet", Params());

                Stop(process); process = null;
                session.Dispose(); session = null;
                session = WalletRpcSession.Create(Path.Combine(directory, "auth"));
                process = Launch(args[0], wallets, directory, session);
                ProbeReady(session, process);
                Call(session, "open_wallet", Params(
                    "filename", "disposable_restored", "password", password));
                Check(Address(session) == created, "native wallet RPC restart mismatch");
                Call(session, "close_wallet", Params());
                Console.WriteLine("PASS: wrong password rejected, disk reopen and native service restart succeeded");
                Console.WriteLine("PASS: no peers, no daemon, no mining, no transfer, no Oracle or user wallet used");
                return 0;
            }
            catch
            {
                // Deliberately never print exception text, wallet data or paths.
                Console.Error.WriteLine("FAIL: authenticated native wallet lifecycle QA did not pass");
                return 1;
            }
            finally
            {
                Stop(process);
                if (session != null) session.Dispose();
                if (directory != null && Directory.Exists(directory)) {
                    try { Directory.Delete(directory, true); } catch { }
                }
            }
        }
    }
}
