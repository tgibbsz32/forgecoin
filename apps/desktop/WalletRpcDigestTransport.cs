using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace ForgeCoinDesktop
{
    // Strict loopback-only HTTP Digest for native FRG wallet RPC.
    // Probe with harmless get_version BEFORE sending any real RPC parameters:
    // secrets are never disclosed to an unprotected listener or on a 401.
    internal static class WalletRpcDigestTransport
    {
        private const int MaxBytes = 512 * 1024;
        private const string Probe = "{\"jsonrpc\":\"2.0\",\"id\":\"auth\",\"method\":\"get_version\",\"params\":{}}";
        private static readonly Regex Parameter = new Regex(
            @"(?<key>[A-Za-z0-9_-]+)\s*=\s*(?:""(?<val>[^""]*)""|(?<val>[^,\s]+))",
            RegexOptions.CultureInvariant);

        private static void Check(bool condition)
        {
            if (!condition) throw new InvalidOperationException("FRG wallet RPC authentication failed.");
        }

        private static HttpWebRequest Make(Uri url, byte[] body, int timeout, string auth)
        {
            Check(url != null && url.Scheme == "http" && url.Host == "127.0.0.1"
                  && url.AbsolutePath == "/json_rpc" && url.Query == ""
                  && url.Fragment == "" && url.Port >= 1024
                  && timeout >= 500 && timeout <= 120000
                  && body != null && body.Length <= MaxBytes);
            var req = (HttpWebRequest)WebRequest.Create(url);
            req.Method = "POST";
            req.ContentType = "application/json";
            req.ContentLength = body.Length;
            req.Timeout = timeout;
            req.ReadWriteTimeout = timeout;
            req.Proxy = null;
            req.AllowAutoRedirect = false;
            req.KeepAlive = false;
            req.ServicePoint.Expect100Continue = false;
            if (auth != null) req.Headers[HttpRequestHeader.Authorization] = auth;
            return req;
        }

        private static HttpWebResponse Send(HttpWebRequest req, byte[] body)
        {
            using (var stream = req.GetRequestStream())
                stream.Write(body, 0, body.Length);
            return (HttpWebResponse)req.GetResponse();
        }

        private static string Md5(string value)
        {
            using (MD5 md5 = MD5.Create())
                return BitConverter.ToString(md5.ComputeHash(Encoding.UTF8.GetBytes(value)))
                    .Replace("-", "").ToLowerInvariant();
        }

        private static string Digest(string challenge, string username,
                                     string password, string path)
        {
            Check(!String.IsNullOrEmpty(challenge) &&
                  challenge.StartsWith("Digest ", StringComparison.OrdinalIgnoreCase)
                  && challenge.Length < 2048 && username.Length <= 80
                  && password.Length <= 256);
            var fields = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (Match m in Parameter.Matches(challenge.Substring(7)))
            {
                string key = m.Groups["key"].Value;
                Check(!fields.ContainsKey(key));
                fields.Add(key, m.Groups["val"].Value);
            }
            Check(fields.ContainsKey("realm") && fields.ContainsKey("nonce")
                  && fields.ContainsKey("qop"));
            string realm = fields["realm"], nonce = fields["nonce"];
            string algorithm = fields.ContainsKey("algorithm") ?
                fields["algorithm"] : "MD5";
            Check(algorithm == "MD5" || algorithm == "MD5-sess");
            bool qopAuth = false;
            foreach (string part in fields["qop"].Split(','))
                if (part.Trim() == "auth") qopAuth = true;
            Check(qopAuth);
            foreach (string part in new string[] {realm, nonce, username})
            {
                Check(!String.IsNullOrEmpty(part) && part.Length < 512 &&
                      part.IndexOfAny(new char[] {'\r', '\n', '"', '\\'}) < 0);
            }
            byte[] random = new byte[16];
            using (var rng = RandomNumberGenerator.Create()) rng.GetBytes(random);
            string cnonce = BitConverter.ToString(random).Replace("-", "").ToLowerInvariant();
            Array.Clear(random, 0, random.Length);
            string ha1 = Md5(username + ":" + realm + ":" + password);
            if (algorithm == "MD5-sess")
                ha1 = Md5(ha1 + ":" + nonce + ":" + cnonce);
            string ha2 = Md5("POST:" + path);
            string response = Md5(ha1 + ":" + nonce +
                                  ":00000001:" + cnonce + ":auth:" + ha2);
            string authorization = "Digest username=\"" + username +
                "\", realm=\"" + realm + "\", nonce=\"" + nonce +
                "\", uri=\"" + path + "\", response=\"" + response +
                "\", algorithm=" + algorithm + ", qop=auth, nc=00000001, cnonce=\"" +
                cnonce + "\"";
            if (fields.ContainsKey("opaque"))
            {
                string opaque = fields["opaque"];
                Check(opaque.IndexOfAny(new char[] {'\r', '\n', '"', '\\'}) < 0);
                authorization += ", opaque=\"" + opaque + "\"";
            }
            return authorization;
        }

        public static string PostJson(Uri url, string username, string password,
                                      string json, int timeout)
        {
            Check(url != null && !String.IsNullOrEmpty(username) &&
                  !String.IsNullOrEmpty(password) && json != null);
            byte[] first = Encoding.UTF8.GetBytes(Probe);
            string challenge;
            try
            {
                using (HttpWebResponse response = Send(Make(url, first, timeout, null), first))
                    throw new InvalidOperationException("Unauthenticated wallet RPC is not allowed.");
            }
            catch (WebException e)
            {
                var response = e.Response as HttpWebResponse;
                if (response == null)
                    throw new InvalidOperationException("Native wallet RPC unavailable.");
                using (response)
                {
                    Check(response.StatusCode == HttpStatusCode.Unauthorized);
                    challenge = response.Headers[HttpResponseHeader.WwwAuthenticate];
                }
            }
            string header = Digest(challenge, username, password, url.PathAndQuery);
            byte[] payload = Encoding.UTF8.GetBytes(json);
            try
            {
                using (var response = Send(Make(url, payload, timeout, header), payload))
                using (var stream = response.GetResponseStream())
                using (var output = new MemoryStream())
                {
                    Check(response.StatusCode == HttpStatusCode.OK);
                    byte[] chunk = new byte[8192];
                    int n;
                    while ((n = stream.Read(chunk, 0, chunk.Length)) > 0)
                    {
                        Check(output.Length + n <= MaxBytes);
                        output.Write(chunk, 0, n);
                    }
                    return Encoding.UTF8.GetString(output.ToArray());
                }
            }
            catch (WebException)
            {
                throw new InvalidOperationException("Native wallet RPC outcome is unverified.");
            }
        }
    }
}
