using System;
using System.IO;
using System.Net;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;

namespace ForgeCoinDesktop
{
    /// <summary>
    /// Ephemeral, local-only native wallet RPC HTTP-Digest credentials.
    ///
    /// The private auth config is accessible to the current Windows user only
    /// and deleted immediately after the wallet responds with valid Digest.
    /// No credentials appear in the daemon/wallet command line, application
    /// settings, GUI logs, exception messages or the distributable package.
    /// Authenticated loopback transport is necessary but is not sufficient to
    /// certify a funded production wallet (same-user hostile processes and
    /// installer provenance must still be assessed).
    /// </summary>
    internal sealed class WalletRpcSession : IDisposable
    {
        private readonly string user;
        private string password;
        private string configPath;
        private bool disposed;

        private WalletRpcSession(string user, string password, string configPath)
        {
            this.user = user;
            this.password = password;
            this.configPath = configPath;
        }

        private static string RandomHex(int count)
        {
            byte[] bytes = new byte[count];
            try
            {
                using (RandomNumberGenerator rng = RandomNumberGenerator.Create())
                    rng.GetBytes(bytes);
                return BitConverter.ToString(bytes).Replace("-", "").ToLowerInvariant();
            }
            finally { Array.Clear(bytes, 0, bytes.Length); }
        }

        public static WalletRpcSession Create(string runtimeDirectory)
        {
            Directory.CreateDirectory(runtimeDirectory);
            string login = "frg" + RandomHex(8);
            string secret = RandomHex(32);
            string file = Path.Combine(runtimeDirectory, "wallet-rpc-" + RandomHex(12) + ".conf");
            FileSecurity security = new FileSecurity();
            security.SetAccessRuleProtection(true, false);
            SecurityIdentifier sid = WindowsIdentity.GetCurrent().User;
            if (sid == null) throw new InvalidOperationException("Windows user identity unavailable.");
            security.SetOwner(sid);
            security.AddAccessRule(new FileSystemAccessRule(sid,
                FileSystemRights.FullControl, AccessControlType.Allow));
            try
            {
                using (FileStream output = new FileStream(
                    file, FileMode.CreateNew, FileSystemRights.Write,
                    FileShare.None, 4096, FileOptions.None, security))
                using (StreamWriter writer = new StreamWriter(output, new UTF8Encoding(false)))
                {
                    writer.Write("rpc-login=");
                    writer.Write(login);
                    writer.Write(":");
                    writer.Write(secret);
                    writer.Write("\n");
                }
                return new WalletRpcSession(login, secret, file);
            }
            catch
            {
                try { File.Delete(file); } catch { }
                throw new InvalidOperationException("Could not prepare a private native wallet RPC authentication file.");
            }
        }

        public string ConfigFile
        {
            get
            {
                if (disposed || String.IsNullOrEmpty(configPath))
                    throw new InvalidOperationException("Wallet RPC configuration is unavailable.");
                return configPath;
            }
        }

        public void Authenticate(HttpWebRequest request)
        {
            if (disposed || password == null)
                throw new InvalidOperationException("Wallet RPC authentication has ended.");
            if (request == null || request.RequestUri == null ||
                !String.Equals(request.RequestUri.Host, "127.0.0.1", StringComparison.Ordinal) ||
                request.RequestUri.Port != 39484 ||
                !String.Equals(request.RequestUri.Scheme, "http", StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Wallet authentication may only reach the local wallet RPC endpoint.");
            request.Credentials = new NetworkCredential(user, password);
            request.PreAuthenticate = true;
            request.AllowAutoRedirect = false;
            request.Proxy = null;
        }

        public void DeleteStartupConfig()
        {
            if (disposed || String.IsNullOrEmpty(configPath)) return;
            File.Delete(configPath);  // failure is fatal: do not leave credentials at rest
            configPath = null;
        }

        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            if (!String.IsNullOrEmpty(configPath))
                try { File.Delete(configPath); } catch { }
            configPath = null;
            password = null;
        }
    }
}
