using System;
using System.Collections;
using System.Collections.Generic;

namespace ForgeCoinDesktop
{
    internal static class XmrigPoolStatusTests
    {
        private static int checks;
        private static void Check(bool ok, string message)
        {
            checks++;
            if (!ok) throw new Exception("XMRig telemetry QA: " + message);
        }

        private static IDictionary Build(string pool, long uptime, double speed,
                                         long good, long total, bool paused,
                                         string algo = "rx/0", string id = "private-qa-instance")
        {
            return new Dictionary<string, object> {
                { "id", id }, { "kind", "miner" }, { "version", "6.26.0" },
                { "paused", paused },
                { "algo", algo },
                { "hashrate", new Dictionary<string, object> {
                    { "total", new object[] { speed, null, null } }
                }},
                { "results", new Dictionary<string, object> {
                    { "diff_current", 1000L }, { "shares_good", good },
                    { "shares_total", total }
                }},
                { "connection", new Dictionary<string, object> {
                    { "pool", pool }, { "uptime", uptime },
                    { "ping", 14L }, { "algo", algo }
                }}
            };
        }

        private static XmrigPoolSnapshot Read(IDictionary summary)
        {
            return XmrigPoolStatus.Parse(
                summary, "127.0.0.1:49690", "private-qa-instance");
        }

        private static void Reject(IDictionary data, string reason)
        {
            bool rejected = false;
            try { Read(data); }
            catch (ArgumentException) { rejected = true; }
            Check(rejected, reason);
        }

        public static int Main()
        {
            var notConnected = Read(Build("", 0, 0, 0, 0, false));
            Check(notConnected.Phase == "Connecting",
                  "live API without pool cannot be called Mining");
            Check(notConnected.AcceptedShares == 0 && notConnected.Hashrate == 0,
                  "unconnected miner reports zero accepted shares");
            var pending = Read(Build("127.0.0.1:49690", 13, 0, 0, 0, false));
            Check(pending.Phase == "Connected",
                  "connected but idle miner cannot be called Mining");
            var warmup = Read(Build("127.0.0.1:49690", 0, 12, 0, 0, false));
            Check(warmup.Phase == "Connecting",
                  "nonzero speed without connected uptime is not pool accepted");
            var actual = Read(Build("127.0.0.1:49690", 15, 128.4, 5, 7, false));
            Check(actual.Phase == "Hashing", "real expected-pool hashrate");
            Check(actual.Hashrate == 128.4, "native speed copied exactly");
            Check(actual.AcceptedShares == 5 && actual.RejectedShares == 2,
                  "good and bad share counters are not conflated");
            Check(actual.PingMs == 14 && actual.Difficulty == 1000.0,
                  "connection ping and native pool job difficulty");
            Check(actual.ConnectionSeconds == 15,
                  "connection uptime");
            var foreign = Read(Build("unrelated-pool.example:3333",
                                     100, 500, 100, 104, false));
            Check(foreign.Phase == "Other pool",
                  "other or donation pool must not show FRG Mining");
            var paused = Read(Build("127.0.0.1:49690", 30, 150, 4, 4, true));
            Check(paused.Phase == "Paused",
                  "XMRig paused status overrides cached hashrate");
            var wrongAlgo = Read(Build("127.0.0.1:49690", 30, 150, 4, 4, false, "cn/1"));
            Check(wrongAlgo.Phase == "Connected",
                  "non-RandomX algorithm must not show FRG Hashing");
            var prefix = XmrigPoolStatus.Parse(
                Build("127.0.0.1:49690", 30, 50, 1, 1, false),
                "stratum+tcp://127.0.0.1:49690", "private-qa-instance");
            Check(prefix.Phase == "Hashing", "Stratum scheme normalization");
            Reject(Build("127.0.0.1:49690", 30, -2, 1, 1, false),
                   "negative hashrate must fail closed");
            Reject(Build("127.0.0.1:49690", 30, 50, 5, 4, false),
                   "good shares cannot exceed total shares");
            Reject(Build("127.0.0.1:49690", 30, 50, 1, 1, false,
                         "rx/0", "other-process"),
                   "API identity must not be confused with another process");
            var empty = new Dictionary<string, object> { { "id", "private-qa-instance" } };
            Check(Read(empty).Phase == "Connecting",
                  "missing connection must not be labeled Mining");
            Console.WriteLine("PASS: " + checks +
                " XMRig 6.26 API state, wrong-pool, spoofed identity and share-count checks");
            return 0;
        }
    }
}
