using System;
using System.IO;
using System.Net;
using System.Text;

namespace ForgeCoinDesktop
{
    // Executable acceptance probe: launch separately against an isolated
    // Windows native wallet RPC with disposable credentials. No wallet keys.
    // Arguments: <loopback port> ; disposable credentials via env only
    internal static class WalletRpcDigestProbe
    {
        static int GetVersionCode(int port, string user, string password)
        {
            var url = "http://127.0.0.1:" + port + "/json_rpc";
            if (user != null)
            {
                try
                {
                    string result = WalletRpcDigestTransport.PostJson(
                        new Uri(url), user, password,
                        "{\"jsonrpc\":\"2.0\",\"id\":\"real-native-qa\",\"method\":\"get_version\",\"params\":{}}",
                        5000);
                    return result.Contains("\"result\"") && result.Contains("\"version\"") ? 200 : 500;
                }
                catch (InvalidOperationException error) { Console.Error.WriteLine("AUTH_RESULT_CATEGORY=" + (error.Message == "Native wallet RPC outcome is unverified." ? "rejected-after-challenge" : error.Message == "FRG wallet RPC authentication failed." ? "challenge-validation-failed" : error.Message == "Native wallet RPC unavailable." ? "no-server" : "invalid-response")); return 401; }
            }
            var request = (HttpWebRequest)WebRequest.Create(url);
            request.Method = "POST";
            request.ContentType = "application/json";
            request.AllowAutoRedirect = false;
            request.Proxy = null;
            request.Timeout = 5000;
            request.ReadWriteTimeout = 5000;
            request.KeepAlive = false;
            request.ServicePoint.Expect100Continue = false; // Native epee HTTP server cannot handle 100-continue Digest handshake
            if (user != null)
            {
                request.Credentials = new NetworkCredential(user, password);
                request.PreAuthenticate = true;
            }
            var body = Encoding.UTF8.GetBytes(
                "{\"jsonrpc\":\"2.0\",\"id\":\"local-qa\",\"method\":\"get_version\",\"params\":{}}");
            request.ContentLength = body.Length;
            try
            {
                using (var stream = request.GetRequestStream())
                    stream.Write(body, 0, body.Length);
                using (var response = (HttpWebResponse)request.GetResponse())
                {
                    if (response.StatusCode != HttpStatusCode.OK)
                        return (int)response.StatusCode;
                    using (var reader = new StreamReader(response.GetResponseStream()))
                    {
                        var result = reader.ReadToEnd();
                        if (!result.Contains("\"result\"") ||
                            !result.Contains("\"version\""))
                            throw new InvalidOperationException("No valid RPC version result");
                    }
                    return 200;
                }
            }
            catch (WebException e)
            {
                var response = e.Response as HttpWebResponse;
                if (response == null)
                {
                    Console.Error.WriteLine("SAFE_DIAG: RPC connection failure category " +
                                            e.Status);
                    throw;
                }
                try { return (int)response.StatusCode; }
                finally { response.Dispose(); }
            }
        }

        public static int Main(string[] args)
        {
            try
            {
                int port;
                if (args.Length != 1 ||
                    !Int32.TryParse(args[0], out port) ||
                    port < 1024 || port > 65535)
                    throw new InvalidOperationException("Expected private test port and credentials");
                string username = Environment.GetEnvironmentVariable("FRG_QA_RPC_USER");
                string password = Environment.GetEnvironmentVariable("FRG_QA_RPC_SECRET");
                if (String.IsNullOrEmpty(username) || String.IsNullOrEmpty(password))
                    throw new InvalidOperationException("Missing disposable QA credentials");
                int noCredentials = GetVersionCode(port, null, null);
                Console.WriteLine("SAFE_STAGE_NOAUTH_HTTP=" + noCredentials);
                int wrongCredentials = GetVersionCode(port, username, password + "incorrect");
                Console.WriteLine("SAFE_STAGE_WRONG_HTTP=" + wrongCredentials);
                int correctCredentials = GetVersionCode(port, username, password);
                Console.WriteLine("NATIVE_NO_AUTH_HTTP=" + noCredentials);
                Console.WriteLine("NATIVE_WRONG_AUTH_HTTP=" + wrongCredentials);
                Console.WriteLine("NATIVE_DOTNET_DIGEST_HTTP=" + correctCredentials);
                if (noCredentials != 401 || wrongCredentials != 401 ||
                    correctCredentials != 200)
                    return 1;
                Console.WriteLine("PASS: .NET HttpWebRequest authenticated native Windows wallet RPC via HTTP Digest");
                return 0;
            }
            catch (Exception error)
            {
                // Intentionally no exception messages, RPC output, secret or
                // process arguments in logs. Type name only.
                Console.Error.WriteLine("SAFE_DIAG_EXCEPTION=" + error.GetType().Name);
                Console.Error.WriteLine("FAIL: .NET native wallet Digest QA did not pass");
                return 2;
            }
        }
    }
}
