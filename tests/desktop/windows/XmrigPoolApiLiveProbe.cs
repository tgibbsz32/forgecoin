using System;
using System.Collections;
using System.IO;
using System.Net;
using System.Text;
using System.Web.Script.Serialization;

namespace ForgeCoinDesktop
{
    /// <summary>
    /// Genuine XMRig 6.26 localhost API test, using a deliberately unreachable
    /// local Stratum endpoint. No external pool, wallet, hash generation or
    /// share submission is authorized. Called only with a verified official
    /// executable in an independent disposable test process.
    /// </summary>
    internal static class XmrigPoolApiLiveProbe
    {
        public static int Main(string[] args)
        {
            try
            {
                int port;
                if (args.Length != 3 || !Int32.TryParse(args[0], out port) ||
                    port < 1024 || port > 65535)
                    throw new ArgumentException("Bad private API test parameters");

                Uri uri = new Uri("http://127.0.0.1:" + port + "/2/summary");
                var req = (HttpWebRequest)WebRequest.Create(uri);
                req.Method = "GET";
                req.Proxy = null;
                req.AllowAutoRedirect = false;
                req.Timeout = 5000;
                req.ReadWriteTimeout = 5000;
                string json;
                using (var response = (HttpWebResponse)req.GetResponse())
                using (var stream = new StreamReader(response.GetResponseStream()))
                {
                    if (response.StatusCode != HttpStatusCode.OK)
                        throw new InvalidOperationException("No local XMRig API");
                    json = stream.ReadToEnd();
                    if (json.Length > 500000)
                        throw new InvalidOperationException("XMRig response too large");
                }
                IDictionary summary =
                    new JavaScriptSerializer().DeserializeObject(json) as IDictionary;
                XmrigPoolSnapshot snapshot = XmrigPoolStatus.Parse(
                    summary, args[2], args[1]);
                if (snapshot.Phase != "Connecting" ||
                    snapshot.AcceptedShares != 0 ||
                    snapshot.RejectedShares != 0 ||
                    snapshot.Hashrate != 0 ||
                    snapshot.ReportedPool.Length != 0)
                    throw new InvalidOperationException(
                        "Unconnected XMRig was incorrectly reported as FRG pool mining");

                bool spoofedRejected = false;
                try { XmrigPoolStatus.Parse(summary, args[2], args[1] + "other"); }
                catch (ArgumentException) { spoofedRejected = true; }
                if (!spoofedRejected)
                    throw new InvalidOperationException(
                        "Wrong XMRig API instance was not rejected");
                Console.WriteLine("PASS: real official XMRig localhost API with 0 shares, " +
                    "0 hashrate and no connected pool is CONNECTING, never MINING");
                Console.WriteLine("PASS: unrelated/spoofed API instance ID rejected");
                return 0;
            }
            catch (Exception failure)
            {
                // Never echo attacker-provided JSON, pool credentials,
                // process arguments, or identifiers.
                Console.Error.WriteLine("FAIL: private XMRig API state check: " +
                                        failure.GetType().Name);
                return 1;
            }
        }
    }
}
