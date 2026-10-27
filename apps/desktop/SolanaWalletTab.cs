using System;
using System.Collections;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using System.Web.Script.Serialization;

namespace ForgeCoinDesktop
{
    // Isolated Solana devnet wallet. This does not handle native FRG keys or enable any token sale.
    internal sealed partial class MainForm
    {
        private const string SolanaRpcEndpoint = "https://api.devnet.solana.com";
        // Release gate: remove only after security and lifecycle review.
        private static readonly bool SolanaWalletEnabled = false;
        private readonly JavaScriptSerializer solanaJson = new JavaScriptSerializer();
        private readonly string solanaWalletDirectory =
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ForgeCoin", "solana-devnet-v1");
        private TextBox solanaNameBox, solanaPasswordBox, solanaAddressBox, solanaFrgMintBox, solanaUsdcMintBox;
        private Label solanaState, solanaSolBalance, solanaFrgBalance, solanaUsdcBalance;
        private Button solanaCreateButton, solanaRestoreButton, solanaUnlockButton, solanaRevealButton,
            solanaBackupButton, solanaImportButton, solanaRefreshButton, solanaCloseButton;
        private string solanaCurrentVault, solanaPublicAddress;
        private bool solanaBusy;

        private TabPage BuildSolanaTab()
        {
            Directory.CreateDirectory(solanaWalletDirectory);
            TabPage tab = new TabPage("Solana Wallet") { AutoScroll = true };
            TableLayoutPanel panel = new TableLayoutPanel
            {
                Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(18), ColumnCount = 1, RowCount = 7
            };
            panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            panel.Controls.Add(new Label {
                Text = "Solana wallet - COMING SOON (all controls disabled)",
                ForeColor = Color.DarkRed, Font = new Font("Segoe UI Semibold", 11F), AutoSize = true,
                Margin = new Padding(0, 0, 0, 12)
            }, 0, 0);
            panel.Controls.Add(new Label {
                Text = "Encrypted BIP39 wallet; derivation m/44'/501'/0'/0'. " +
                       "No Solana mainnet transfers, production minting, or USDC trading are enabled here.",
                AutoSize = true, MaximumSize = new Size(880, 0), Margin = new Padding(0, 0, 0, 16)
            }, 0, 1);

            GroupBox setup = new GroupBox { Text = "Create, unlock or restore your Solana wallet", Height = 167, Dock = DockStyle.Fill };
            FlowLayoutPanel setupFlow = new FlowLayoutPanel { Dock = DockStyle.Fill, AutoScroll = true, Padding = new Padding(9) };
            setupFlow.Controls.Add(new Label { Text = "Name", AutoSize = true, Margin = new Padding(3, 11, 7, 4) });
            solanaNameBox = new TextBox { Width = 165, Text = "solana-devnet" };
            setupFlow.Controls.Add(solanaNameBox);
            setupFlow.Controls.Add(new Label { Text = "Encryption password (12+ characters)", AutoSize = true, Margin = new Padding(13, 11, 7, 4) });
            solanaPasswordBox = new TextBox { Width = 235, UseSystemPasswordChar = true };
            setupFlow.Controls.Add(solanaPasswordBox);
            solanaCreateButton = SolanaButton("Create", delegate { StartSolanaWalletOperation("create", null); });
            solanaUnlockButton = SolanaButton("Unlock", delegate { StartSolanaWalletOperation("unlock", null); });
            solanaRestoreButton = SolanaButton("Restore words", RestoreSolanaWords);
            solanaRevealButton = SolanaButton("Reveal recovery words", delegate { StartSolanaWalletOperation("reveal", null); });
            solanaBackupButton = SolanaButton("Backup encrypted wallet", BackupSolanaWallet);
            solanaImportButton = SolanaButton("Import encrypted backup", ImportSolanaWallet);
            solanaCloseButton = SolanaButton("Lock wallet", delegate { LockSolanaWallet(); });
            setupFlow.Controls.Add(solanaCreateButton);
            setupFlow.Controls.Add(solanaUnlockButton);
            setupFlow.Controls.Add(solanaRestoreButton);
            setupFlow.Controls.Add(solanaRevealButton);
            setupFlow.Controls.Add(solanaBackupButton);
            setupFlow.Controls.Add(solanaImportButton);
            setupFlow.Controls.Add(solanaCloseButton);
            setup.Controls.Add(setupFlow);
            panel.Controls.Add(setup, 0, 2);

            GroupBox address = new GroupBox { Text = "Public address and status", Dock = DockStyle.Fill, Height = 112 };
            Panel addressPanel = new Panel { Dock = DockStyle.Fill, Padding = new Padding(10) };
            solanaState = new Label { Text = "Locked. Wallet files stored in %LOCALAPPDATA%\\ForgeCoin\\solana-devnet-v1", AutoSize = true, Dock = DockStyle.Top };
            solanaAddressBox = new TextBox { ReadOnly = true, Dock = DockStyle.Bottom, Text = "Unlock a wallet to display its address." };
            addressPanel.Controls.Add(solanaState);
            addressPanel.Controls.Add(solanaAddressBox);
            address.Controls.Add(addressPanel);
            panel.Controls.Add(address, 0, 3);

            GroupBox tokens = new GroupBox { Text = "Track token mints on Solana devnet", Height = 145, Dock = DockStyle.Fill };
            FlowLayoutPanel tokenFlow = new FlowLayoutPanel { Dock = DockStyle.Fill, AutoScroll = true, Padding = new Padding(9) };
            tokenFlow.Controls.Add(new Label { Text = "ForgeCoin SPL mint (devnet)", AutoSize = true, Margin = new Padding(3, 11, 8, 4) });
            solanaFrgMintBox = new TextBox { Width = 335 };
            tokenFlow.Controls.Add(solanaFrgMintBox);
            tokenFlow.Controls.Add(new Label { Text = "USDC devnet mint (optional)", AutoSize = true, Margin = new Padding(12, 11, 8, 4) });
            solanaUsdcMintBox = new TextBox { Width = 335 };
            tokenFlow.Controls.Add(solanaUsdcMintBox);
            tokenFlow.Controls.Add(new Label {
                Text = "Mint addresses are not configured until they are verified on devnet. Do not paste a mainnet USDC address.",
                AutoSize = true, ForeColor = Color.DarkRed, MaximumSize = new Size(720, 0)
            });
            tokens.Controls.Add(tokenFlow);
            panel.Controls.Add(tokens, 0, 4);

            GroupBox balances = new GroupBox { Text = "Balances (public devnet RPC)", Height = 148, Dock = DockStyle.Fill };
            FlowLayoutPanel balanceFlow = new FlowLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(10), AutoScroll = true };
            solanaSolBalance = SolanaBalanceLabel("SOL: not loaded");
            solanaFrgBalance = SolanaBalanceLabel("mFRG (SPL): mint not configured");
            solanaUsdcBalance = SolanaBalanceLabel("USDC: mint not configured");
            solanaRefreshButton = SolanaButton("Refresh balances", RefreshSolanaBalances);
            balanceFlow.Controls.Add(solanaSolBalance);
            balanceFlow.Controls.Add(solanaFrgBalance);
            balanceFlow.Controls.Add(solanaUsdcBalance);
            balanceFlow.Controls.Add(solanaRefreshButton);
            balances.Controls.Add(balanceFlow);
            panel.Controls.Add(balances, 0, 5);

            panel.Controls.Add(new Label {
                Text = "The encrypted vault and its password are both needed to unlock the wallet. " +
                       "Write the recovery words on offline media; an encrypted wallet backup is NOT a substitute for them. " +
                       "Never reuse your 25-word native FRG phrase. Sending, bridging and minting are disabled in this preview.",
                AutoSize = true, MaximumSize = new Size(850, 0), ForeColor = Color.DarkSlateGray,
                Margin = new Padding(0, 15, 0, 15)
            }, 0, 6);
            tab.Controls.Add(panel);
            LockSolanaWallet();
            if (!SolanaWalletEnabled)
            {
                DisableSolanaInputTree(panel);
                solanaState.Text = "Coming soon - Solana wallet is disabled until a verified release.";
            }
            return tab;
        }

        private static void DisableSolanaInputTree(Control parent)
        {
            foreach (Control child in parent.Controls)
            {
                if (child is Button || child is TextBox || child is ComboBox || child is NumericUpDown)
                    child.Enabled = false;
                DisableSolanaInputTree(child);
            }
        }

        private static Button SolanaButton(string text, EventHandler handler)
        {
            Button button = new Button { Text = text, AutoSize = true, Margin = new Padding(5, 5, 5, 7) };
            button.Click += handler;
            return button;
        }
        private static Label SolanaBalanceLabel(string value)
        {
            return new Label { Text = value, AutoSize = true, MinimumSize = new Size(175, 28), Margin = new Padding(7, 12, 7, 4) };
        }
        private void SetSolanaControls()
        {
            if (!SolanaWalletEnabled)
            {
                solanaCreateButton.Enabled = false;
                solanaRestoreButton.Enabled = false;
                solanaUnlockButton.Enabled = false;
                solanaRevealButton.Enabled = false;
                solanaBackupButton.Enabled = false;
                solanaImportButton.Enabled = false;
                solanaCloseButton.Enabled = false;
                solanaRefreshButton.Enabled = false;
                solanaNameBox.Enabled = false;
                solanaPasswordBox.Enabled = false;
                return;
            }
            bool unlocked = !String.IsNullOrEmpty(solanaPublicAddress);
            solanaCreateButton.Enabled = !solanaBusy;
            solanaRestoreButton.Enabled = !solanaBusy;
            solanaUnlockButton.Enabled = !solanaBusy;
            solanaRevealButton.Enabled = unlocked && !solanaBusy;
            solanaBackupButton.Enabled = unlocked && !solanaBusy;
            solanaImportButton.Enabled = !solanaBusy;
            solanaCloseButton.Enabled = unlocked && !solanaBusy;
            solanaRefreshButton.Enabled = unlocked && !solanaBusy;
            solanaNameBox.Enabled = !solanaBusy;
            solanaPasswordBox.Enabled = !solanaBusy;
        }
        private void LockSolanaWallet()
        {
            solanaPublicAddress = null;
            solanaCurrentVault = null;
            if (solanaPasswordBox != null) solanaPasswordBox.Clear();
            if (solanaAddressBox != null) solanaAddressBox.Text = "Unlock a wallet to display its address.";
            if (solanaState != null) solanaState.Text = "Locked - Solana devnet wallet";
            if (solanaSolBalance != null) solanaSolBalance.Text = "SOL: not loaded";
            if (solanaFrgBalance != null) solanaFrgBalance.Text = "mFRG (SPL): mint not configured";
            if (solanaUsdcBalance != null) solanaUsdcBalance.Text = "USDC: mint not configured";
            if (solanaCreateButton != null) SetSolanaControls();
        }
        private string ValidateSolanaVaultPath()
        {
            string name = solanaNameBox.Text.Trim();
            if (!Regex.IsMatch(name, "^[A-Za-z0-9_-]{1,48}$"))
                throw new InvalidOperationException("Use 1-48 letters, digits, hyphen or underscore for wallet name.");
            return Path.Combine(solanaWalletDirectory, name + ".wallet.json");
        }
        private void RestoreSolanaWords(object sender, EventArgs e)
        {
            if (!SolanaWalletEnabled) return;
            using (Form dialog = new Form { Text = "Restore a Solana devnet wallet", Width = 670, Height = 230, StartPosition = FormStartPosition.CenterParent })
            {
                Label notice = new Label { Text = "Enter your separate Solana BIP39 recovery phrase. Do not use native FRG words.", Dock = DockStyle.Top, Height = 45, Padding = new Padding(12) };
                TextBox words = new TextBox { Dock = DockStyle.Top, UseSystemPasswordChar = true, Margin = new Padding(12) };
                Button restore = new Button { Text = "Restore", Dock = DockStyle.Bottom, DialogResult = DialogResult.OK };
                dialog.Controls.Add(restore);
                dialog.Controls.Add(words);
                dialog.Controls.Add(notice);
                dialog.AcceptButton = restore;
                if (dialog.ShowDialog(this) != DialogResult.OK) return;
                string phrase = words.Text;
                words.Clear();
                StartSolanaWalletOperation("restore", phrase);
            }
        }
        private void StartSolanaWalletOperation(string operation, string words)
        {
            if (!SolanaWalletEnabled) return;
            if (solanaBusy) return;
            string path;
            try { path = operation == "reveal" ? solanaCurrentVault : ValidateSolanaVaultPath(); }
            catch (Exception ex) { MessageBox.Show(this, ex.Message, "Solana wallet"); return; }
            if (String.IsNullOrEmpty(path)) { MessageBox.Show(this, "Unlock a wallet first."); return; }
            string password = solanaPasswordBox.Text;
            solanaPasswordBox.Clear();
            if (password.Length < 12) {
                MessageBox.Show(this, "Enter the wallet encryption password (at least 12 characters).", "Solana wallet");
                return;
            }
            solanaBusy = true;
            solanaState.Text = "Working locally..."; SetSolanaControls();
            ThreadPool.QueueUserWorkItem(delegate {
                IDictionary response = null;
                string failure = null;
                try {
                    response = CallSolanaHelper(operation, path, password, words);
                    if (!Convert.ToBoolean(response["ok"]))
                        failure = Convert.ToString(response["error"]);
                }
                catch (Exception ex) { failure = ex.Message; }
                try {
                    if (IsDisposed || !IsHandleCreated) return;
                    BeginInvoke((MethodInvoker)delegate {
                        solanaBusy = false;
                        if (failure != null) {
                            solanaState.Text = "Wallet operation failed";
                            MessageBox.Show(this, failure, "Solana wallet", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                        } else {
                            solanaPublicAddress = Convert.ToString(response["address"]);
                            solanaCurrentVault = path;
                            solanaAddressBox.Text = solanaPublicAddress;
                            solanaState.Text = "Unlocked on Solana DEVNET (" + operation + " succeeded)";
                            if (response.Contains("mnemonic") && response["mnemonic"] != null)
                                ShowSolanaPhrase(Convert.ToString(response["mnemonic"]));
                            RefreshSolanaBalances(null, EventArgs.Empty);
                        }
                        SetSolanaControls();
                    });
                } catch (InvalidOperationException) { }
            });
        }

        private IDictionary CallSolanaHelper(string op, string path, string password, string words)
        {
            string helper = Path.Combine(binRoot, "solana-wallet-helper.exe");
            if (!File.Exists(helper)) throw new FileNotFoundException("Solana wallet helper is not installed in the bin folder.", helper);
            ProcessStartInfo start = new ProcessStartInfo(helper) {
                UseShellExecute = false, CreateNoWindow = true, RedirectStandardInput = true,
                RedirectStandardOutput = true, RedirectStandardError = false
            };
            using (Process process = new Process { StartInfo = start }) {
                process.Start();
                process.StandardInput.Write(solanaJson.Serialize(new {
                    op = op, vault_path = path, password = password, mnemonic = words
                }));
                process.StandardInput.Close();
                string answer = process.StandardOutput.ReadToEnd();
                if (!process.WaitForExit(30000) || process.ExitCode != 0)
                    throw new InvalidOperationException("Solana helper did not complete successfully.");
                IDictionary result = solanaJson.DeserializeObject(answer) as IDictionary;
                if (result == null || !result.Contains("ok")) throw new InvalidOperationException("Invalid helper response.");
                return result;
            }
        }
        private void ShowSolanaPhrase(string phrase)
        {
            using (Form dialog = new Form { Text = "Solana recovery words - keep offline", Width = 690, Height = 285, StartPosition = FormStartPosition.CenterParent })
            using (System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer { Interval = 60000 }) {
                Label notice = new Label { Text = "Write these words down on offline media. Anyone with them can control this wallet. Hides automatically after 60 seconds.", Dock = DockStyle.Top, Height = 60, ForeColor = Color.DarkRed, Padding = new Padding(12) };
                TextBox wordsBox = new TextBox { Text = phrase, Dock = DockStyle.Fill, ReadOnly = true, Multiline = true,
                    Font = new Font("Consolas", 12F), ShortcutsEnabled = false, ScrollBars = ScrollBars.Vertical };
                Button done = new Button { Text = "I recorded these offline", Dock = DockStyle.Bottom, Height = 40, DialogResult = DialogResult.OK };
                dialog.Controls.Add(wordsBox); dialog.Controls.Add(notice); dialog.Controls.Add(done);
                timer.Tick += delegate { wordsBox.Clear(); dialog.Close(); };
                timer.Start();
                dialog.ShowDialog(this);
                wordsBox.Clear();
            }
        }
        private void BackupSolanaWallet(object sender, EventArgs e)
        {
            if (!SolanaWalletEnabled) return;
            if (String.IsNullOrEmpty(solanaCurrentVault)) return;
            using (SaveFileDialog dlg = new SaveFileDialog { FileName = "solana-encrypted-backup.wallet.json",
                Filter = "Encrypted wallet JSON (*.json)|*.json", OverwritePrompt = true }) {
                if (dlg.ShowDialog(this) != DialogResult.OK) return;
                if (String.Equals(Path.GetFullPath(dlg.FileName), Path.GetFullPath(solanaCurrentVault), StringComparison.OrdinalIgnoreCase))
                    return;
                try { File.Copy(solanaCurrentVault, dlg.FileName, true); MessageBox.Show(this, "Encrypted backup saved. Keep the separate password and offline seed phrase."); }
                catch (Exception ex) { MessageBox.Show(this, ex.Message, "Backup failed"); }
            }
        }
        private void ImportSolanaWallet(object sender, EventArgs e)
        {
            if (!SolanaWalletEnabled) return;
            string destination;
            try { destination = ValidateSolanaVaultPath(); }
            catch (Exception ex) { MessageBox.Show(this, ex.Message, "Import failed"); return; }
            if (File.Exists(destination)) {
                MessageBox.Show(this, "This wallet name already exists. Choose a different wallet name to prevent key loss.");
                return;
            }
            using (OpenFileDialog dlg = new OpenFileDialog {
                Title = "Select an encrypted Solana wallet backup",
                Filter = "Encrypted wallet JSON (*.json)|*.json"
            }) {
                if (dlg.ShowDialog(this) != DialogResult.OK) return;
                try {
                    FileInfo file = new FileInfo(dlg.FileName);
                    if (file.Length > 8192) throw new InvalidOperationException("Encrypted wallet backup is unexpectedly large.");
                    IDictionary data = solanaJson.DeserializeObject(File.ReadAllText(dlg.FileName)) as IDictionary;
                    if (data == null || Convert.ToString(Field(data, "network")) != "solana-devnet" ||
                        Convert.ToString(Field(data, "derivation")) != "m/44'/501'/0'/0'" ||
                        !IsSolanaAddress(Convert.ToString(Field(data, "address"))) ||
                        Convert.ToString(Field(data, "version")) != "1")
                        throw new InvalidOperationException("Unsupported or invalid Solana devnet backup.");
                    File.Copy(dlg.FileName, destination, false);
                    MessageBox.Show(this, "Encrypted backup imported. Enter its original password and select Unlock.");
                } catch (Exception ex) { MessageBox.Show(this, ex.Message, "Import failed"); }
            }
        }
        private static bool IsSolanaAddress(string value)
        {
            return !String.IsNullOrWhiteSpace(value) && Regex.IsMatch(value.Trim(), "^[1-9A-HJ-NP-Za-km-z]{32,44}$");
        }
        private object SolanaRpc(string method, object[] parameters)
        {
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(SolanaRpcEndpoint);
            request.Method = "POST"; request.ContentType = "application/json"; request.Timeout = 12000; request.ReadWriteTimeout = 12000;
            byte[] data = Encoding.UTF8.GetBytes(solanaJson.Serialize(new { jsonrpc = "2.0", id = 1, method = method, @params = parameters }));
            using (Stream stream = request.GetRequestStream()) stream.Write(data, 0, data.Length);
            using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
            using (StreamReader reader = new StreamReader(response.GetResponseStream())) {
                IDictionary result = solanaJson.DeserializeObject(reader.ReadToEnd()) as IDictionary;
                if (result == null || result.Contains("error")) throw new InvalidOperationException("Solana devnet RPC unavailable or rejected request.");
                return result["result"];
            }
        }
        private static object Field(object parent, string key)
        {
            IDictionary d = parent as IDictionary;
            return d != null && d.Contains(key) ? d[key] : null;
        }
        private decimal ReadSolanaTokenBalance(string address, string mint)
        {
            decimal sum = 0;
            object result = SolanaRpc("getTokenAccountsByOwner", new object[] { address,
                new { mint = mint }, new { encoding = "jsonParsed", commitment = "confirmed" } });
            IEnumerable accounts = Field(result, "value") as IEnumerable;
            if (accounts == null) return 0;
            foreach (object entry in accounts) {
                object parsed = Field(Field(entry, "account"), "data");
                parsed = Field(parsed, "parsed");
                object tokenAmount = Field(Field(parsed, "info"), "tokenAmount");
                string amount = Convert.ToString(Field(tokenAmount, "uiAmountString"), CultureInfo.InvariantCulture);
                decimal number;
                if (Decimal.TryParse(amount, NumberStyles.Number, CultureInfo.InvariantCulture, out number)) sum += number;
            }
            return sum;
        }
        private void RefreshSolanaBalances(object sender, EventArgs e)
        {
            if (!SolanaWalletEnabled) return;
            if (String.IsNullOrEmpty(solanaPublicAddress) || solanaBusy) return;
            string address = solanaPublicAddress;
            string frgMint = solanaFrgMintBox.Text.Trim(), usdcMint = solanaUsdcMintBox.Text.Trim();
            solanaRefreshButton.Enabled = false;
            solanaState.Text = "Reading public balances from Solana devnet...";
            ThreadPool.QueueUserWorkItem(delegate {
                string sol = null, frg = null, usdc = null, problem = null;
                try {
                    object balance = SolanaRpc("getBalance", new object[] { address, new { commitment = "confirmed" } });
                    decimal lamports = Convert.ToDecimal(Field(balance, "value"), CultureInfo.InvariantCulture);
                    sol = (lamports / 1000000000m).ToString("0.#########", CultureInfo.InvariantCulture) + " SOL";
                    frg = !IsSolanaAddress(frgMint) ? "mint not configured" :
                        ReadSolanaTokenBalance(address, frgMint).ToString("0.#########", CultureInfo.InvariantCulture);
                    usdc = !IsSolanaAddress(usdcMint) ? "mint not configured" :
                        ReadSolanaTokenBalance(address, usdcMint).ToString("0.#########", CultureInfo.InvariantCulture);
                } catch (Exception ex) { problem = ex.Message; }
                try {
                    if (IsDisposed || !IsHandleCreated) return;
                    BeginInvoke((MethodInvoker)delegate {
                        solanaRefreshButton.Enabled = !solanaBusy && !String.IsNullOrEmpty(solanaPublicAddress);
                        if (solanaPublicAddress != address) return;
                        if (problem == null) {
                            solanaSolBalance.Text = "SOL: " + sol;
                            solanaFrgBalance.Text = "mFRG (SPL): " + frg;
                            solanaUsdcBalance.Text = "USDC: " + usdc;
                            solanaState.Text = "Public balances refreshed (devnet, confirmed)";
                        } else solanaState.Text = "Balance refresh failed: " + problem;
                    });
                } catch (InvalidOperationException) { }
            });
        }
    }
}
