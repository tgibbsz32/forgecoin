using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;

namespace ForgeCoinDesktop
{
    // Separate Solana wallet: private keys are encrypted locally and never sent to RPC.
    // Native FRG wallet, chain, mining permissions and release gates are untouched.
    internal sealed partial class MainForm
    {
        private TextBox solWalletNameBox;
        private TextBox solPasswordBox;
        private TextBox solConfirmPasswordBox;
        private TextBox solAddressBox;
        private Label solWalletState;
        private Label solBalanceLabel;
        private Label solMfrgBalanceLabel;
        private Label solNetworkStatusLabel;
        private ComboBox solNetworkSelector;
        private string solCurrentWalletPath;
        private string solCurrentAddress;
        private int solRefreshInFlight;
        private DateTime solLastRefreshUtc = DateTime.MinValue;
        private const string DevnetMint = "9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw";
        private const string SolanaProgramId = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";

        private string SolanaVaultRoot()
        {
#if DEBUG
            // QA-only isolation. This override is absent from release builds.
            string qa = Environment.GetEnvironmentVariable("FORGECOIN_SOLANA_QA_ROOT");
            if (!String.IsNullOrWhiteSpace(qa)) return qa;
#endif
            return Path.Combine(appRoot, "solana", "wallets");
        }

        private TabPage BuildSolanaTab()
        {
            TabPage page = new TabPage("Solana / mFRG");
            TableLayoutPanel root = new TableLayoutPanel {
                Dock = DockStyle.Fill, Padding = new Padding(20), ColumnCount = 1, RowCount = 7
            };
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 64));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 111));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 66));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 89));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 115));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 60));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

            Label notice = new Label {
                Dock = DockStyle.Fill, ForeColor = Color.FromArgb(95, 77, 37),
                Text = "Solana is a public blockchain and is separate from native private FRG. " +
                       "No verified mFRG Solana mainnet mint is configured in this application. " +
                       "Creating a Solana wallet does not create or convert native FRG."
            };
            root.Controls.Add(notice, 0, 0);

            GroupBox vaultGroup = new GroupBox { Text = "Local encrypted Solana wallet", Dock = DockStyle.Fill };
            TableLayoutPanel inputs = new TableLayoutPanel { Dock = DockStyle.Fill,
                Padding = new Padding(7), ColumnCount = 6, RowCount = 2 };
            inputs.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 72));
            inputs.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 32));
            inputs.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 95));
            inputs.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 36));
            inputs.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 98));
            inputs.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 32));
            inputs.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
            inputs.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
            inputs.Controls.Add(new Label { Text = "Wallet", Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft }, 0, 0);
            solWalletNameBox = new TextBox { Dock = DockStyle.Fill, Text = "solana-wallet" };
            inputs.Controls.Add(solWalletNameBox, 1, 0);
            inputs.Controls.Add(new Label { Text = "Password", Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft }, 2, 0);
            solPasswordBox = new TextBox { Dock = DockStyle.Fill, UseSystemPasswordChar = true };
            inputs.Controls.Add(solPasswordBox, 3, 0);
            inputs.Controls.Add(new Label { Text = "Confirm", Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft }, 4, 0);
            solConfirmPasswordBox = new TextBox { Dock = DockStyle.Fill, UseSystemPasswordChar = true };
            inputs.Controls.Add(solConfirmPasswordBox, 5, 0);
            solWalletState = new Label { Text = "Locked. An encrypted backup is required to recover funds.",
                Dock = DockStyle.Fill, ForeColor = Color.DimGray, AutoEllipsis = true };
            inputs.Controls.Add(solWalletState, 0, 1);
            inputs.SetColumnSpan(solWalletState, 6);
            vaultGroup.Controls.Add(inputs);
            root.Controls.Add(vaultGroup, 0, 1);

            FlowLayoutPanel actions = new FlowLayoutPanel { Dock = DockStyle.Fill,
                WrapContents = true, AutoScroll = true };
            actions.Controls.Add(PrimaryButton("Create Solana wallet", SolanaCreate));
            actions.Controls.Add(SecondaryButton("Open", SolanaOpen));
            actions.Controls.Add(SecondaryButton("Import keypair", SolanaImportKeypair));
            actions.Controls.Add(SecondaryButton("Restore backup", SolanaRestoreBackup));
            actions.Controls.Add(SecondaryButton("Backup vault", SolanaExportBackup));
            actions.Controls.Add(SecondaryButton("Recovery phrase", SolanaShowRecovery));
            actions.Controls.Add(SecondaryButton("Lock", SolanaLockClick));
            root.Controls.Add(actions, 0, 2);

            GroupBox receive = new GroupBox { Text = "Solana public address", Dock = DockStyle.Fill };
            TableLayoutPanel addressPanel = new TableLayoutPanel {
                ColumnCount = 2, RowCount = 1, Dock = DockStyle.Fill
            };
            addressPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            addressPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 135));
            solAddressBox = new TextBox { Dock = DockStyle.Fill, ReadOnly = true,
                Multiline = true, Font = new Font("Consolas", 10F),
                Text = "Create or open an encrypted Solana wallet." };
            addressPanel.Controls.Add(solAddressBox, 0, 0);
            addressPanel.Controls.Add(SecondaryButton("Copy address", SolanaCopyAddress), 1, 0);
            receive.Controls.Add(addressPanel);
            root.Controls.Add(receive, 0, 3);

            TableLayoutPanel assets = new TableLayoutPanel { Dock = DockStyle.Fill,
                ColumnCount = 2, RowCount = 1 };
            assets.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
            assets.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
            solBalanceLabel = Stat(assets, 0, "SOL");
            solMfrgBalanceLabel = Stat(assets, 1, "miniFORGE (mFRG)");
            solBalanceLabel.Text = "-";
            solMfrgBalanceLabel.Text = "Mainnet mint unconfigured";
            root.Controls.Add(assets, 0, 4);

            FlowLayoutPanel net = new FlowLayoutPanel { Dock = DockStyle.Fill,
                WrapContents = true };
            net.Controls.Add(new Label { Text = "Network", AutoSize = true,
                Padding = new Padding(1, 13, 6, 0) });
            solNetworkSelector = new ComboBox { Width = 195, DropDownStyle = ComboBoxStyle.DropDownList };
            solNetworkSelector.Items.Add("Solana mainnet-beta");
            solNetworkSelector.Items.Add("Solana devnet (test only)");
            solNetworkSelector.SelectedIndex = 0;
            solNetworkSelector.SelectedIndexChanged += delegate {
                solBalanceLabel.Text = "-";
                solMfrgBalanceLabel.Text = solNetworkSelector.SelectedIndex == 0 ?
                    "Mainnet mint unconfigured" : "Checking...";
                if (!String.IsNullOrEmpty(solCurrentAddress)) RefreshSolanaBalances(true);
            };
            net.Controls.Add(solNetworkSelector);
            net.Controls.Add(PrimaryButton("Refresh balances", delegate { RefreshSolanaBalances(true); }));
            solNetworkStatusLabel = new Label { Text = "Balances require an internet connection.",
                AutoSize = true, ForeColor = Color.DimGray, Padding = new Padding(4, 13, 0, 0) };
            net.Controls.Add(solNetworkStatusLabel);
            root.Controls.Add(net, 0, 5);

            Label info = new Label { Dock = DockStyle.Fill, ForeColor = Color.DimGray,
                Text = "Vaults are encrypted locally with your password. Keep a backup and recovery phrase offline; " +
                       "losing both means permanent loss of funds. Importing a CLI keypair cannot recreate its " +
                       "original recovery phrase. No private key or mnemonic is sent to RPC. " +
                       "The displayed mFRG balance uses the verified mint for the selected network; " +
                       "mainnet remains unconfigured until a verified official mainnet mint is published and independently checked." };
            root.Controls.Add(info, 0, 6);
            page.Controls.Add(root);
            return page;
        }

        private string SolanaSafeName()
        {
            string value = solWalletNameBox.Text.Trim();
            if (!Regex.IsMatch(value, "^[A-Za-z0-9_-]{1,48}$"))
                throw new InvalidOperationException("Use 1-48 letters, digits, underscores or dashes for the wallet name.");
            return value;
        }
        private string SolanaVaultPath()
        {
            return Path.Combine(SolanaVaultRoot(), SolanaSafeName() + ".frgsol");
        }
        private void SolanaPasswordReady()
        {
            if (solPasswordBox.Text.Length < 12)
                throw new InvalidOperationException("Use a Solana backup password of at least 12 characters.");
            if (solPasswordBox.Text != solConfirmPasswordBox.Text)
                throw new InvalidOperationException("Solana backup passwords do not match.");
        }
        private void SolanaOpened(string filename, string address)
        {
            solCurrentWalletPath = filename;
            solCurrentAddress = address;
            solAddressBox.Text = address;
            solPasswordBox.Clear();
            solConfirmPasswordBox.Clear();
            solWalletState.Text = "Unlocked for public-balance viewing. Vault remains encrypted at rest.";
            solWalletState.ForeColor = Color.DarkGreen;
            solBalanceLabel.Text = "Checking...";
            solMfrgBalanceLabel.Text = solNetworkSelector.SelectedIndex == 0 ?
                "Mainnet mint unconfigured" : "Checking...";
            RefreshSolanaBalances(true);
        }
        private void SolanaError(string message)
        {
            solWalletState.Text = message;
            solWalletState.ForeColor = Color.DarkRed;
            // Do not route any keygen output, passwords or mnemonic through ShowError/logs.
        }
        private string SolanaKeygenBinary()
        {
            string packaged = Path.Combine(binRoot, "solana-keygen.exe");
            if (File.Exists(packaged)) return packaged;
            string cliInstall = Path.Combine(Environment.GetFolderPath(
                Environment.SpecialFolder.UserProfile),
                ".local", "share", "solana", "install", "active_release",
                "bin", "solana-keygen.exe");
            if (File.Exists(cliInstall)) return cliInstall;
            throw new FileNotFoundException("Solana CLI (solana-keygen.exe) is required for local wallet creation. " +
                "Install the official Solana CLI and verify its origin.");
        }
        private void SolanaCreate(object sender, EventArgs e)
        {
            string scratch = null;
            try
            {
                SolanaPasswordReady();
                string target = SolanaVaultPath();
                Directory.CreateDirectory(SolanaVaultRoot());
                if (File.Exists(target))
                    throw new InvalidOperationException("Wallet name already exists. No existing wallet was changed.");
                // Solana's official keygen creates a temporary local keypair file.
                // The generated keypair/mnemonic are immediately put into an encrypted vault,
                // then the temporary file is removed. Create only inside local user-profile storage.
                scratch = Path.Combine(Path.GetDirectoryName(SolanaVaultRoot()),
                    "keygen-tmp-" + Guid.NewGuid().ToString("N"));
                Directory.CreateDirectory(scratch);
                string tempKeypair = Path.Combine(scratch, "keypair.json");
                ProcessStartInfo start = new ProcessStartInfo {
                    FileName = SolanaKeygenBinary(),
                    Arguments = "new --no-bip39-passphrase --word-count 12 --outfile \"" + tempKeypair + "\"",
                    UseShellExecute = false, CreateNoWindow = true,
                    RedirectStandardOutput = true, RedirectStandardError = true
                };
                string output;
                using (Process keygen = Process.Start(start))
                {
                    output = keygen.StandardOutput.ReadToEnd();
                    string ignoredStderr = keygen.StandardError.ReadToEnd();
                    if (!keygen.WaitForExit(30000) || keygen.ExitCode != 0)
                        throw new InvalidOperationException("Solana local key generation failed.");
                }
                string mnemonic = "";
                foreach (string line in output.Split(new char[] {'\r','\n'}, StringSplitOptions.RemoveEmptyEntries))
                {
                    string trimmed = line.Trim();
                    if (Regex.IsMatch(trimmed, "^[a-z]+(?: [a-z]+){11}$"))
                    {
                        mnemonic = trimmed;
                        break;
                    }
                }
                if (mnemonic.Length == 0)
                    throw new InvalidOperationException("Solana keygen did not provide a recoverable 12-word phrase.");
                string pair = File.ReadAllText(tempKeypair);
                string vault = SolanaVault.Encrypt(pair, mnemonic, solPasswordBox.Text);
                string address = SolanaVault.PublicAddress(vault);
                SolanaVault.SaveNew(target, vault);
                File.Delete(tempKeypair);
                Directory.Delete(scratch);
                scratch = null;
                SolanaOpened(target, address);
                solWalletState.Text = "Created and encrypted. Back up your vault and 12-word recovery phrase now.";
            }
            catch (Exception ex)
            {
                SolanaError("Creation failed: " + ex.GetType().Name +
                    ". Check password, name, CLI installation, and local permissions.");
            }
            finally
            {
                if (scratch != null)
                {
                    try
                    {
                        foreach (string f in Directory.GetFiles(scratch)) File.Delete(f);
                        Directory.Delete(scratch);
                    }
                    catch { SolanaError("WARNING: Temporary keypair cleanup failed. Secure the local Solana temporary folder."); }
                }
            }
        }
        private void SolanaImportKeypair(object sender, EventArgs e)
        {
            try
            {
                SolanaPasswordReady();
                string dest = SolanaVaultPath();
                Directory.CreateDirectory(SolanaVaultRoot());
                if (File.Exists(dest))
                    throw new InvalidOperationException("Wallet name already exists.");
                using (OpenFileDialog choose = new OpenFileDialog())
                {
                    choose.Title = "Select your existing Solana CLI keypair JSON (private)";
                    choose.Filter = "Solana keypair JSON (*.json)|*.json";
                    if (choose.ShowDialog(this) != DialogResult.OK) return;
                    FileInfo info = new FileInfo(choose.FileName);
                    if (info.Length > 16384) throw new InvalidDataException("Invalid keypair size.");
                    string keypair = File.ReadAllText(choose.FileName);
                    string vault = SolanaVault.Encrypt(keypair, "", solPasswordBox.Text);
                    SolanaVault.SaveNew(dest, vault);
                    SolanaOpened(dest, SolanaVault.PublicAddress(vault));
                    solWalletState.Text = "Existing keypair encrypted. Its original seed phrase is not recoverable from the JSON keypair; back up this vault.";
                }
            }
            catch (Exception ex)
            {
                SolanaError("Import failed: " + ex.Message);
            }
        }
        private void SolanaOpen(object sender, EventArgs e)
        {
            try
            {
                string filename = SolanaVaultPath();
                string data = File.ReadAllText(filename);
                SolanaVault.WalletSecret opened = SolanaVault.Decrypt(data, solPasswordBox.Text);
                SolanaOpened(filename, opened.Address);
            }
            catch (Exception ex)
            {
                SolanaError("Open failed: " + (ex is System.Security.Cryptography.CryptographicException ?
                    "Invalid password or corrupted backup." : ex.Message));
            }
        }
        private void SolanaRestoreBackup(object sender, EventArgs e)
        {
            try
            {
                SolanaPasswordReady();
                string dest = SolanaVaultPath();
                Directory.CreateDirectory(SolanaVaultRoot());
                if (File.Exists(dest)) throw new IOException("A wallet with this name already exists.");
                using (OpenFileDialog file = new OpenFileDialog())
                {
                    file.Title = "Restore encrypted Solana wallet backup";
                    file.Filter = "ForgeCoin encrypted Solana backup (*.frgsol)|*.frgsol";
                    if (file.ShowDialog(this) != DialogResult.OK) return;
                    FileInfo info = new FileInfo(file.FileName);
                    if (info.Length > 100000) throw new InvalidDataException("Encrypted backup exceeds size limit.");
                    string encoded = File.ReadAllText(file.FileName);
                    SolanaVault.WalletSecret restored = SolanaVault.Decrypt(encoded, solPasswordBox.Text);
                    SolanaVault.SaveNew(dest, encoded);
                    SolanaOpened(dest, restored.Address);
                    solWalletState.Text = "Encrypted Solana backup verified and restored.";
                }
            }
            catch (Exception ex) { SolanaError("Restore failed: " + ex.Message); }
        }
        private void SolanaExportBackup(object sender, EventArgs e)
        {
            try
            {
                if (String.IsNullOrEmpty(solCurrentWalletPath))
                    throw new InvalidOperationException("Open the Solana wallet first.");
                using (SaveFileDialog save = new SaveFileDialog())
                {
                    save.Title = "Save an encrypted Solana wallet backup";
                    save.Filter = "ForgeCoin encrypted Solana backup (*.frgsol)|*.frgsol";
                    save.FileName = Path.GetFileName(solCurrentWalletPath);
                    save.OverwritePrompt = true;
                    if (save.ShowDialog(this) != DialogResult.OK) return;
                    string source = Path.GetFullPath(solCurrentWalletPath);
                    string dest = Path.GetFullPath(save.FileName);
                    if (String.Equals(source, dest, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidOperationException("Choose a different location for your backup.");
                    File.Copy(source, dest, true);
                    solWalletState.Text = "Encrypted wallet backup saved. Keep it offline and remember its password.";
                }
            }
            catch (Exception ex) { SolanaError("Backup failed: " + ex.Message); }
        }
        private string SolanaPromptPassword()
        {
            using (Form prompt = new Form())
            {
                prompt.Text = "Unlock recovery phrase";
                prompt.StartPosition = FormStartPosition.CenterParent;
                prompt.FormBorderStyle = FormBorderStyle.FixedDialog;
                prompt.MaximizeBox = false; prompt.MinimizeBox = false;
                prompt.Width = 430; prompt.Height = 165;
                Label notice = new Label { Text = "Enter your encrypted Solana wallet password:",
                    Left = 14, Top = 12, AutoSize = true };
                TextBox input = new TextBox { Left = 14, Top = 38, Width = 388, UseSystemPasswordChar = true };
                Button ok = new Button { Text = "Unlock", DialogResult = DialogResult.OK,
                    Left = 306, Top = 77, Width = 95 };
                prompt.Controls.Add(notice); prompt.Controls.Add(input); prompt.Controls.Add(ok);
                prompt.AcceptButton = ok;
                return prompt.ShowDialog(this) == DialogResult.OK ? input.Text : null;
            }
        }
        private void SolanaShowRecovery(object sender, EventArgs e)
        {
            try
            {
                if (String.IsNullOrEmpty(solCurrentWalletPath))
                    throw new InvalidOperationException("Open the Solana wallet first.");
                if (MessageBox.Show(this,
                    "Recovery words control the entire Solana wallet. Never share them, photograph them, " +
                    "or save them in a cloud note. Display privately?", "Reveal recovery phrase",
                    MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
                string password = SolanaPromptPassword();
                if (password == null) return;
                SolanaVault.WalletSecret contents = SolanaVault.Decrypt(
                    File.ReadAllText(solCurrentWalletPath), password);
                if (contents.Address != solCurrentAddress)
                    throw new InvalidOperationException("Backup identity does not match the open wallet.");
                if (String.IsNullOrEmpty(contents.Mnemonic))
                    throw new InvalidOperationException(
                        "Imported CLI keypairs have no reconstructible BIP39 words. Use encrypted backups.");
                using (Form dialog = new Form())
                {
                    dialog.Text = "SENSITIVE - Solana recovery words";
                    dialog.StartPosition = FormStartPosition.CenterParent;
                    dialog.Width = 560; dialog.Height = 190;
                    dialog.FormBorderStyle = FormBorderStyle.FixedDialog;
                    dialog.MaximizeBox = false;
                    TextBox phrase = new TextBox { ReadOnly = true, Multiline = true,
                        Left = 20, Top = 22, Width = 500, Height = 72,
                        Font = new Font("Consolas", 11F), Text = contents.Mnemonic };
                    Label note = new Label { Left = 20, Top = 108, Width = 500, Height = 30,
                        Text = "Write the words down offline. Close this window when finished." };
                    dialog.Controls.Add(phrase); dialog.Controls.Add(note);
                    dialog.ShowDialog(this);
                    phrase.Clear();
                }
            }
            catch (Exception ex) { SolanaError("Cannot reveal phrase: " + ex.Message); }
        }
        private void SolanaLockClick(object sender, EventArgs e)
        {
            SolanaLock();
        }
        private void SolanaLock()
        {
            solCurrentWalletPath = null;
            solCurrentAddress = null;
            if (solAddressBox != null) solAddressBox.Text = "Wallet locked.";
            if (solPasswordBox != null) solPasswordBox.Clear();
            if (solConfirmPasswordBox != null) solConfirmPasswordBox.Clear();
            if (solBalanceLabel != null) solBalanceLabel.Text = "-";
            if (solMfrgBalanceLabel != null) solMfrgBalanceLabel.Text = "Locked";
            if (solWalletState != null) solWalletState.Text = "Locked";
        }
        private void SolanaCopyAddress(object sender, EventArgs e)
        {
            if (!String.IsNullOrEmpty(solCurrentAddress)) Clipboard.SetText(solCurrentAddress);
        }
        private string SolanaMainnetMint()
        {
            // Never substitute the devnet mint on mainnet. A separate verified
            // mint config is required after real on-chain mainnet issuance.
            string filename = Path.Combine(AppDomain.CurrentDomain.BaseDirectory,
                "config", "miniFORGE.mainnet.json");
            if (!File.Exists(filename)) return null;
            IDictionary settings = json.DeserializeObject(File.ReadAllText(filename)) as IDictionary;
            if (settings == null || !settings.Contains("network") ||
                Convert.ToString(settings["network"]) != "mainnet-beta" ||
                !settings.Contains("productionReady") ||
                !Convert.ToBoolean(settings["productionReady"]) ||
                !settings.Contains("mint")) return null;
            string mint = Convert.ToString(settings["mint"]);
            if (String.IsNullOrEmpty(mint) || mint.Length < 32 || mint.Length > 44)
                throw new InvalidDataException("Invalid mainnet mFRG mint configuration.");
            return mint;
        }
        private IDictionary SolanaRpc(string rpc, string method, object[] parameters)
        {
            Dictionary<string, object> request = new Dictionary<string, object> {
                { "jsonrpc", "2.0" }, { "id", "frg-solana-balances" }, { "method", method },
                { "params", parameters }
            };
            byte[] payload = Encoding.UTF8.GetBytes(json.Serialize(request));
            HttpWebRequest http = (HttpWebRequest)WebRequest.Create(rpc);
            http.Method = "POST"; http.ContentType = "application/json";
            http.ContentLength = payload.Length; http.Timeout = 9000;
            http.ReadWriteTimeout = 9000;
            using (Stream requestBody = http.GetRequestStream()) requestBody.Write(payload, 0, payload.Length);
            using (HttpWebResponse response = (HttpWebResponse)http.GetResponse())
            using (StreamReader reader = new StreamReader(response.GetResponseStream()))
            {
                IDictionary parsed = json.DeserializeObject(reader.ReadToEnd()) as IDictionary;
                if (parsed == null || parsed.Contains("error") || !parsed.Contains("result"))
                    throw new InvalidOperationException("Solana RPC unavailable or returned an error.");
                return parsed["result"] as IDictionary;
            }
        }
        private void RefreshSolanaBalances(bool force)
        {
            if (String.IsNullOrEmpty(solCurrentAddress) || solNetworkSelector == null) return;
            if (!force && (DateTime.UtcNow - solLastRefreshUtc).TotalSeconds < 12) return;
            if (Interlocked.Exchange(ref solRefreshInFlight, 1) != 0) return;
            solLastRefreshUtc = DateTime.UtcNow;
            string address = solCurrentAddress;
            bool mainnet = solNetworkSelector.SelectedIndex == 0;
            string rpc = mainnet ? "https://api.mainnet-beta.solana.com" : "https://api.devnet.solana.com";
            string mint = null;
            try { mint = mainnet ? SolanaMainnetMint() : DevnetMint; }
            catch { solMfrgBalanceLabel.Text = "Mint config error"; }
            string verifiedMint = mint;
            solNetworkStatusLabel.Text = mainnet ? "Mainnet: fetching confirmed balances..." :
                "DEVNET only: fetching test balances...";
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    IDictionary balance = SolanaRpc(rpc, "getBalance", new object[] {
                        address, new Dictionary<string, object>{{"commitment","confirmed"}}
                    });
                    long lamports = Convert.ToInt64(balance["value"], CultureInfo.InvariantCulture);
                    string sol = (lamports / 1000000000m).ToString("0.#########", CultureInfo.InvariantCulture);
                    string tokens = mainnet ? "Mainnet mint unconfigured" : "0";
                    if (verifiedMint != null)
                    {
                        IDictionary parsed = SolanaRpc(rpc, "getTokenAccountsByOwner", new object[] {
                            address,
                            new Dictionary<string, object> {{"mint", verifiedMint}},
                            new Dictionary<string, object> {{"encoding","jsonParsed"},{"commitment","confirmed"}}
                        });
                        decimal totalAtomic = 0;
                        IList accounts = parsed["value"] as IList;
                        if (accounts == null) throw new InvalidOperationException("Malformed SPL account response.");
                        foreach (object objectAccount in accounts)
                        {
                            IDictionary entry = objectAccount as IDictionary;
                            IDictionary account = entry == null ? null : entry["account"] as IDictionary;
                            if (account == null || Convert.ToString(account["owner"]) != SolanaProgramId)
                                throw new InvalidDataException("Unexpected SPL token program.");
                            IDictionary data = account["data"] as IDictionary;
                            IDictionary structure = data == null ? null : data["parsed"] as IDictionary;
                            IDictionary info = structure == null ? null : structure["info"] as IDictionary;
                            if (info == null || Convert.ToString(info["mint"]) != verifiedMint ||
                                Convert.ToString(info["owner"]) != address)
                                throw new InvalidDataException("SPL token account identity mismatch.");
                            IDictionary quantity = info["tokenAmount"] as IDictionary;
                            if (quantity == null || Convert.ToInt32(quantity["decimals"]) != 6)
                                throw new InvalidDataException("Unexpected mFRG decimals.");
                            totalAtomic += Decimal.Parse(Convert.ToString(quantity["amount"]),
                                NumberStyles.None, CultureInfo.InvariantCulture);
                        }
                        tokens = (totalAtomic / 1000000m).ToString("0.######", CultureInfo.InvariantCulture);
                    }
                    string displaySol = sol, displayTokens = tokens;
                    PostUi(delegate
                    {
                        if (solCurrentAddress != address || mainnet != (solNetworkSelector.SelectedIndex == 0)) return;
                        solBalanceLabel.Text = displaySol;
                        solMfrgBalanceLabel.Text = displayTokens;
                        solNetworkStatusLabel.Text = mainnet ?
                            "Solana mainnet - confirmed (public chain)" :
                            "Solana DEVNET - test balances only";
                    });
                }
                catch
                {
                    PostUi(delegate
                    {
                        if (solCurrentAddress != address || mainnet != (solNetworkSelector.SelectedIndex == 0)) return;
                        solBalanceLabel.Text = "Unavailable";
                        solMfrgBalanceLabel.Text = verifiedMint == null ?
                            "Mainnet mint unconfigured" : "Unavailable";
                        solNetworkStatusLabel.Text = "RPC unavailable. Check connection and retry.";
                    });
                }
                finally { Interlocked.Exchange(ref solRefreshInFlight, 0); }
            });
        }
        private void RefreshSolanaBalances()
        {
            RefreshSolanaBalances(false);
        }
    }
}
