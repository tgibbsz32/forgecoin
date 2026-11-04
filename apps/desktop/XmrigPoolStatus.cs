using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;

namespace ForgeCoinDesktop
{
    // XMRig's *local* API is process telemetry, NOT proof of FRG shares.
    // A live process or responding API alone must never show "Mining".
    internal sealed class XmrigPoolSnapshot
    {
        internal readonly string Phase;
        internal readonly string ReportedPool;
        internal readonly string Algorithm;
        internal readonly double Hashrate;
        internal readonly double Difficulty;
        internal readonly long AcceptedShares;
        internal readonly long RejectedShares;
        internal readonly long ConnectionSeconds;
        internal readonly long PingMs;
        internal readonly string ApiId;

        internal XmrigPoolSnapshot(string phase, string pool, string algorithm,
                                  double hashrate, double difficulty, long accepted,
                                  long rejected, long seconds, long ping, string apiId)
        {
            Phase = phase;
            ReportedPool = pool;
            Algorithm = algorithm;
            Hashrate = hashrate;
            Difficulty = difficulty;
            AcceptedShares = accepted;
            RejectedShares = rejected;
            ConnectionSeconds = seconds;
            PingMs = ping;
            ApiId = apiId;
        }
    }

    internal static class XmrigPoolStatus
    {
        private static string Text(IDictionary obj, string key)
        {
            if (obj == null || !obj.Contains(key) || obj[key] == null)
                return "";
            return Convert.ToString(obj[key], CultureInfo.InvariantCulture).Trim();
        }

        private static long Counter(IDictionary obj, string key)
        {
            if (obj == null || !obj.Contains(key) || obj[key] == null) return 0;
            long value = Convert.ToInt64(obj[key], CultureInfo.InvariantCulture);
            if (value < 0) throw new ArgumentException("Negative XMRig API counter.");
            return value;
        }

        private static double Value(IDictionary obj, string key)
        {
            if (obj == null || !obj.Contains(key) || obj[key] == null) return 0;
            double value = Convert.ToDouble(obj[key], CultureInfo.InvariantCulture);
            if (Double.IsNaN(value) || Double.IsInfinity(value) || value < 0)
                throw new ArgumentException("Invalid XMRig API telemetry.");
            return value;
        }

        private static double FirstRate(IDictionary summary)
        {
            IDictionary hashrate = summary == null ? null : summary["hashrate"] as IDictionary;
            if (hashrate == null || !hashrate.Contains("total"))
                return 0;
            IEnumerable total = hashrate["total"] as IEnumerable;
            if (total == null || total is string) return 0;
            foreach (object first in total)
            {
                if (first == null) return 0;
                double speed = Convert.ToDouble(first, CultureInfo.InvariantCulture);
                if (Double.IsNaN(speed) || Double.IsInfinity(speed) || speed < 0)
                    throw new ArgumentException("Invalid XMRig rate.");
                return speed;
            }
            return 0;
        }

        private static string NormalizePool(string input)
        {
            if (String.IsNullOrWhiteSpace(input)) return "";
            string pool = input.Trim();
            foreach (string prefix in new string[] {
                "stratum+tcp://", "stratum+ssl://", "stratum+tls://"
            })
            {
                if (pool.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                    pool = pool.Substring(prefix.Length);
            }
            return pool.TrimEnd('/').ToLowerInvariant();
        }

        /// <summary>
        /// Map XMRig /2/summary without treating a process, local API or
        /// unrelated donation pool as successful FRG pool mining. Actual
        /// acceptance must come from independent native Stratum/share tests.
        /// </summary>
        internal static XmrigPoolSnapshot Parse(IDictionary summary,
                                                string requestedPool,
                                                string expectedApiId)
        {
            if (summary == null)
                throw new ArgumentException("XMRig summary was absent.");
            string actualId = Text(summary, "id");
            // XMRig's --api-id is limited to 31 visible characters in
            // the native 6.22 API. A longer synthetic ID can falsely pass
            // unit tests even though the real miner truncates it.
            if (String.IsNullOrEmpty(expectedApiId) ||
                expectedApiId.Length > 31 || actualId.Length > 31 ||
                !String.Equals(actualId, expectedApiId,
                               StringComparison.Ordinal))
                throw new ArgumentException("XMRig API instance identity mismatch.");

            IDictionary connection = summary["connection"] as IDictionary;
            IDictionary results = summary["results"] as IDictionary;
            double speed = FirstRate(summary);
            long good = Counter(results, "shares_good");
            long total = Counter(results, "shares_total");
            if (good > total)
                throw new ArgumentException("Inconsistent XMRig share counters.");
            string actualPool = Text(connection, "pool");
            string expectedPool = NormalizePool(requestedPool);
            string reportedPool = NormalizePool(actualPool);
            long connectionSeconds = Counter(connection, "uptime");
            string algorithm = Text(connection, "algo");
            if (algorithm.Length == 0) algorithm = Text(summary, "algo");
            double difficulty = Value(results, "diff_current");
            long ping = Counter(connection, "ping");
            bool paused = summary.Contains("paused") &&
                summary["paused"] != null &&
                Convert.ToBoolean(summary["paused"], CultureInfo.InvariantCulture);
            string phase;
            if (paused)
                phase = "Paused";
            else if (reportedPool.Length > 0 && reportedPool != expectedPool)
                phase = "Other pool";
            else if (reportedPool.Length == 0 || connectionSeconds == 0)
                phase = "Connecting";
            else if (speed == 0 || !String.Equals(algorithm, "rx/0",
                                                StringComparison.OrdinalIgnoreCase))
                phase = "Connected";
            else
                phase = "Hashing";

            return new XmrigPoolSnapshot(
                phase, actualPool, algorithm, speed, difficulty,
                good, total - good, connectionSeconds, ping, actualId);
        }
    }
}
