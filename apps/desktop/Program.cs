using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using System.Web.Script.Serialization;

namespace ForgeCoinDesktop
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }

    internal sealed partial class MainForm : Form
    {
        private const decimal AtomicUnits = 100000000m;
        // This prelaunch GUI may scan/restore disposable wallets, but must NOT
        // initiate native MAINNET mining or transfer before the reviewed launch.
        // No environment variable or configuration file can override this.
        private static readonly bool NativeSpendAuthorized = false;
        private static readonly bool NativeMiningAuthorized = false;
        private int transferInFlight;
#if FRG_PRIVATE_MINING_QA && !FRG_PRIVATE_UI_QA
#error Isolated native mining QA must use the temporary private UI sandbox.
#endif
#if FRG_PRIVATE_POOL_QA && !FRG_PRIVATE_UI_QA
#error Isolated native pool QA must use the temporary private UI sandbox.
#endif
#if FRG_PRIVATE_MINING_QA
        // Strict test-only build. Ordinary and private-prelaunch binaries do
        // not define this symbol; NativeMiningAuthorized remains false.
        private const string QaDaemonSha256 =
            "3efaf014c7fdfcea167630f1884abee2defd40f28f1e725b6c0a8fcede5b5c37";

        private bool IsolatedSoloQaReady()
        {
            if (!nodeOfflineMode || !bootstrapModeBox.Checked ||
                !IsRunning(daemon) || daemon.StartInfo == null)
                return false;
            string expected = Path.GetFullPath(Path.Combine(binRoot, "forged.exe"));
            string actual = Path.GetFullPath(daemon.StartInfo.FileName);
            if (!String.Equals(expected, actual, StringComparison.OrdinalIgnoreCase))
                return false;
            string args = daemon.StartInfo.Arguments;
            return args.Contains("--offline") &&
                   args.Contains("--no-zmq") &&
                   args.Contains("--out-peers 0") &&
                   args.Contains("--in-peers 0") &&
                   args.Contains("--p2p-bind-ip 127.0.0.1") &&
                   args.Contains("--rpc-bind-ip 127.0.0.1") &&
                   args.Contains(Quote(Path.Combine(appRoot, "blockchain")));
        }

        private void RequirePinnedPrivateQaDaemon(string executable)
        {
            using (FileStream input = File.OpenRead(executable))
            using (SHA256 hash = SHA256.Create())
            {
                string digest = BitConverter.ToString(hash.ComputeHash(input))
                    .Replace("-", "").ToLowerInvariant();
                if (digest != QaDaemonSha256)
                    throw new InvalidOperationException(
                        "Local mining QA requires the exact pinned private daemon.");
            }
        }
#endif
#if FRG_PRIVATE_POOL_QA
        // Test-only offline XMRig path; deliberately no Stratum service or
        // CPU/GPU backend, no FRG credentials and no externally reachable peer.
        // The ordinary Windows desktop never defines this symbol.
        private const string QaXmrigSha256 =
            "e5cd22ffe8725fbabf32ae2ba993d5b791e65e2ef159ad32ad260505f2e22480";

        private bool IsolatedPoolQaReady()
        {
            return !IsRunning(daemon) && !IsRunning(poolMiner) &&
                !stopMiningButton.Enabled &&
                String.Equals(poolUrlBox.Text.Trim(), "127.0.0.1:49690",
                              StringComparison.Ordinal);
        }

        private void RequirePinnedPrivateQaXmrig(string file)
        {
            using (FileStream stream = File.OpenRead(file))
            using (SHA256 sha = SHA256.Create())
            {
                string digest = BitConverter.ToString(sha.ComputeHash(stream))
                    .Replace("-", "").ToLowerInvariant();
                if (digest != QaXmrigSha256)
                    throw new InvalidOperationException(
                        "Private pool GUI QA requires the locally pinned XMRig executable.");
            }
        }
#endif
#if FRG_PRIVATE_UI_QA
        // Compiled ONLY into the isolated WinForms test harness, never into the
        // desktop executable or the shipped prelaunch package. Refuse to touch
        // an existing user's %LOCALAPPDATA% wallet files.
        private static string PrivateQaPath(string environmentVariable)
        {
            string path = Environment.GetEnvironmentVariable(environmentVariable);
            if (String.IsNullOrWhiteSpace(path))
                throw new InvalidOperationException("Private GUI QA sandbox path not supplied.");
            string full = Path.GetFullPath(path);
            string temp = Path.GetFullPath(Path.GetTempPath());
            if (!full.StartsWith(temp, StringComparison.OrdinalIgnoreCase) ||
                full.IndexOf("frg-windows-gui-qa-", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidOperationException("Private GUI QA must remain in an isolated temporary folder.");
            return full;
        }
        private readonly string appRoot = PrivateQaPath("FRG_PRIVATE_UI_QA_ROOT");
        private readonly string binRoot = PrivateQaPath("FRG_PRIVATE_UI_QA_BIN");
#else
        private readonly string appRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ForgeCoin");
        private readonly string binRoot = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "bin");
#endif
        private readonly JavaScriptSerializer json = new JavaScriptSerializer();
        private readonly System.Windows.Forms.Timer refreshTimer = new System.Windows.Forms.Timer();
        private readonly System.Windows.Forms.Timer miningTimer = new System.Windows.Forms.Timer();

        private Process daemon;
        private Process walletRpc;
        private WalletRpcSession walletSession;
        private Process poolMiner;
        // Per-run public monitor identity: prevent reading another process's
        // localhost XMRig API as if it were our FRG pool miner.
        private string poolApiId;
        private bool walletOpen;

        private Label nodeState;
        private Label heightValue;
        private Label peersValue;
        private Label syncValue;
        private Label hashValue;
        private TextBox peerBox;
        private Button startNodeButton;
        private Button stopNodeButton;
        private RichTextBox logBox;
        private CheckBox bootstrapModeBox;
        private bool nodeOfflineMode;

        private TextBox walletNameBox;
        private TextBox passwordBox;
        private Label walletState;
        private TextBox addressBox;
        private Label balanceValue;
        private Label unlockedValue;
        private TextBox sendAddressBox;
        private TextBox sendAmountBox;
        private Button createWalletButton;
        private Button openWalletButton;
        private Button restoreWalletButton;
        private Button closeWalletButton;
        private Button seedButton;
        private Button sendButton;
        private TextBox miningAddressBox;
        private NumericUpDown miningThreads;
        private Label miningState;
        private Label hashRateValue;
        private Label miningThreadsValue;
        private Label miningDifficultyValue;
        private Label miningBlockHeightValue;
        private Label miningNetworkRateValue;
        private Label miningRewardValue;
        private Label miningTargetValue;
        private Label miningBlocksFoundValue;
        private Button startMiningButton;
        private Button stopMiningButton;
        private Label miningDetailLabel;
        private Label miningNodeDetailLabel;
        private int minedBlocksSession;
        private DataGridView receiveAddressGrid;
        private DataGridView contactGrid;
        private TextBox receiveLabelBox;
        private TextBox contactNameBox;
        private TextBox contactAddressBox;
        private TextBox poolUrlBox;
        private TextBox poolUserBox;
        private TextBox poolWorkerBox;
        private TextBox poolPassBox;
        private NumericUpDown poolThreads;
        private Label poolState;
        private Label poolHashRateValue;
        private Label poolAcceptedValue;
        private Label poolRejectedValue;
        private Label poolDifficultyValue;
        private Label poolNameValue;
        private Label poolPingValue;
        private Label poolUptimeValue;
        private Label poolAlgorithmValue;
        private Label poolDetailLabel;
        private RichTextBox poolLogBox;
        private Button startPoolButton;
        private Button stopPoolButton;
        private Label explorerHeightValue;
        private Label explorerDifficultyValue;
        private Label explorerNetworkRateValue;
        private Label explorerPoolValue;
        private Label explorerStatusLabel;
        private DataGridView explorerBlockGrid;
        private TextBox explorerLookupBox;
        private RichTextBox explorerResultBox;
        private int nodeRefreshInFlight;
        private int miningRefreshInFlight;
        private int miningStartInFlight;
        private int walletRefreshInFlight;
        private int poolRefreshInFlight;

        public MainForm()
        {
            Text = "ForgeCoin Desktop";
            MinimumSize = new Size(900, 680);
            Size = new Size(1040, 760);
            StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 10F);
            BackColor = Color.FromArgb(234, 243, 253);

            Directory.CreateDirectory(appRoot);
            Directory.CreateDirectory(Path.Combine(appRoot, "blockchain"));
            Directory.CreateDirectory(Path.Combine(appRoot, "wallets"));
            Directory.CreateDirectory(Path.Combine(appRoot, "ringdb"));
            Directory.CreateDirectory(Path.Combine(appRoot, "logs"));

            TableLayoutPanel shell = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 2, Margin = new Padding(0), Padding = new Padding(0) };
            shell.RowStyles.Add(new RowStyle(SizeType.Absolute, 82));
            shell.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            shell.Controls.Add(BuildHeader(), 0, 0);
            shell.Controls.Add(BuildTabs(), 0, 1);
            Controls.Add(shell);

            refreshTimer.Interval = 3000;
            refreshTimer.Tick += delegate
            {
                RefreshNode();
                if (walletOpen) RefreshWallet();
                if (!String.IsNullOrEmpty(solCurrentAddress)) RefreshSolanaBalances();
            };
            refreshTimer.Start();
            miningTimer.Interval = 1000;
            miningTimer.Tick += delegate { RefreshMining(); RefreshPoolMining(); };
            miningTimer.Start();
            FormClosing += OnClosing;
            FormClosed += delegate { SolanaLock(); };
        }

        private Control BuildHeader()
        {
            Panel header = new Panel { Dock = DockStyle.Top, Height = 82, BackColor = Color.FromArgb(9, 32, 61) };
            Label title = new Label { Text = "FORGECOIN", ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 22F), AutoSize = true, Location = new Point(87, 14) };
            Label subtitle = new Label { Text = "Wallet  /  RandomX Mining  /  Network Explorer", ForeColor = Color.FromArgb(164, 204, 243), AutoSize = true, Location = new Point(89, 52) };
            string logoPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "forgecoin-logo.png");
            if (File.Exists(logoPath))
            {
                try
                {
                    PictureBox logo = new PictureBox { Location = new Point(18, 10), Size = new Size(62, 62), SizeMode = PictureBoxSizeMode.Zoom };
                    using (Image loaded = Image.FromFile(logoPath)) logo.Image = new Bitmap(loaded);
                    header.Controls.Add(logo);
                }
                catch (Exception) { /* Missing or invalid artwork must never prevent startup. */ }
            }
            header.Controls.Add(title);
            header.Controls.Add(subtitle);
            return header;
        }

        private Control BuildTabs()
        {
            TabControl tabs = new TabControl { Dock = DockStyle.Fill, Padding = new Point(18, 8) };
            tabs.TabPages.Add(BuildNodeTab());
            tabs.TabPages.Add(BuildWalletTab());
            tabs.TabPages.Add(BuildSolanaTab());
            tabs.TabPages.Add(BuildAddressesTab());
            tabs.TabPages.Add(BuildExplorerTab());
            tabs.TabPages.Add(BuildMiningTab());
            tabs.TabPages.Add(BuildPoolMiningTab());
            return tabs;
        }

        private TabPage BuildNodeTab()
        {
            TabPage page = new TabPage("Node");
            TableLayoutPanel root = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(20), ColumnCount = 1, RowCount = 4 };
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 55));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 105));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 112));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

            FlowLayoutPanel controls = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.LeftToRight, WrapContents = false };
            startNodeButton = PrimaryButton(NativeMiningAuthorized ? "Start Node" : "Offline QA node", StartNode);
            startNodeButton.Enabled = NativeMiningAuthorized;
            startNodeButton.AccessibleDescription =
                "Before launch, only an explicitly selected private offline test node may start.";
            stopNodeButton = SecondaryButton("Stop", StopNode);
            stopNodeButton.Enabled = false;
            nodeState = Badge("Stopped", Color.FromArgb(110, 118, 130));
            controls.Controls.Add(startNodeButton);
            controls.Controls.Add(stopNodeButton);
            controls.Controls.Add(nodeState);

            TableLayoutPanel stats = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 4, RowCount = 1 };
            for (int i = 0; i < 4; i++) stats.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            heightValue = Stat(stats, 0, "HEIGHT");
            peersValue = Stat(stats, 1, "PEERS");
            syncValue = Stat(stats, 2, "SYNC");
            hashValue = Stat(stats, 3, "LATEST BLOCK");

            TableLayoutPanel peerPanel = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 3 };
            peerPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 150));
            peerPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            peerPanel.Controls.Add(new Label { Text = "Exclusive peer", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 0);
            peerBox = new TextBox { Dock = DockStyle.Fill, Enabled = NativeMiningAuthorized };
            peerPanel.Controls.Add(peerBox, 1, 0);
            peerPanel.Controls.Add(new Label { Text = "Leave blank to reuse saved peers. A new installation needs a known ForgeCoin peer. Changes apply after restart.", ForeColor = Color.DimGray, AutoSize = true }, 1, 1);
            bootstrapModeBox = new CheckBox { Text = "Private offline node QA only — mining is launch-locked", AutoSize = true, ForeColor = Color.FromArgb(145, 68, 20), Font = new Font("Segoe UI Semibold", 9.5F), Padding = new Padding(0, 4, 0, 0) };
            bootstrapModeBox.CheckedChanged += delegate
            {
                if (!IsRunning(daemon))
                    startNodeButton.Enabled = NativeMiningAuthorized || bootstrapModeBox.Checked;
            };
            peerPanel.Controls.Add(bootstrapModeBox, 1, 2);

            logBox = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, BackColor = Color.FromArgb(18, 21, 28), ForeColor = Color.FromArgb(211, 216, 227), Font = new Font("Consolas", 9F), BorderStyle = BorderStyle.None };
            root.Controls.Add(controls, 0, 0);
            root.Controls.Add(stats, 0, 1);
            root.Controls.Add(peerPanel, 0, 2);
            root.Controls.Add(logBox, 0, 3);
            page.Controls.Add(root);
            return page;
        }

        private TabPage BuildWalletTab()
        {
            TabPage page = new TabPage("Wallet");
            TableLayoutPanel root = new TableLayoutPanel { Name = "WalletPageLayout", Dock = DockStyle.Fill, AutoScroll = true, AutoScrollMinSize = new Size(0, 635), Padding = new Padding(20), ColumnCount = 1, RowCount = 5 };
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 194));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 100));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 100));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 155));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

            GroupBox openGroup = new GroupBox { Text = "Wallet file", Dock = DockStyle.Fill };
            TableLayoutPanel openGrid = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(10), ColumnCount = 6, RowCount = 3 };
            openGrid.RowStyles.Add(new RowStyle(SizeType.Absolute, 52));
            openGrid.RowStyles.Add(new RowStyle(SizeType.Absolute, 52));
            openGrid.RowStyles.Add(new RowStyle(SizeType.Absolute, 49));
            openGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 95));
            openGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 35));
            openGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 85));
            openGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 35));
            openGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 135));
            openGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 135));
            openGrid.Controls.Add(new Label { Text = "Name", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 0);
            walletNameBox = new TextBox { Dock = DockStyle.Fill, Text = "forge-wallet" };
            openGrid.Controls.Add(walletNameBox, 1, 0);
            openGrid.Controls.Add(new Label { Text = "Password", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 2, 0);
            passwordBox = new TextBox { Dock = DockStyle.Fill, UseSystemPasswordChar = true };
            openGrid.Controls.Add(passwordBox, 3, 0);
            createWalletButton = PrimaryButton("Create", CreateWallet);
            openWalletButton = SecondaryButton("Open", OpenWallet);
            openGrid.Controls.Add(createWalletButton, 4, 0);
            openGrid.Controls.Add(openWalletButton, 5, 0);
            walletState = new Label { Text = "Wallet service stopped", ForeColor = Color.DimGray, Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft };
            openGrid.SetColumnSpan(walletState, 4);
            openGrid.Controls.Add(walletState, 0, 1);
            closeWalletButton = SecondaryButton("Close wallet", CloseWallet);
            closeWalletButton.Enabled = false;
            openGrid.Controls.Add(closeWalletButton, 4, 1);
            seedButton = SecondaryButton("Recovery seed", ShowRecoverySeed);
            seedButton.Enabled = false;
            openGrid.Controls.Add(seedButton, 5, 1);
            Label restoreHint = new Label { Text = "Private QA only: recover a disposable 25-word native wallet. Never paste a funded seed into a preview.", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft, ForeColor = Color.DarkRed };
            openGrid.Controls.Add(restoreHint, 0, 2);
            openGrid.SetColumnSpan(restoreHint, 4);
            restoreWalletButton = SecondaryButton("Restore 25 words", RestoreWallet);
            openGrid.Controls.Add(restoreWalletButton, 4, 2);
            openGrid.SetColumnSpan(restoreWalletButton, 2);
            openGroup.Controls.Add(openGrid);

            TableLayoutPanel balances = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 1 };
            balances.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
            balances.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
            balanceValue = Stat(balances, 0, "BALANCE (FRG)");
            unlockedValue = Stat(balances, 1, "AVAILABLE (FRG)");

            GroupBox receiveGroup = new GroupBox { Text = "Receive", Dock = DockStyle.Fill };
            addressBox = new TextBox { Dock = DockStyle.Fill, ReadOnly = true, Multiline = true, Font = new Font("Consolas", 9.5F), Text = "Open a wallet to view its address." };
            receiveGroup.Controls.Add(addressBox);

            GroupBox sendGroup = new GroupBox { Text = "Send", Dock = DockStyle.Fill };
            TableLayoutPanel sendGrid = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(10), ColumnCount = 3, RowCount = 3 };
            sendGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 95));
            sendGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            sendGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 120));
            sendGrid.Controls.Add(new Label { Text = "Address", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 0);
            sendAddressBox = new TextBox { Dock = DockStyle.Fill };
            sendGrid.Controls.Add(sendAddressBox, 1, 0);
            sendGrid.SetColumnSpan(sendAddressBox, 2);
            sendGrid.Controls.Add(new Label { Text = "Amount (FRG)", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 1);
            sendAmountBox = new TextBox { Dock = DockStyle.Fill };
            sendGrid.Controls.Add(sendAmountBox, 1, 1);
            sendButton = PrimaryButton("Send", SendFunds);
            sendButton.Enabled = false;
            sendGrid.Controls.Add(sendButton, 2, 1);
            Label sendNote = new Label { Text = "Transactions use the wallet's default fee and ring settings.", ForeColor = Color.DimGray, Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft };
            sendGrid.Controls.Add(sendNote, 1, 2);
            sendGrid.SetColumnSpan(sendNote, 2);
            sendGroup.Controls.Add(sendGrid);

            Label storage = new Label { Text = "Wallets and blockchain data are stored in: " + appRoot, Dock = DockStyle.Fill, ForeColor = Color.DimGray, TextAlign = ContentAlignment.MiddleLeft };
            root.Controls.Add(openGroup, 0, 0);
            root.Controls.Add(balances, 0, 1);
            root.Controls.Add(receiveGroup, 0, 2);
            root.Controls.Add(sendGroup, 0, 3);
            root.Controls.Add(storage, 0, 4);
            page.Controls.Add(root);
            return page;
        }

        private TabPage BuildAddressesTab()
        {
            TabPage page = new TabPage("Addresses");
            TableLayoutPanel root = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(16), ColumnCount = 1, RowCount = 2 };
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 52));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 48));

            GroupBox receiveGroup = new GroupBox { Text = "Receive addresses", Dock = DockStyle.Fill };
            TableLayoutPanel receiveLayout = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(8), ColumnCount = 1, RowCount = 2 };
            receiveLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 52));
            receiveLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            FlowLayoutPanel receiveActions = new FlowLayoutPanel { Dock = DockStyle.Fill, WrapContents = false };
            receiveActions.Controls.Add(new Label { Text = "Label", AutoSize = true, Padding = new Padding(0, 12, 4, 0) });
            receiveLabelBox = new TextBox { Width = 230, Margin = new Padding(4, 9, 8, 4) };
            receiveActions.Controls.Add(receiveLabelBox);
            receiveActions.Controls.Add(PrimaryButton("New Address", GenerateReceiveAddress));
            receiveActions.Controls.Add(SecondaryButton("Copy Selected", CopyReceiveAddress));
            receiveAddressGrid = MakeGrid();
            receiveAddressGrid.Columns.Add("Index", "#");
            receiveAddressGrid.Columns.Add("Label", "Label");
            receiveAddressGrid.Columns.Add("Address", "ForgeCoin address");
            receiveAddressGrid.Columns.Add("Used", "Used");
            receiveAddressGrid.Columns[0].FillWeight = 10;
            receiveAddressGrid.Columns[1].FillWeight = 25;
            receiveAddressGrid.Columns[2].FillWeight = 100;
            receiveAddressGrid.Columns[3].FillWeight = 12;
            receiveAddressGrid.CellDoubleClick += delegate { CopyReceiveAddress(null, EventArgs.Empty); };
            receiveLayout.Controls.Add(receiveActions, 0, 0);
            receiveLayout.Controls.Add(receiveAddressGrid, 0, 1);
            receiveGroup.Controls.Add(receiveLayout);

            GroupBox contactsGroup = new GroupBox { Text = "Saved recipients", Dock = DockStyle.Fill };
            TableLayoutPanel contactsLayout = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(8), ColumnCount = 1, RowCount = 2 };
            contactsLayout.RowCount = 3;
            contactsLayout.RowStyles.Clear();
            contactsLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 42));
            contactsLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 52));
            contactsLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            FlowLayoutPanel contactFields = new FlowLayoutPanel { Dock = DockStyle.Fill, WrapContents = false };
            contactNameBox = new TextBox { Width = 150, Margin = new Padding(4, 9, 4, 4) };
            contactAddressBox = new TextBox { Width = 540, Margin = new Padding(4, 9, 8, 4) };
            contactFields.Controls.Add(new Label { Text = "Name", AutoSize = true, Padding = new Padding(0, 12, 2, 0) });
            contactFields.Controls.Add(contactNameBox);
            contactFields.Controls.Add(new Label { Text = "Address", AutoSize = true, Padding = new Padding(4, 12, 2, 0) });
            contactFields.Controls.Add(contactAddressBox);
            FlowLayoutPanel contactButtons = new FlowLayoutPanel { Dock = DockStyle.Fill, WrapContents = false };
            contactButtons.Controls.Add(PrimaryButton("Save Contact", SaveContact));
            contactButtons.Controls.Add(SecondaryButton("Use for Send", UseContactForSend));
            contactButtons.Controls.Add(SecondaryButton("Delete", DeleteContact));
            contactGrid = MakeGrid();
            contactGrid.Columns.Add("Index", "#");
            contactGrid.Columns.Add("Name", "Name");
            contactGrid.Columns.Add("Address", "ForgeCoin address");
            contactGrid.Columns[0].FillWeight = 10;
            contactGrid.Columns[1].FillWeight = 28;
            contactGrid.Columns[2].FillWeight = 100;
            contactGrid.CellDoubleClick += delegate { UseContactForSend(null, EventArgs.Empty); };
            contactsLayout.Controls.Add(contactFields, 0, 0);
            contactsLayout.Controls.Add(contactButtons, 0, 1);
            contactsLayout.Controls.Add(contactGrid, 0, 2);
            contactsGroup.Controls.Add(contactsLayout);

            root.Controls.Add(receiveGroup, 0, 0);
            root.Controls.Add(contactsGroup, 0, 1);
            page.Controls.Add(root);
            return page;
        }

        private DataGridView MakeGrid()
        {
            return new DataGridView {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                AllowUserToAddRows = false,
                AllowUserToDeleteRows = false,
                AllowUserToResizeRows = false,
                MultiSelect = false,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                RowHeadersVisible = false,
                BackgroundColor = Color.White,
                BorderStyle = BorderStyle.FixedSingle
            };
        }

        private TabPage BuildExplorerTab()
        {
            TabPage page = new TabPage("Explorer");
            TableLayoutPanel root = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(16), ColumnCount = 1, RowCount = 4 };
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 105));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 245));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 56));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

            TableLayoutPanel stats = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 4, RowCount = 1 };
            for (int i = 0; i < 4; i++) stats.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            explorerHeightValue = Stat(stats, 0, "CHAIN HEIGHT");
            explorerDifficultyValue = Stat(stats, 1, "DIFFICULTY");
            explorerNetworkRateValue = Stat(stats, 2, "NETWORK HASH RATE");
            explorerPoolValue = Stat(stats, 3, "PENDING TXS");

            GroupBox blocksGroup = new GroupBox { Text = "Recent blocks from this computer's ForgeCoin node", Dock = DockStyle.Fill };
            TableLayoutPanel blocksLayout = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(8), ColumnCount = 1, RowCount = 2 };
            blocksLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 36));
            blocksLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            explorerStatusLabel = new Label { Text = "Start the node to browse the blockchain locally.", Dock = DockStyle.Fill, ForeColor = Color.DimGray, TextAlign = ContentAlignment.MiddleLeft };
            explorerBlockGrid = MakeGrid();
            explorerBlockGrid.Columns.Add("Height", "Height");
            explorerBlockGrid.Columns.Add("Age", "Age");
            explorerBlockGrid.Columns.Add("Transactions", "TXs");
            explorerBlockGrid.Columns.Add("Reward", "Reward (FRG)");
            explorerBlockGrid.Columns.Add("Difficulty", "Difficulty");
            explorerBlockGrid.Columns.Add("Size", "Size");
            explorerBlockGrid.Columns.Add("Hash", "Block hash");
            explorerBlockGrid.Columns[0].FillWeight = 16;
            explorerBlockGrid.Columns[1].FillWeight = 16;
            explorerBlockGrid.Columns[2].FillWeight = 10;
            explorerBlockGrid.Columns[3].FillWeight = 18;
            explorerBlockGrid.Columns[4].FillWeight = 22;
            explorerBlockGrid.Columns[5].FillWeight = 14;
            explorerBlockGrid.Columns[6].FillWeight = 55;
            explorerBlockGrid.CellDoubleClick += delegate
            {
                if (explorerBlockGrid.SelectedRows.Count == 0) return;
                explorerLookupBox.Text = Convert.ToString(explorerBlockGrid.SelectedRows[0].Cells["Hash"].Value);
                SearchExplorer(null, EventArgs.Empty);
            };
            blocksLayout.Controls.Add(explorerStatusLabel, 0, 0);
            blocksLayout.Controls.Add(explorerBlockGrid, 0, 1);
            blocksGroup.Controls.Add(blocksLayout);

            FlowLayoutPanel search = new FlowLayoutPanel { Dock = DockStyle.Fill, WrapContents = false };
            search.Controls.Add(new Label { Text = "Block height, block hash, or transaction ID", AutoSize = true, Padding = new Padding(0, 13, 6, 0) });
            explorerLookupBox = new TextBox { Width = 330, Margin = new Padding(4, 10, 8, 4) };
            explorerLookupBox.KeyDown += delegate(object sender, KeyEventArgs e) { if (e.KeyCode == Keys.Enter) { SearchExplorer(sender, EventArgs.Empty); e.SuppressKeyPress = true; } };
            search.Controls.Add(explorerLookupBox);
            search.Controls.Add(PrimaryButton("Search", SearchExplorer));
            search.Controls.Add(SecondaryButton("Refresh", delegate { RefreshExplorer(); }));

            explorerResultBox = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, BackColor = Color.White, ForeColor = Color.FromArgb(29, 33, 43), Font = new Font("Consolas", 9.5F), BorderStyle = BorderStyle.FixedSingle, Text = "Searches use only the local ForgeCoin daemon. Sender, recipient, and transfer amounts remain private by protocol." };

            root.Controls.Add(stats, 0, 0);
            root.Controls.Add(blocksGroup, 0, 1);
            root.Controls.Add(search, 0, 2);
            root.Controls.Add(explorerResultBox, 0, 3);
            page.Controls.Add(root);
            return page;
        }

        private void RefreshExplorer()
        {
            try
            {
                IDictionary info = Rpc("http://127.0.0.1:39481/json_rpc", "get_info", new Dictionary<string, object>());
                long height = info.Contains("height") ? ToLong(info["height"]) : 0;
                double difficulty = info.Contains("difficulty") ? Convert.ToDouble(info["difficulty"], CultureInfo.InvariantCulture) : 0;
                double target = info.Contains("target") ? Math.Max(1, Convert.ToDouble(info["target"], CultureInfo.InvariantCulture)) : 120;
                long poolSize = info.Contains("tx_pool_size") ? ToLong(info["tx_pool_size"]) : 0;
                bool synchronized = info.Contains("synchronized") && Convert.ToBoolean(info["synchronized"], CultureInfo.InvariantCulture);

                explorerHeightValue.Text = height.ToString("N0", CultureInfo.InvariantCulture);
                explorerDifficultyValue.Text = difficulty.ToString("N0", CultureInfo.InvariantCulture);
                explorerNetworkRateValue.Text = FormatRate(difficulty / target);
                explorerPoolValue.Text = poolSize.ToString("N0", CultureInfo.InvariantCulture);
                explorerStatusLabel.Text = (synchronized ? "Synchronized" : "Local chain") + " • Each wallet verifies this data through its own node • Updated " + DateTime.Now.ToString("HH:mm:ss");
                explorerStatusLabel.ForeColor = synchronized ? Color.FromArgb(40, 125, 78) : Color.FromArgb(145, 91, 20);

                explorerBlockGrid.Rows.Clear();
                if (height <= 0) return;
                long end = height - 1;
                long start = Math.Max(0, end - 9);
                IDictionary range = Rpc("http://127.0.0.1:39481/json_rpc", "get_block_headers_range", new Dictionary<string, object> { { "start_height", start }, { "end_height", end } });
                IEnumerable headers = range.Contains("headers") ? range["headers"] as IEnumerable : null;
                if (headers == null) return;
                List<IDictionary> ordered = new List<IDictionary>();
                foreach (object item in headers)
                {
                    IDictionary header = item as IDictionary;
                    if (header != null) ordered.Add(header);
                }
                ordered.Sort(delegate(IDictionary a, IDictionary b) { return ToLong(b["height"]).CompareTo(ToLong(a["height"])); });
                foreach (IDictionary header in ordered)
                {
                    long timestamp = header.Contains("timestamp") ? ToLong(header["timestamp"]) : 0;
                    long txCount = header.Contains("num_txes") ? ToLong(header["num_txes"]) + 1 : 1;
                    long reward = header.Contains("reward") ? ToLong(header["reward"]) : 0;
                    string diff = header.Contains("difficulty") ? Convert.ToDouble(header["difficulty"], CultureInfo.InvariantCulture).ToString("N0", CultureInfo.InvariantCulture) : "—";
                    long size = header.Contains("block_size") ? ToLong(header["block_size"]) : 0;
                    explorerBlockGrid.Rows.Add(
                        ToLong(header["height"]).ToString("N0", CultureInfo.InvariantCulture),
                        FormatAge(timestamp),
                        txCount.ToString(CultureInfo.InvariantCulture),
                        FormatCoin(reward),
                        diff,
                        FormatBytes(size),
                        header.Contains("hash") ? Convert.ToString(header["hash"]) : "");
                }
            }
            catch (Exception ex)
            {
                explorerStatusLabel.Text = "Local explorer unavailable • Start or reconnect the ForgeCoin node • " + ex.Message;
                explorerStatusLabel.ForeColor = Color.DimGray;
                explorerHeightValue.Text = "—";
                explorerDifficultyValue.Text = "—";
                explorerNetworkRateValue.Text = "—";
                explorerPoolValue.Text = "—";
            }
        }

        private void SearchExplorer(object sender, EventArgs e)
        {
            try
            {
                string query = explorerLookupBox.Text.Trim();
                if (query.Length == 0) throw new InvalidOperationException("Enter a block height, block hash, or transaction ID.");
                long height;
                if (long.TryParse(query, NumberStyles.None, CultureInfo.InvariantCulture, out height))
                {
                    if (height < 0) throw new InvalidOperationException("Block height cannot be negative.");
                    ShowExplorerBlock(new Dictionary<string, object> { { "height", height } });
                    return;
                }
                if (query.Length != 64) throw new InvalidOperationException("A block or transaction hash must contain 64 hexadecimal characters.");
                for (int i = 0; i < query.Length; i++) if (!Uri.IsHexDigit(query[i])) throw new InvalidOperationException("The hash contains a character that is not hexadecimal.");
                try
                {
                    ShowExplorerBlock(new Dictionary<string, object> { { "hash", query.ToLowerInvariant() } });
                }
                catch
                {
                    ShowExplorerTransaction(query.ToLowerInvariant());
                }
            }
            catch (Exception ex)
            {
                explorerResultBox.Text = "Lookup failed: " + ex.Message;
            }
        }

        private void ShowExplorerBlock(IDictionary<string, object> parameters)
        {
            IDictionary result = Rpc("http://127.0.0.1:39481/json_rpc", "get_block", parameters);
            IDictionary header = result.Contains("block_header") ? result["block_header"] as IDictionary : null;
            if (header == null) throw new InvalidOperationException("The local node did not return that block.");
            IDictionary info = Rpc("http://127.0.0.1:39481/json_rpc", "get_info", new Dictionary<string, object>());
            long chainHeight = info.Contains("height") ? ToLong(info["height"]) : 0;
            long blockHeight = header.Contains("height") ? ToLong(header["height"]) : 0;
            long timestamp = header.Contains("timestamp") ? ToLong(header["timestamp"]) : 0;
            long reward = header.Contains("reward") ? ToLong(header["reward"]) : 0;
            long txCount = header.Contains("num_txes") ? ToLong(header["num_txes"]) + 1 : 1;
            long confirmations = Math.Max(0, chainHeight - blockHeight);

            StringBuilder text = new StringBuilder();
            text.AppendLine("BLOCK");
            text.AppendLine("Height:         " + blockHeight.ToString("N0", CultureInfo.InvariantCulture));
            text.AppendLine("Confirmations:  " + confirmations.ToString("N0", CultureInfo.InvariantCulture));
            text.AppendLine("Hash:           " + Field(header, "hash"));
            text.AppendLine("Previous block: " + Field(header, "prev_hash"));
            text.AppendLine("Timestamp:      " + FormatTimestamp(timestamp) + " (" + FormatAge(timestamp) + ")");
            text.AppendLine("Difficulty:     " + NumberField(header, "difficulty"));
            text.AppendLine("Reward:         " + FormatCoin(reward) + " FRG");
            text.AppendLine("Transactions:   " + txCount.ToString(CultureInfo.InvariantCulture) + " including the miner transaction");
            text.AppendLine("Block size:     " + FormatBytes(header.Contains("block_size") ? ToLong(header["block_size"]) : 0));
            text.AppendLine("Nonce:          " + Field(header, "nonce"));
            text.AppendLine("Version:        " + Field(header, "major_version") + "." + Field(header, "minor_version"));
            if (result.Contains("tx_hashes"))
            {
                IEnumerable hashes = result["tx_hashes"] as IEnumerable;
                if (hashes != null)
                {
                    text.AppendLine();
                    text.AppendLine("NON-MINER TRANSACTION IDS");
                    foreach (object hash in hashes) text.AppendLine(Convert.ToString(hash));
                }
            }
            explorerResultBox.Text = text.ToString();
        }

        private void ShowExplorerTransaction(string hash)
        {
            ArrayList hashes = new ArrayList { hash };
            IDictionary result = RestRpc("http://127.0.0.1:39481/get_transactions", new Dictionary<string, object> { { "txs_hashes", hashes }, { "decode_as_json", true }, { "prune", true } });
            IEnumerable txs = result.Contains("txs") ? result["txs"] as IEnumerable : null;
            IDictionary tx = null;
            if (txs != null) foreach (object item in txs) { tx = item as IDictionary; if (tx != null) break; }
            if (tx == null) throw new InvalidOperationException("No block or transaction with that hash exists in the local node.");

            bool inPool = tx.Contains("in_pool") && Convert.ToBoolean(tx["in_pool"], CultureInfo.InvariantCulture);
            long blockHeight = tx.Contains("block_height") ? ToLong(tx["block_height"]) : 0;
            long timestamp = tx.Contains("block_timestamp") ? ToLong(tx["block_timestamp"]) : 0;
            IDictionary info = Rpc("http://127.0.0.1:39481/json_rpc", "get_info", new Dictionary<string, object>());
            long chainHeight = info.Contains("height") ? ToLong(info["height"]) : 0;
            long confirmations = inPool ? 0 : Math.Max(0, chainHeight - blockHeight);
            long fee = 0;
            int inputs = 0;
            int outputs = 0;
            string version = "—";
            string unlockTime = "—";
            if (tx.Contains("as_json"))
            {
                IDictionary decoded = json.DeserializeObject(Convert.ToString(tx["as_json"])) as IDictionary;
                if (decoded != null)
                {
                    inputs = decoded.Contains("vin") ? CountItems(decoded["vin"] as IEnumerable) : 0;
                    outputs = decoded.Contains("vout") ? CountItems(decoded["vout"] as IEnumerable) : 0;
                    version = Field(decoded, "version");
                    unlockTime = Field(decoded, "unlock_time");
                    IDictionary signatures = decoded.Contains("rct_signatures") ? decoded["rct_signatures"] as IDictionary : null;
                    if (signatures != null && signatures.Contains("txnFee")) fee = ToLong(signatures["txnFee"]);
                }
            }
            long bytes = tx.Contains("as_hex") ? Convert.ToString(tx["as_hex"]).Length / 2 : 0;
            StringBuilder text = new StringBuilder();
            text.AppendLine("TRANSACTION");
            text.AppendLine("Transaction ID: " + (tx.Contains("tx_hash") ? Convert.ToString(tx["tx_hash"]) : hash));
            text.AppendLine("Status:         " + (inPool ? "Pending in transaction pool" : "Mined in block " + blockHeight.ToString("N0", CultureInfo.InvariantCulture)));
            text.AppendLine("Confirmations:  " + confirmations.ToString("N0", CultureInfo.InvariantCulture));
            if (!inPool) text.AppendLine("Timestamp:      " + FormatTimestamp(timestamp) + " (" + FormatAge(timestamp) + ")");
            text.AppendLine("Fee:            " + FormatCoin(fee) + " FRG");
            text.AppendLine("Size:           " + FormatBytes(bytes));
            text.AppendLine("Inputs:         " + inputs.ToString(CultureInfo.InvariantCulture));
            text.AppendLine("Outputs:        " + outputs.ToString(CultureInfo.InvariantCulture));
            text.AppendLine("Version:        " + version);
            text.AppendLine("Unlock time:    " + unlockTime);
            text.AppendLine("Double spend:   " + (tx.Contains("double_spend_seen") && Convert.ToBoolean(tx["double_spend_seen"], CultureInfo.InvariantCulture) ? "Reported" : "No"));
            text.AppendLine();
            text.AppendLine("Sender, recipient, and transferred amount are private and are not available to a public explorer.");
            explorerResultBox.Text = text.ToString();
        }

        private TabPage BuildMiningTab()
        {
            TabPage page = new TabPage("Mining");
            TableLayoutPanel root = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(20), ColumnCount = 1, RowCount = 5 };
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 115));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 185));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 65));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 112));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

            GroupBox destinationGroup = new GroupBox { Text = "Mining payout", Dock = DockStyle.Fill };
            TableLayoutPanel destinationGrid = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(10), ColumnCount = 2, RowCount = 2 };
            destinationGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 135));
            destinationGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            destinationGrid.Controls.Add(new Label { Text = "Wallet address", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 0);
            miningAddressBox = new TextBox { Dock = DockStyle.Fill };
            destinationGrid.Controls.Add(miningAddressBox, 1, 0);
            destinationGrid.Controls.Add(new Label { Text = "Open a wallet to fill this automatically, or paste another ForgeCoin address.", AutoSize = true, ForeColor = Color.DimGray }, 1, 1);
            destinationGroup.Controls.Add(destinationGrid);

            TableLayoutPanel stats = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 4, RowCount = 2 };
            for (int i = 0; i < 4; i++) stats.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            stats.RowStyles.Add(new RowStyle(SizeType.Percent, 50));
            stats.RowStyles.Add(new RowStyle(SizeType.Percent, 50));
            hashRateValue = StatAt(stats, 0, 0, "LOCAL HASH RATE (H/S)");
            miningNetworkRateValue = StatAt(stats, 1, 0, "NETWORK HASH RATE");
            miningDifficultyValue = StatAt(stats, 2, 0, "DIFFICULTY");
            miningBlockHeightValue = StatAt(stats, 3, 0, "BLOCK HEIGHT");
            miningRewardValue = StatAt(stats, 0, 1, "BLOCK REWARD (FRG)");
            miningTargetValue = StatAt(stats, 1, 1, "TARGET TIME");
            miningThreadsValue = StatAt(stats, 2, 1, "ACTIVE THREADS");
            miningBlocksFoundValue = StatAt(stats, 3, 1, "BLOCKS FOUND THIS RUN");

            TableLayoutPanel controls = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 5, RowCount = 1, Margin = new Padding(0) };
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 100));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 80));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 145));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 145));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            controls.Controls.Add(new Label { Text = "CPU threads", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 0);
            miningThreads = new NumericUpDown { Minimum = 1, Maximum = Math.Max(1, Environment.ProcessorCount), Value = Math.Max(1, Environment.ProcessorCount / 2), Dock = DockStyle.Fill, Margin = new Padding(4, 12, 8, 10) };
            controls.Controls.Add(miningThreads, 1, 0);
            startMiningButton = PrimaryButton("Start Mining", StartMining);
            startMiningButton.Enabled = NativeMiningAuthorized;
            startMiningButton.Text = NativeMiningAuthorized ? "Start Mining" : "Launch locked";
#if FRG_PRIVATE_MINING_QA
            startMiningButton.Text = "QA SOLO ONLY";
#endif
            startMiningButton.AccessibleDescription = "Solo mainnet mining requires an explicitly approved network launch.";
            stopMiningButton = SecondaryButton("Stop", StopMining);
            stopMiningButton.Enabled = false;
            miningState = Badge("Stopped", Color.FromArgb(110, 118, 130));
            startMiningButton.Dock = DockStyle.Fill;
            stopMiningButton.Dock = DockStyle.Fill;
            miningState.AutoSize = false; miningState.Dock = DockStyle.Fill; miningState.TextAlign = ContentAlignment.MiddleCenter; miningState.Margin = new Padding(12, 8, 5, 8);
            controls.Controls.Add(startMiningButton, 2, 0); controls.Controls.Add(stopMiningButton, 3, 0); controls.Controls.Add(miningState, 4, 0);

            TableLayoutPanel monitorPanel = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 2, Margin = new Padding(0) };
            monitorPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 50));
            monitorPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 50));
            miningNodeDetailLabel = new Label { Dock = DockStyle.Fill, AutoSize = false, Text = "Node monitor: stopped", BackColor = Color.FromArgb(225, 235, 250), ForeColor = Color.FromArgb(35, 58, 92), Font = new Font("Segoe UI Semibold", 10F), Padding = new Padding(12), TextAlign = ContentAlignment.MiddleLeft, Margin = new Padding(0, 0, 0, 3) };
            miningDetailLabel = new Label { Dock = DockStyle.Fill, AutoSize = false, Text = "Miner monitor: stopped", BackColor = Color.FromArgb(255, 244, 214), ForeColor = Color.FromArgb(85, 60, 10), Font = new Font("Segoe UI Semibold", 10F), Padding = new Padding(12), TextAlign = ContentAlignment.MiddleLeft, Margin = new Padding(0, 3, 0, 0) };
            monitorPanel.Controls.Add(miningNodeDetailLabel, 0, 0);
            monitorPanel.Controls.Add(miningDetailLabel, 0, 1);
            Label implementation = new Label { Dock = DockStyle.Fill, AutoSize = false, Text = "Mining uses ForgeCoin's built-in RandomX CPU miner. Keep the node synchronized with at least one ForgeCoin peer. Higher thread counts increase CPU use, heat, and power consumption.", ForeColor = Color.DimGray, Padding = new Padding(8) };

            root.Controls.Add(destinationGroup, 0, 0);
            root.Controls.Add(stats, 0, 1);
            root.Controls.Add(controls, 0, 2);
            root.Controls.Add(monitorPanel, 0, 3);
            root.Controls.Add(implementation, 0, 4);
            page.Controls.Add(root);
            return page;
        }

        private TabPage BuildPoolMiningTab()
        {
            TabPage page = new TabPage("Pool Mining");
            TableLayoutPanel root = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(16), ColumnCount = 1, RowCount = 4 };
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 155));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 185));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 65));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

            GroupBox settings = new GroupBox { Text = "Future ForgeCoin pool connection", Dock = DockStyle.Fill };
            TableLayoutPanel form = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(10), ColumnCount = 4, RowCount = 3 };
            form.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 110));
            form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 62));
            form.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 105));
            form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 38));
            form.Controls.Add(new Label { Text = "Pool URL", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 0);
            poolUrlBox = new TextBox { Dock = DockStyle.Fill };
            form.Controls.Add(poolUrlBox, 1, 0); form.SetColumnSpan(poolUrlBox, 3);
            form.Controls.Add(new Label { Text = "Wallet / user", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 1);
            poolUserBox = new TextBox { Dock = DockStyle.Fill };
            form.Controls.Add(poolUserBox, 1, 1); form.SetColumnSpan(poolUserBox, 3);
            form.Controls.Add(new Label { Text = "Worker name", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 2);
            poolWorkerBox = new TextBox { Dock = DockStyle.Fill, Text = Environment.MachineName };
            form.Controls.Add(poolWorkerBox, 1, 2);
            form.Controls.Add(new Label { Text = "Pool password", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 2, 2);
            poolPassBox = new TextBox { Dock = DockStyle.Fill, Text = "x" };
            form.Controls.Add(poolPassBox, 3, 2);
            settings.Controls.Add(form);

            TableLayoutPanel stats = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 4, RowCount = 2 };
            for (int i = 0; i < 4; i++) stats.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            stats.RowStyles.Add(new RowStyle(SizeType.Percent, 50));
            stats.RowStyles.Add(new RowStyle(SizeType.Percent, 50));
            poolHashRateValue = StatAt(stats, 0, 0, "HASH RATE (H/S)");
            poolAcceptedValue = StatAt(stats, 1, 0, "ACCEPTED SHARES");
            poolRejectedValue = StatAt(stats, 2, 0, "REJECTED SHARES");
            poolDifficultyValue = StatAt(stats, 3, 0, "SHARE DIFFICULTY");
            poolNameValue = StatAt(stats, 0, 1, "CONNECTED POOL");
            poolPingValue = StatAt(stats, 1, 1, "PING");
            poolUptimeValue = StatAt(stats, 2, 1, "UPTIME");
            poolAlgorithmValue = StatAt(stats, 3, 1, "ALGORITHM");

            TableLayoutPanel controls = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 5, RowCount = 1, Margin = new Padding(0) };
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 100));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 80));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 145));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 145));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            controls.Controls.Add(new Label { Text = "CPU threads", Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft }, 0, 0);
            poolThreads = new NumericUpDown { Minimum = 1, Maximum = Math.Max(1, Environment.ProcessorCount), Value = Math.Max(1, Environment.ProcessorCount / 2), Dock = DockStyle.Fill, Margin = new Padding(4, 12, 8, 10) };
            controls.Controls.Add(poolThreads, 1, 0);
            startPoolButton = PrimaryButton("Start Pool", StartPoolMining);
            startPoolButton.Enabled = NativeMiningAuthorized;
#if FRG_PRIVATE_POOL_QA
            startPoolButton.Enabled = true; // isolated localhost / no CPU or GPU
#endif
            startPoolButton.Text = NativeMiningAuthorized ? "Start Pool" : "Launch locked";
            startPoolButton.AccessibleDescription = "Native pool mining is disabled until launch and payout acceptance.";
            stopPoolButton = SecondaryButton("Stop", StopPoolMining);
            stopPoolButton.Enabled = false;
            poolState = Badge("Stopped", Color.FromArgb(110, 118, 130));
            startPoolButton.Dock = DockStyle.Fill;
            stopPoolButton.Dock = DockStyle.Fill;
            poolState.AutoSize = false; poolState.Dock = DockStyle.Fill; poolState.TextAlign = ContentAlignment.MiddleCenter; poolState.Margin = new Padding(12, 8, 5, 8);
            controls.Controls.Add(startPoolButton, 2, 0); controls.Controls.Add(stopPoolButton, 3, 0); controls.Controls.Add(poolState, 4, 0);

            TableLayoutPanel live = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 2 };
            live.RowStyles.Add(new RowStyle(SizeType.Absolute, 54));
            live.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            poolDetailLabel = new Label { Dock = DockStyle.Fill, Text = "Pool miner status: stopped", BackColor = Color.FromArgb(225, 235, 250), ForeColor = Color.FromArgb(35, 58, 92), Font = new Font("Segoe UI Semibold", 10F), Padding = new Padding(12), TextAlign = ContentAlignment.MiddleLeft };
            poolLogBox = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, BackColor = Color.FromArgb(18, 21, 28), ForeColor = Color.FromArgb(211, 216, 227), Font = new Font("Consolas", 9F), BorderStyle = BorderStyle.None };
            live.Controls.Add(poolDetailLabel, 0, 0); live.Controls.Add(poolLogBox, 0, 1);

            root.Controls.Add(settings, 0, 0);
            root.Controls.Add(stats, 0, 1);
            root.Controls.Add(controls, 0, 2);
            root.Controls.Add(live, 0, 3);
            page.Controls.Add(root);
            return page;
        }

        private Button PrimaryButton(string text, EventHandler click)
        {
            Button b = new Button { Text = text, AutoSize = false, Width = 125, Height = 40, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(29, 112, 217), ForeColor = Color.White, Cursor = Cursors.Hand, Font = new Font("Segoe UI Semibold", 10F), Margin = new Padding(5) };
            b.FlatAppearance.BorderSize = 2;
            b.FlatAppearance.BorderColor = Color.FromArgb(21, 81, 174);
            b.Click += click;
            return b;
        }

        private Button SecondaryButton(string text, EventHandler click)
        {
            Button b = new Button { Text = text, AutoSize = false, Width = 125, Height = 40, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(225, 239, 254), ForeColor = Color.FromArgb(28, 32, 42), Cursor = Cursors.Hand, Font = new Font("Segoe UI Semibold", 10F), Margin = new Padding(5) };
            b.FlatAppearance.BorderSize = 2;
            b.FlatAppearance.BorderColor = Color.FromArgb(98, 149, 204);
            b.Click += click;
            return b;
        }

        private Label Badge(string text, Color color)
        {
            return new Label { Text = text, AutoSize = true, BackColor = color, ForeColor = Color.White, Padding = new Padding(12, 9, 12, 9), Margin = new Padding(12, 0, 0, 0) };
        }

        private Label Stat(TableLayoutPanel parent, int column, string caption)
        {
            return StatAt(parent, column, 0, caption);
        }

        private Label StatAt(TableLayoutPanel parent, int column, int row, string caption)
        {
            Panel p = new Panel { Dock = DockStyle.Fill, Margin = new Padding(5), BackColor = Color.White };
            Label c = new Label { Text = caption, ForeColor = Color.FromArgb(110, 118, 130), Font = new Font("Segoe UI Semibold", 8F), AutoSize = true, Location = new Point(14, 12) };
            Label v = new Label { Text = "—", ForeColor = Color.FromArgb(29, 33, 43), Font = new Font("Segoe UI Semibold", 16F), AutoEllipsis = true, Location = new Point(13, 38), Size = new Size(205, 38) };
            p.Controls.Add(c); p.Controls.Add(v); parent.Controls.Add(p, column, row);
            return v;
        }

        private void StartNode(object sender, EventArgs e)
        {
            if (IsRunning(daemon)) return;
            // Prevent even an outbound public P2P bootstrap from the preview.
            // The operator may run an isolated localhost-only offline node
            // for private testing, but can NEVER begin mainnet mining here.
            if (!NativeMiningAuthorized && !bootstrapModeBox.Checked)
            {
                ShowError("Public FRG node bootstrap is disabled until launch. Choose private offline node QA.");
                return;
            }
            string exe = Path.Combine(binRoot, "forged.exe");
            if (!File.Exists(exe)) { ShowError("The ForgeCoin daemon is missing from the bin folder."); return; }
#if FRG_PRIVATE_MINING_QA
            if (!bootstrapModeBox.Checked)
            {
                ShowError("Isolated mining QA requires explicit offline node selection.");
                return;
            }
            RequirePinnedPrivateQaDaemon(exe);
#endif
            List<string> args = new List<string> {
                "--data-dir", Quote(Path.Combine(appRoot, "blockchain")),
                "--p2p-bind-ip", "127.0.0.1", "--p2p-bind-port", "39480",
                "--rpc-bind-ip", "127.0.0.1", "--rpc-bind-port", "39481",
                "--no-igd", "--no-zmq", "--check-updates", "disabled",
                "--disable-dns-checkpoints", "--non-interactive", "--log-level", "1"
            };
            string peer = peerBox.Text.Trim();
            nodeOfflineMode = bootstrapModeBox.Checked;
            if (nodeOfflineMode)
            {
                args.Add("--offline");
#if FRG_PRIVATE_MINING_QA
                args.Add("--out-peers"); args.Add("0");
                args.Add("--in-peers"); args.Add("0");
                args.Add("--hide-my-port");
#endif
            }
            else if (peer.Length > 0)
            {
                args.Add("--allow-local-ip"); args.Add("--add-exclusive-node"); args.Add(Quote(peer));
            }
            daemon = StartCaptured(exe, string.Join(" ", args.ToArray()), "NODE");
            if (daemon != null)
            {
                nodeState.Text = "Starting"; nodeState.BackColor = Color.FromArgb(205, 139, 36);
                startNodeButton.Enabled = false; stopNodeButton.Enabled = true;
                bootstrapModeBox.Enabled = false; peerBox.Enabled = false;
#if FRG_PRIVATE_MINING_QA
                startMiningButton.Enabled = IsolatedSoloQaReady();
#endif
            }
        }

        private void StopNode(object sender, EventArgs e)
        {
            if (!IsRunning(daemon)) { SetNodeStopped(); return; }
            try { Rpc("http://127.0.0.1:39481/json_rpc", "stop_daemon", new Dictionary<string, object>()); } catch { }
            WaitThenKill(daemon);
            daemon = null;
            SetNodeStopped();
        }

        private void SetNodeStopped()
        {
            nodeState.Text = "Stopped"; nodeState.BackColor = Color.FromArgb(110, 118, 130);
            startNodeButton.Enabled = NativeMiningAuthorized || bootstrapModeBox.Checked; stopNodeButton.Enabled = false;
            bootstrapModeBox.Enabled = true; peerBox.Enabled = NativeMiningAuthorized;
        }

        private void RefreshNode()
        {
            if (Interlocked.Exchange(ref nodeRefreshInFlight, 1) != 0) return;
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    IDictionary result = Rpc("http://127.0.0.1:39481/json_rpc", "get_info", new Dictionary<string, object>());
                    IDictionary header = Rpc("http://127.0.0.1:39481/json_rpc", "get_last_block_header", new Dictionary<string, object>());
                    PostUi(delegate
                    {
                        long height = ToLong(result["height"]);
                        long target = result.Contains("target_height") ? ToLong(result["target_height"]) : 0;
                        long incoming = result.Contains("incoming_connections_count") ? ToLong(result["incoming_connections_count"]) : 0;
                        long outgoing = result.Contains("outgoing_connections_count") ? ToLong(result["outgoing_connections_count"]) : 0;
                        heightValue.Text = height.ToString("N0");
                        peersValue.Text = (incoming + outgoing).ToString(CultureInfo.InvariantCulture);
                        bool synchronized = result.Contains("synchronized") && Convert.ToBoolean(result["synchronized"], CultureInfo.InvariantCulture);
                        bool offline = result.Contains("offline") && Convert.ToBoolean(result["offline"], CultureInfo.InvariantCulture);
                        syncValue.Text = offline ? "Private offline QA" : (synchronized ? "Synchronized" : (target > height ? height.ToString("N0") + " / " + target.ToString("N0") : "Waiting for peer"));
                        nodeState.Text = offline ? "Offline QA node" : "Running";
                        nodeState.BackColor = offline ? Color.FromArgb(176, 112, 32) : Color.FromArgb(53, 145, 92);
                        IDictionary h = header.Contains("block_header") ? header["block_header"] as IDictionary : null;
                        if (h != null && h.Contains("hash")) hashValue.Text = Shorten(Convert.ToString(h["hash"]), 16);
                    });
                }
                catch
                {
                    if (!IsRunning(daemon)) PostUi(SetNodeStopped);
                }
                finally { Interlocked.Exchange(ref nodeRefreshInFlight, 0); }
            });
        }

        private void EnsureWalletService()
        {
            if (IsRunning(walletRpc))
            {
                if (walletSession == null)
                    throw new InvalidOperationException("Wallet service has no authenticated session.");
                return;
            }
            // Never attach to an existing unauthenticated/foreign wallet RPC.
            // A fresh random local Digest identity belongs exclusively to the
            // newly launched native wallet service.
            if (walletSession != null)
            {
                walletSession.Dispose();
                walletSession = null;
            }
            string exe = Path.Combine(binRoot, "forge-wallet-rpc.exe");
            if (!File.Exists(exe))
                throw new FileNotFoundException("The ForgeCoin wallet service is missing.", exe);
            walletSession = WalletRpcSession.Create(Path.Combine(appRoot, "rpc-private"));
            try
            {
                string args = "--wallet-dir " + Quote(Path.Combine(appRoot, "wallets")) +
                    " --rpc-bind-ip 127.0.0.1 --rpc-bind-port 39484" +
                    " --config-file " + Quote(walletSession.ConfigFile) +
                    " --daemon-address 127.0.0.1:39481 --no-dns --no-initial-sync" +
                    " --shared-ringdb-dir " + Quote(Path.Combine(appRoot, "ringdb")) +
                    " --log-level 0 --log-file " + Quote(Path.Combine(appRoot, "logs", "wallet-rpc.log"));
                walletRpc = StartCaptured(exe, args, "WALLET");
#if FRG_PRIVATE_UI_QA
                Console.WriteLine("QA_GUI: wallet process start attempted");
#endif
                if (walletRpc == null)
                    throw new InvalidOperationException("Native wallet RPC process could not be started.");
                for (int i = 0; i < 35; i++)
                {
                    if (!IsRunning(walletRpc))
                        throw new InvalidOperationException("Native wallet RPC process exited.");
                    Thread.Sleep(175);
                    try
                    {
                        IDictionary version = Rpc("http://127.0.0.1:39484/json_rpc",
                            "get_version", new Dictionary<string, object>(), 2000);
                        if (version != null)
                        {
                            // A successful authenticated Digest request is
                            // mandatory before the private config is removed.
                            walletSession.DeleteStartupConfig();
#if FRG_PRIVATE_UI_QA
                            Console.WriteLine("QA_GUI: authenticated native wallet RPC ready");
#endif
                            return;
                        }
                    }
                    catch { /* readiness only; never display wallet RPC payload */ }
                }
                throw new InvalidOperationException("Authenticated native wallet RPC did not become ready.");
            }
            catch
            {
                if (IsRunning(walletRpc))
                    try { walletRpc.Kill(); walletRpc.WaitForExit(3000); } catch { }
                walletRpc = null;
                walletSession.Dispose();
                walletSession = null;
                throw new InvalidOperationException(
                    "Could not start a private authenticated native FRG wallet service.");
            }
        }

        private void CreateWallet(object sender, EventArgs e)
        {
            try
            {
                string name = ValidWalletName();
                RequireNewWalletPassword();
                if (WalletFileAlreadyExists(name))
                    throw new InvalidOperationException("The wallet file already exists. Use Open instead of overwriting it.");
                EnsureWalletService();
                Dictionary<string, object> p = new Dictionary<string, object> { { "filename", name }, { "password", passwordBox.Text }, { "language", "English" } };
                // Native encrypted wallet creation is disk-heavy and may
                // exceed the 2-second status-poll timeout on a cold system.
                Rpc("http://127.0.0.1:39484/json_rpc", "create_wallet", p, 15000);
#if FRG_PRIVATE_UI_QA
                Console.WriteLine("QA_GUI: native wallet creation RPC accepted");
#endif
                WalletOpened("Created " + name);
#if FRG_PRIVATE_UI_QA
                Console.WriteLine("QA_GUI: wallet open refresh completed");
#endif
                ShowRecoverySeed(null, EventArgs.Empty);
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private void RestoreWallet(object sender, EventArgs e)
        {
            // Explicit private QA operation only. Ask the native RPC to scan
            // from genesis rather than reusing any prior restore height.
            // No mnemonic is saved to settings, disk, logs, UI status or error.
            try
            {
                if (walletOpen) throw new InvalidOperationException("Close the current wallet before restoring.");
                string name = ValidWalletName();
                RequireNewWalletPassword();
                if (WalletFileAlreadyExists(name))
                    throw new InvalidOperationException("This wallet file already exists. Choose a new name; existing wallets are never overwritten.");
                EnsureWalletService(); // refuse missing native RPC before requesting a seed
                using (Form dialog = new Form {
                    Text = "Restore a disposable FRG test wallet", Size = new Size(760, 290),
                    StartPosition = FormStartPosition.CenterParent, MinimizeBox = false,
                    MaximizeBox = false, FormBorderStyle = FormBorderStyle.FixedDialog
                })
                {
                    TableLayoutPanel layout = new TableLayoutPanel {
                        Dock = DockStyle.Fill, Padding = new Padding(18),
                        ColumnCount = 1, RowCount = 4
                    };
                    layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 66));
                    layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 45));
                    layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 38));
                    layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
                    layout.Controls.Add(new Label {
                        Dock = DockStyle.Fill, ForeColor = Color.DarkRed,
                        Text = "PRELAUNCH PRIVATE QA ONLY. Do not restore a wallet containing real funds.\nOnly disposable native FRG test seeds are appropriate here."
                    }, 0, 0);
                    TextBox seedInput = new TextBox {
                        Dock = DockStyle.Fill, UseSystemPasswordChar = true,
                        AccessibleName = "Twenty-five English native wallet recovery words"
                    };
                    layout.Controls.Add(seedInput, 0, 1);
                    CheckBox show = new CheckBox {
                        Text = "Temporarily show recovery words", Dock = DockStyle.Fill,
                        AccessibleName = "Show or conceal the recovery words"
                    };
                    show.CheckedChanged += delegate { seedInput.UseSystemPasswordChar = !show.Checked; };
                    layout.Controls.Add(show, 0, 2);
                    FlowLayoutPanel buttons = new FlowLayoutPanel {
                        Dock = DockStyle.Fill, FlowDirection = FlowDirection.RightToLeft
                    };
                    Button recover = new Button { Text = "Restore test wallet", Width = 165,
                        DialogResult = DialogResult.OK };
                    Button cancel = new Button { Text = "Cancel", Width = 100,
                        DialogResult = DialogResult.Cancel };
                    buttons.Controls.Add(recover); buttons.Controls.Add(cancel);
                    layout.Controls.Add(buttons, 0, 3);
                    dialog.Controls.Add(layout);
                    dialog.AcceptButton = recover;
                    dialog.CancelButton = cancel;
                    if (dialog.ShowDialog(this) != DialogResult.OK) return;
                    string seed = FrgWalletInput.NormalizeEnglishMnemonic(seedInput.Text);
                    Dictionary<string, object> p = new Dictionary<string, object> {
                        { "filename", name }, { "password", passwordBox.Text },
                        { "seed", seed }, { "restore_height", 0 },
                        { "language", "English" }
                    };
                    seedInput.Clear();
                    show.Checked = false;
                    try
                    {
                        IDictionary result = Rpc("http://127.0.0.1:39484/json_rpc",
                                                 "restore_deterministic_wallet", p, 90000);
                        if (!result.Contains("address") ||
                            !FrgWalletInput.LooksLikePublicAddress(Convert.ToString(result["address"])))
                            throw new InvalidOperationException("Native wallet did not return a plausible FRG address.");
                    }
                    catch
                    {
                        // Wallet-RPC errors can contain service-provided text.
                        // Never echo returned payloads or any seed to the UI.
                        throw new InvalidOperationException(
                            "Recovery was not verified. Examine only redacted local RPC diagnostics; never retry with a funded seed.");
                    }
                    finally
                    {
                        p["seed"] = String.Empty;
                    }
                    WalletOpened("Restored test wallet " + name + " (genesis rescan)");
                }
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private void RequireNewWalletPassword()
        {
            if (passwordBox.Text.Length < 12)
                throw new InvalidOperationException("Use a test-wallet password of at least 12 characters.");
        }

        private bool WalletFileAlreadyExists(string name)
        {
            string baseName = Path.Combine(appRoot, "wallets", name);
            return File.Exists(baseName) || File.Exists(baseName + ".keys") ||
                   Directory.Exists(baseName);
        }

        private void OpenWallet(object sender, EventArgs e)
        {
            try
            {
                string name = ValidWalletName();
                EnsureWalletService();
                Dictionary<string, object> p = new Dictionary<string, object> { { "filename", name }, { "password", passwordBox.Text } };
                Rpc("http://127.0.0.1:39484/json_rpc", "open_wallet", p, 15000);
                WalletOpened("Opened " + name);
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private string ValidWalletName()
        {
            return FrgWalletInput.WalletName(walletNameBox.Text);
        }

        private void WalletOpened(string message)
        {
            walletOpen = true;
            walletState.Text = message;
            walletState.ForeColor = Color.FromArgb(40, 125, 78);
            createWalletButton.Enabled = false; openWalletButton.Enabled = false; restoreWalletButton.Enabled = false; closeWalletButton.Enabled = true; seedButton.Enabled = true; sendButton.Enabled = NativeSpendAuthorized;
            passwordBox.Clear();
            RefreshWallet();
            RefreshAddressLists();
#if FRG_PRIVATE_UI_QA
            Console.WriteLine("QA_GUI: address book refresh returned");
#endif
        }

        private void CloseWallet(object sender, EventArgs e)
        {
            try { Rpc("http://127.0.0.1:39484/json_rpc", "close_wallet", new Dictionary<string, object>()); } catch { }
            walletOpen = false;
            walletState.Text = "Wallet closed"; walletState.ForeColor = Color.DimGray;
            createWalletButton.Enabled = true; openWalletButton.Enabled = true; restoreWalletButton.Enabled = true; closeWalletButton.Enabled = false; seedButton.Enabled = false; sendButton.Enabled = false;
            balanceValue.Text = "—"; unlockedValue.Text = "—"; addressBox.Text = "Open a wallet to view its address.";
            receiveAddressGrid.Rows.Clear(); contactGrid.Rows.Clear();
        }

        private void ShowRecoverySeed(object sender, EventArgs e)
        {
            try
            {
                if (!walletOpen) throw new InvalidOperationException("Open a wallet first.");
                IDictionary result = Rpc("http://127.0.0.1:39484/json_rpc", "query_key", new Dictionary<string, object> { { "key_type", "mnemonic" } }, 15000);
                string seed = result.Contains("key") ? Convert.ToString(result["key"]) : "";
                if (seed.Length == 0) throw new InvalidOperationException("The wallet service did not return a recovery seed.");

                Form dialog = new Form { Text = "ForgeCoin Recovery Seed", Size = new Size(720, 330), StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, FormBorderStyle = FormBorderStyle.FixedDialog };
                Label warning = new Label { Text = "Write these words down and store them offline. Anyone with this seed can spend the wallet's funds.", Dock = DockStyle.Top, Height = 58, Padding = new Padding(14), ForeColor = Color.DarkRed };
                TextBox words = new TextBox { Text = seed, ReadOnly = true, Multiline = true, Dock = DockStyle.Fill, Font = new Font("Segoe UI", 12F), Margin = new Padding(14), ScrollBars = ScrollBars.Vertical };
                Panel buttons = new Panel { Dock = DockStyle.Bottom, Height = 58 };
                Button copy = new Button { Text = "Copy", Width = 100, Height = 34, Location = new Point(478, 12) };
                Button done = new Button { Text = "I saved it", Width = 100, Height = 34, Location = new Point(588, 12), DialogResult = DialogResult.OK };
                copy.Click += delegate { Clipboard.SetText(seed); };
                buttons.Controls.Add(copy); buttons.Controls.Add(done);
                dialog.AcceptButton = done;
                dialog.Controls.Add(words); dialog.Controls.Add(warning); dialog.Controls.Add(buttons);
#if FRG_PRIVATE_UI_QA
                Console.WriteLine("QA_GUI: entering native seed backup dialog");
#endif
                dialog.ShowDialog(this);
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private void RefreshAddressLists()
        {
            if (!walletOpen) return;
            try
            {
                IDictionary addresses = Rpc("http://127.0.0.1:39484/json_rpc", "get_address", new Dictionary<string, object> { { "account_index", 0 } });
                receiveAddressGrid.Rows.Clear();
                IEnumerable rows = addresses.Contains("addresses") ? addresses["addresses"] as IEnumerable : null;
                if (rows != null)
                {
                    foreach (object item in rows)
                    {
                        IDictionary a = item as IDictionary;
                        if (a == null) continue;
                        receiveAddressGrid.Rows.Add(
                            a.Contains("address_index") ? a["address_index"] : "",
                            a.Contains("label") ? a["label"] : "",
                            a.Contains("address") ? a["address"] : "",
                            a.Contains("used") && Convert.ToBoolean(a["used"], CultureInfo.InvariantCulture) ? "Yes" : "No");
                    }
                }

                IDictionary book = Rpc("http://127.0.0.1:39484/json_rpc", "get_address_book", new Dictionary<string, object> { { "entries", new object[0] } });
                contactGrid.Rows.Clear();
                IEnumerable contacts = book.Contains("entries") ? book["entries"] as IEnumerable : null;
                if (contacts != null)
                {
                    foreach (object item in contacts)
                    {
                        IDictionary c = item as IDictionary;
                        if (c == null) continue;
                        contactGrid.Rows.Add(
                            c.Contains("index") ? c["index"] : "",
                            c.Contains("description") ? c["description"] : "",
                            c.Contains("address") ? c["address"] : "");
                    }
                }
            }
            catch (Exception ex) { walletState.Text = "Address refresh: " + ex.Message; walletState.ForeColor = Color.DarkOrange; }
        }

        private void GenerateReceiveAddress(object sender, EventArgs e)
        {
            try
            {
                if (!walletOpen) throw new InvalidOperationException("Open a wallet before generating an address.");
                string label = receiveLabelBox.Text.Trim();
                Rpc("http://127.0.0.1:39484/json_rpc", "create_address", new Dictionary<string, object> { { "account_index", 0 }, { "label", label } });
                receiveLabelBox.Clear();
                RefreshAddressLists();
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private void CopyReceiveAddress(object sender, EventArgs e)
        {
            try
            {
                if (receiveAddressGrid.SelectedRows.Count == 0) throw new InvalidOperationException("Select a receive address first.");
                string value = Convert.ToString(receiveAddressGrid.SelectedRows[0].Cells["Address"].Value);
                if (value.Length == 0) throw new InvalidOperationException("The selected row has no address.");
                Clipboard.SetText(value);
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private void SaveContact(object sender, EventArgs e)
        {
            try
            {
                if (!walletOpen) throw new InvalidOperationException("Open a wallet before saving recipients.");
                string address = contactAddressBox.Text.Trim();
                string name = contactNameBox.Text.Trim();
                if (address.Length < 20) throw new InvalidOperationException("Enter a valid ForgeCoin recipient address.");
                Rpc("http://127.0.0.1:39484/json_rpc", "add_address_book", new Dictionary<string, object> { { "address", address }, { "description", name } });
                contactNameBox.Clear(); contactAddressBox.Clear();
                RefreshAddressLists();
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private void UseContactForSend(object sender, EventArgs e)
        {
            try
            {
                if (contactGrid.SelectedRows.Count == 0) throw new InvalidOperationException("Select a saved recipient first.");
                sendAddressBox.Text = Convert.ToString(contactGrid.SelectedRows[0].Cells["Address"].Value);
                MessageBox.Show("The recipient address was placed in the Wallet tab's Send form.", "ForgeCoin", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private void DeleteContact(object sender, EventArgs e)
        {
            try
            {
                if (contactGrid.SelectedRows.Count == 0) throw new InvalidOperationException("Select a saved recipient first.");
                int index = Convert.ToInt32(contactGrid.SelectedRows[0].Cells["Index"].Value, CultureInfo.InvariantCulture);
                if (MessageBox.Show("Delete this saved recipient?", "ForgeCoin", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
                Rpc("http://127.0.0.1:39484/json_rpc", "delete_address_book", new Dictionary<string, object> { { "index", index } });
                RefreshAddressLists();
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private void RefreshWallet()
        {
            if (!walletOpen || Interlocked.Exchange(ref walletRefreshInFlight, 1) != 0) return;
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    IDictionary balances = Rpc("http://127.0.0.1:39484/json_rpc", "get_balance", new Dictionary<string, object> { { "account_index", 0 } });
                    IDictionary addresses = Rpc("http://127.0.0.1:39484/json_rpc", "get_address", new Dictionary<string, object> { { "account_index", 0 } });
                    PostUi(delegate
                    {
                        if (!walletOpen) return;
                        balanceValue.Text = FormatCoin(ToLong(balances["balance"]));
                        unlockedValue.Text = FormatCoin(ToLong(balances["unlocked_balance"]));
                        addressBox.Text = Convert.ToString(addresses["address"]);
                        if (miningAddressBox.Text.Trim().Length == 0) miningAddressBox.Text = addressBox.Text;
                        if (poolUserBox.Text.Trim().Length == 0) poolUserBox.Text = addressBox.Text;
                    });
                }
                catch (Exception ex)
                {
                    string message = ex.Message;
                    PostUi(delegate { walletState.Text = "Wallet refresh: " + message; walletState.ForeColor = Color.DarkOrange; });
                }
                finally { Interlocked.Exchange(ref walletRefreshInFlight, 0); }
            });
        }

        private void SendFunds(object sender, EventArgs e)
        {
            // Guard at the actual send entrypoint, not just on the button.
            // No native FRG spend is authorized before independent consensus
            // review, signed builds and deliberate owner launch activation.
            if (!NativeSpendAuthorized)
            {
                ShowError("Public native FRG spending is disabled before mainnet release authorization.");
                return;
            }
            if (Interlocked.CompareExchange(ref transferInFlight, 1, 0) != 0) return;
            bool submissionAttempted = false;
            try
            {
                if (!walletOpen || !IsRunning(walletRpc))
                    throw new InvalidOperationException("Open the native wallet before transferring.");
                long atomic = FrgWalletInput.ParseAmountAtoms(sendAmountBox.Text.Trim());
                string address = sendAddressBox.Text.Trim();
                if (!FrgWalletInput.LooksLikePublicAddress(address))
                    throw new InvalidOperationException("Enter a public FRG address, not a recovery phrase.");
                IDictionary validation = Rpc("http://127.0.0.1:39484/json_rpc",
                    "validate_address", new Dictionary<string, object> {
                        { "address", address }, { "any_net_type", false },
                        { "allow_openalias", false }
                    }, 10000);
                if (!validation.Contains("valid") ||
                    !Convert.ToBoolean(validation["valid"], CultureInfo.InvariantCulture))
                    throw new InvalidOperationException("The native wallet rejected the destination address checksum/network.");
                if (validation.Contains("nettype") &&
                    !String.Equals(Convert.ToString(validation["nettype"]), "mainnet",
                        StringComparison.OrdinalIgnoreCase))
                    throw new InvalidOperationException("A testnet or stagenet address cannot receive a mainnet transfer.");
                DialogResult confirmed = MessageBox.Show(
                    "Native wallet validated the destination. Send " +
                    FormatCoin(atomic) + " FRG to\n\n" + address +
                    "?\n\nThis action cannot be reversed.",
                    "Confirm native FRG transfer", MessageBoxButtons.YesNo,
                    MessageBoxIcon.Warning);
                if (confirmed != DialogResult.Yes) return;
                sendButton.Enabled = false;
                ArrayList destinations = new ArrayList {
                    new Dictionary<string, object> { { "amount", atomic }, { "address", address } }
                };
                submissionAttempted = true;
                IDictionary result = Rpc("http://127.0.0.1:39484/json_rpc", "transfer",
                    new Dictionary<string, object> {
                        { "destinations", destinations }, { "account_index", 0 },
                        { "priority", 0 }, { "get_tx_key", false }
                    }, 120000);
                string tx = result.Contains("tx_hash") ?
                    Convert.ToString(result["tx_hash"]) : String.Empty;
                if (!FrgWalletInput.IsTransactionId(tx))
                    throw new InvalidOperationException("Native wallet did not return a valid transaction identifier.");
                MessageBox.Show("Native wallet reported transaction hash:\n\n" + tx +
                    "\n\nCheck confirmation on the canonical chain before considering this settled.",
                    "FRG transfer submitted (not yet confirmed)",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                sendAddressBox.Clear();
                sendAmountBox.Clear();
                RefreshWallet();
            }
            catch (Exception ex)
            {
                if (submissionAttempted)
                {
                    // A wallet-RPC timeout may mean the transfer ALREADY
                    // broadcast. Repeating it can spend twice.
                    MessageBox.Show(
                        "The native wallet's transfer outcome is ambiguous. Do NOT " +
                        "retry automatically. Reopen the wallet and reconcile " +
                        "outgoing transfers, transaction hashes and chain state " +
                        "before making another payment.",
                        "Transfer outcome unverified", MessageBoxButtons.OK,
                        MessageBoxIcon.Warning);
                }
                else ShowError(ex.Message);
            }
            finally
            {
                Interlocked.Exchange(ref transferInFlight, 0);
                if (!IsDisposed) sendButton.Enabled = NativeSpendAuthorized && walletOpen;
            }
        }

        private void StartMining(object sender, EventArgs e)
        {
            try
            {
                // Production is frozen. A separately compiled test-only build
                // can mine only through its GUI-owned hash-pinned, localhost,
                // zero-peer offline node; never through public P2P.
                if (!NativeMiningAuthorized)
                {
#if FRG_PRIVATE_MINING_QA
                    if (!IsolatedSoloQaReady())
                        throw new InvalidOperationException(
                            "Isolated solo QA requires a GUI-owned offline pinned daemon.");
#else
                    throw new InvalidOperationException(
                        "Native mainnet mining cannot start before the owner's authorized Oracle/network launch.");
#endif
                }
                if (!IsRunning(daemon))
                    throw new InvalidOperationException("Start the ForgeCoin node before mining.");
                if (IsRunning(poolMiner))
                    throw new InvalidOperationException("Stop pool mining before solo mining.");
                string address = miningAddressBox.Text.Trim();
                if (!FrgWalletInput.LooksLikePublicAddress(address))
                    throw new InvalidOperationException(
                        "Enter a public FRG payout address, never a recovery seed.");
                if (Interlocked.CompareExchange(ref miningStartInFlight, 1, 0) != 0)
                    return;
                Dictionary<string, object> request = new Dictionary<string, object> {
                    { "miner_address", address },
                    { "threads_count", Decimal.ToInt32(miningThreads.Value) },
                    { "do_background_mining", false },
                    { "ignore_battery", false }
                };
                startMiningButton.Enabled = false;
                miningState.Text = "Starting";
                miningState.BackColor = Color.FromArgb(205, 139, 36);
                miningDetailLabel.Text = "Miner monitor: initializing local RandomX workers...";
                // Native RandomX initialization can take longer than the
                // two-second polling deadline. Never block the Windows UI
                // while native workers initialize their cache and dataset.
                ThreadPool.QueueUserWorkItem(delegate
                {
                    bool accepted = false;
                    string failure = null;
                    try
                    {
                        IDictionary reply = RestRpc(
                            "http://127.0.0.1:39481/start_mining", request, 60000);
                        accepted = reply != null;
                    }
                    catch (Exception ex)
                    {
                        // No secret wallet material is sent in this request,
                        // but still keep backend stack traces out of the GUI.
                        failure = ex is WebException
                            ? "Local daemon mining RPC timed out or disconnected."
                            : "Native solo mining RPC rejected the start request.";
                    }
                    finally
                    {
                        Interlocked.Exchange(ref miningStartInFlight, 0);
                    }
                    PostUi(delegate
                    {
                        if (IsDisposed || !IsRunning(daemon)) return;
                        if (accepted)
                        {
                            miningState.Text = "Mining";
                            miningState.BackColor = Color.FromArgb(53, 145, 92);
                            miningDetailLabel.Text =
                                "Miner monitor: native RandomX start confirmed; checking hashrate...";
                            stopMiningButton.Enabled = true;
                            startMiningButton.Enabled = false;
                            RefreshMining();
                        }
                        else
                        {
                            miningState.Text = "Stopped";
                            miningState.BackColor = Color.FromArgb(110, 118, 130);
                            miningDetailLabel.Text = "Miner monitor: " + failure;
                            stopMiningButton.Enabled = false;
                            startMiningButton.Enabled = NativeMiningAuthorized;
#if FRG_PRIVATE_MINING_QA
                            startMiningButton.Enabled = IsolatedSoloQaReady();
#endif
                        }
                    });
                });
            }
            catch (Exception ex)
            {
#if FRG_PRIVATE_MINING_QA
                // Disposable QA must not block on a modal error dialog when
                // a required RPC precondition is unmet. Print only type.
                Console.Error.WriteLine("QA_SOLO_GUI_START_REJECTED=" +
                                        ex.GetType().Name);
                miningDetailLabel.Text = "Isolated QA native start rejected.";
#else
                ShowError(ex.Message);
#endif
            }
        }

        private void StopMining(object sender, EventArgs e)
        {
            try { RestRpc("http://127.0.0.1:39481/stop_mining", new Dictionary<string, object>()); } catch (Exception ex) { ShowError(ex.Message); }
            miningState.Text = "Stopped"; miningState.BackColor = Color.FromArgb(110, 118, 130);
            hashRateValue.Text = "0"; miningThreadsValue.Text = "0";
            miningDetailLabel.Text = "Miner monitor: stopped at " + DateTime.Now.ToString("HH:mm:ss");
            startMiningButton.Enabled = NativeMiningAuthorized; stopMiningButton.Enabled = false;
#if FRG_PRIVATE_MINING_QA
            startMiningButton.Enabled = IsolatedSoloQaReady();
#endif
        }

        private void RefreshMining()
        {
            if (!IsRunning(daemon))
            {
                miningState.Text = "Node stopped"; miningState.BackColor = Color.FromArgb(110, 118, 130);
                hashRateValue.Text = "0"; miningThreadsValue.Text = "0";
                miningDifficultyValue.Text = "—"; miningBlockHeightValue.Text = "—"; miningNetworkRateValue.Text = "—";
                miningRewardValue.Text = "—"; miningTargetValue.Text = "—"; miningBlocksFoundValue.Text = minedBlocksSession.ToString(CultureInfo.InvariantCulture);
                miningNodeDetailLabel.Text = "Node monitor: stopped • Public bootstrap and native mining remain launch-locked.";
                miningDetailLabel.Text = "Miner monitor: stopped";
                // Timer-driven refresh must NEVER override the explicit
                // prelaunch mining authorization, even with no daemon.
                startMiningButton.Enabled = NativeMiningAuthorized; stopMiningButton.Enabled = false;
                return;
            }
            if (Interlocked.Exchange(ref miningRefreshInFlight, 1) != 0) return;
            string fallbackPayout = miningAddressBox.Text.Trim();
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    IDictionary status = RestRpc("http://127.0.0.1:39481/mining_status", new Dictionary<string, object>());
                    IDictionary info = Rpc("http://127.0.0.1:39481/json_rpc", "get_info", new Dictionary<string, object>());
                    PostUi(delegate
                    {
                        bool active = status.Contains("active") && Convert.ToBoolean(status["active"], CultureInfo.InvariantCulture);
                        double speed = status.Contains("speed") ? Convert.ToDouble(status["speed"], CultureInfo.InvariantCulture) : 0;
                        double difficulty = status.Contains("difficulty") ? Convert.ToDouble(status["difficulty"], CultureInfo.InvariantCulture) : 0;
                        double targetSeconds = status.Contains("block_target") ? Convert.ToDouble(status["block_target"], CultureInfo.InvariantCulture) : 0;
                        hashRateValue.Text = FormatRate(speed);
                        miningNetworkRateValue.Text = targetSeconds > 0 ? FormatRate(difficulty / targetSeconds) : "—";
                        miningDifficultyValue.Text = difficulty.ToString("N0", CultureInfo.InvariantCulture);
                        miningRewardValue.Text = status.Contains("block_reward") ? FormatCoin(ToLong(status["block_reward"])) : "—";
                        miningTargetValue.Text = targetSeconds > 0 ? targetSeconds.ToString("N0", CultureInfo.InvariantCulture) + " sec" : "—";
                        miningThreadsValue.Text = status.Contains("threads_count") ? Convert.ToString(status["threads_count"], CultureInfo.InvariantCulture) : "0";
                        miningBlocksFoundValue.Text = minedBlocksSession.ToString(CultureInfo.InvariantCulture);
                        long chainHeight = info.Contains("height") ? ToLong(info["height"]) : 0;
                        long peers = (info.Contains("incoming_connections_count") ? ToLong(info["incoming_connections_count"]) : 0) + (info.Contains("outgoing_connections_count") ? ToLong(info["outgoing_connections_count"]) : 0);
                        bool synchronized = info.Contains("synchronized") && Convert.ToBoolean(info["synchronized"], CultureInfo.InvariantCulture);
                        bool offline = info.Contains("offline") && Convert.ToBoolean(info["offline"], CultureInfo.InvariantCulture);
                        miningBlockHeightValue.Text = Math.Max(0, chainHeight - 1).ToString("N0", CultureInfo.InvariantCulture);
                        miningState.Text = active ? "Mining" : "Stopped";
                        miningState.BackColor = active ? Color.FromArgb(53, 145, 92) : Color.FromArgb(110, 118, 130);
                        startMiningButton.Enabled = NativeMiningAuthorized && !active && Interlocked.CompareExchange(ref miningStartInFlight, 0, 0) == 0; stopMiningButton.Enabled = active;
#if FRG_PRIVATE_MINING_QA
                        // Preserve the in-flight guard during every status refresh:
                        // polling must not re-enable Start while native RPC startup
                        // is still pending in the background.
                        startMiningButton.Enabled = !active && IsolatedSoloQaReady() &&
                            Interlocked.CompareExchange(ref miningStartInFlight, 0, 0) == 0;
#endif
                        string payout = status.Contains("address") ? Shorten(Convert.ToString(status["address"]), 18) : Shorten(fallbackPayout, 18);
                        miningNodeDetailLabel.Text = "Node monitor: " + (offline ? "OFFLINE BOOTSTRAP" : (synchronized ? "ONLINE / synchronized" : "ONLINE / waiting for peer")) + " • Block " + Math.Max(0, chainHeight - 1) + " • Peers " + peers;
                        miningDetailLabel.Text = "Miner monitor: " + (active ? "ACTIVE" : "stopped") + " • " + FormatRate(speed) + " • Payout " + payout + " • Updated " + DateTime.Now.ToString("HH:mm:ss");
                    });
                }
                catch (Exception ex)
                {
                    string message = ex.Message;
                    PostUi(delegate { miningDetailLabel.Text = "Miner update unavailable: " + message; });
                }
                finally { Interlocked.Exchange(ref miningRefreshInFlight, 0); }
            });
        }

        private void StartPoolMining(object sender, EventArgs e)
        {
            try
            {
#if FRG_PRIVATE_POOL_QA
                if (!IsolatedPoolQaReady())
                    throw new InvalidOperationException(
                        "Private GUI pool QA requires an unused disconnected loopback Stratum endpoint.");
#else
                if (!NativeMiningAuthorized)
                    throw new InvalidOperationException("Public pool mining remains disabled until approved launch and payout acceptance.");
#endif
                if (IsRunning(poolMiner)) return;
                if (stopMiningButton.Enabled) throw new InvalidOperationException("Stop solo mining before starting pool mining.");
                string exe = Path.Combine(binRoot, "xmrig", "xmrig.exe");
                if (!File.Exists(exe)) throw new FileNotFoundException("The packaged XMRig pool backend is missing.", exe);
#if FRG_PRIVATE_POOL_QA
                RequirePinnedPrivateQaXmrig(exe);
#endif
                string url = poolUrlBox.Text.Trim();
                string user = poolUserBox.Text.Trim();
                string pass = poolPassBox.Text;
                string worker = poolWorkerBox.Text.Trim();
                if (url.Length < 4 || url.IndexOf(':') < 0) throw new InvalidOperationException("Enter the pool address and port, for example pool.example.org:3333.");
                if (!FrgWalletInput.LooksLikePublicAddress(user))
                    throw new InvalidOperationException("Enter a public native FRG wallet address for account-free pool mining.");
                // XMRig 6.22 truncates --api-id at 31 bytes (observed
                // against its genuine localhost /2/summary API).
                // Twelve random bytes yield a 24-character ID with 96 bits
                // of entropy; never expect the truncated 32-hex value.
                byte[] monitorId = new byte[12];
                using (RandomNumberGenerator rng = RandomNumberGenerator.Create())
                    rng.GetBytes(monitorId);
                poolApiId = BitConverter.ToString(monitorId)
                    .Replace("-", "").ToLowerInvariant();
                Array.Clear(monitorId, 0, monitorId.Length);
                List<string> args = new List<string> {
                    "--api-id=" + poolApiId,
                    "-a", "rx/0", "-o", Quote(url), "-u", Quote(user), "-p", Quote(pass.Length == 0 ? "x" : pass),
                    "-t", Decimal.ToInt32(poolThreads.Value).ToString(CultureInfo.InvariantCulture), "--keepalive",
                    "--http-host", "127.0.0.1", "--http-port", "39483", "--no-color", "--print-time", "5"
                };
                if (worker.Length > 0) { args.Add("--rig-id"); args.Add(Quote(worker)); }
#if FRG_PRIVATE_POOL_QA
                // The test GUI NEVER hashes or contacts any public pool.
                args.Add("--no-cpu"); args.Add("--no-opencl"); args.Add("--no-cuda");
#endif
                poolLogBox.Clear();
                poolMiner = StartPoolCaptured(exe, string.Join(" ", args.ToArray()));
                if (poolMiner == null)
                {
                    poolApiId = null;
                    return;
                }
                poolState.Text = "Connecting"; poolState.BackColor = Color.FromArgb(205, 139, 36);
                poolDetailLabel.Text = "Pool miner status: connecting to " + url + "…";
                startPoolButton.Enabled = false; stopPoolButton.Enabled = true;
            }
            catch (Exception ex) { ShowError(ex.Message); }
        }

        private void StopPoolMining(object sender, EventArgs e)
        {
            if (IsRunning(poolMiner)) { try { poolMiner.Kill(); poolMiner.WaitForExit(2500); } catch { } }
            poolMiner = null;
            poolApiId = null;
            poolState.Text = "Stopped"; poolState.BackColor = Color.FromArgb(110, 118, 130);
            poolDetailLabel.Text = "Pool miner status: stopped at " + DateTime.Now.ToString("HH:mm:ss");
            startPoolButton.Enabled = NativeMiningAuthorized; stopPoolButton.Enabled = false;
#if FRG_PRIVATE_POOL_QA
            startPoolButton.Enabled = true;
#endif
        }

        private Process StartPoolCaptured(string exe, string args)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo(exe, args) { WorkingDirectory = Path.GetDirectoryName(exe), UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
                Process p = new Process { StartInfo = psi, EnableRaisingEvents = true };
                p.OutputDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) AppendPoolLog(e.Data); };
                p.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) AppendPoolLog(e.Data); };
                p.Exited += delegate { AppendPoolLog("XMRig exited."); };
                p.Start(); p.BeginOutputReadLine(); p.BeginErrorReadLine();
                return p;
            }
            catch (Exception ex) { ShowError(ex.Message); return null; }
        }

        private void RefreshPoolMining()
        {
            if (!IsRunning(poolMiner))
            {
                if (poolMiner != null) StopPoolMining(null, EventArgs.Empty);
                return;
            }
            if (Interlocked.Exchange(ref poolRefreshInFlight, 1) != 0) return;
            string requestedPool = poolUrlBox.Text.Trim();
            string expectedMonitor = poolApiId;
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    IDictionary summary = HttpGetJson("http://127.0.0.1:39483/2/summary");
                    XmrigPoolSnapshot result = XmrigPoolStatus.Parse(
                        summary, requestedPool, expectedMonitor);
                    PostUi(delegate
                    {
                        // XMRig is independent of ForgeCoin consensus. Do not
                        // display a stale or unrelated API as our pool miner.
                        if (!IsRunning(poolMiner) || poolApiId != result.ApiId)
                            return;
                        poolHashRateValue.Text = FormatRate(result.Hashrate);
                        poolAcceptedValue.Text = result.AcceptedShares.ToString(
                            "N0", CultureInfo.InvariantCulture);
                        poolRejectedValue.Text = result.RejectedShares.ToString(
                            "N0", CultureInfo.InvariantCulture);
                        poolDifficultyValue.Text = result.Difficulty > 0
                            ? result.Difficulty.ToString("N0", CultureInfo.InvariantCulture)
                            : "—";
                        poolNameValue.Text = Shorten(
                            result.ReportedPool.Length > 0
                                ? result.ReportedPool : requestedPool, 20);
                        poolPingValue.Text = result.PingMs > 0
                            ? result.PingMs.ToString(CultureInfo.InvariantCulture) + " ms"
                            : "—";
                        poolUptimeValue.Text = result.ConnectionSeconds > 0
                            ? FormatDuration(result.ConnectionSeconds) : "—";
                        poolAlgorithmValue.Text = result.Algorithm.Length > 0
                            ? result.Algorithm : "—";
                        poolState.Text = result.Phase;
                        poolState.BackColor = result.Phase == "Hashing"
                            ? Color.FromArgb(53, 145, 92)
                            : result.Phase == "Connected"
                                ? Color.FromArgb(29, 112, 217)
                                : result.Phase == "Other pool"
                                    ? Color.DarkRed
                                    : Color.FromArgb(205, 139, 36);
                        // Hashrate proves local CPU work. Only accepted-share
                        // counters can support share claims; neither proves a
                        // settled FRG pool payout.
                        poolDetailLabel.Text = "Pool miner: " + result.Phase +
                            " • " + FormatRate(result.Hashrate) +
                            " • " + result.AcceptedShares + " accepted / " +
                            result.RejectedShares + " rejected • " +
                            "Updated " + DateTime.Now.ToString("HH:mm:ss");
                    });
                }
                catch (Exception ex)
                {
                    bool identityMismatch = ex is ArgumentException;
                    PostUi(delegate
                    {
                        // An older poll may finish after Stop + Start. Do not
                        // let its failure overwrite the new process's state.
                        if (IsDisposed || !IsRunning(poolMiner) ||
                            poolApiId != expectedMonitor) return;
                        poolState.Text = identityMismatch ? "Unverified" : "Connecting";
                        poolState.BackColor = identityMismatch
                            ? Color.DarkRed : Color.FromArgb(205, 139, 36);
                        poolDetailLabel.Text = identityMismatch
                            ? "Pool telemetry rejected: invalid or unrelated local XMRig API."
                            : "Pool miner is waiting for a verified local API response.";
                    });
                }
                finally { Interlocked.Exchange(ref poolRefreshInFlight, 0); }
            });
        }

        private void AppendPoolLog(string line)
        {
            if (IsDisposed) return;
            BeginInvoke((MethodInvoker)delegate
            {
                poolLogBox.AppendText("[" + DateTime.Now.ToString("HH:mm:ss") + "] " + line + Environment.NewLine);
                if (poolLogBox.TextLength > 120000) { poolLogBox.Select(0, 30000); poolLogBox.SelectedText = ""; }
                poolLogBox.ScrollToCaret();
            });
        }

        private Process StartCaptured(string exe, string args, string prefix)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo(exe, args) { WorkingDirectory = binRoot, UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
                Process p = new Process { StartInfo = psi, EnableRaisingEvents = true };
                p.OutputDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) AppendLog(prefix, e.Data); };
                p.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) AppendLog(prefix, e.Data); };
                p.Exited += delegate { AppendLog(prefix, "Process exited."); };
                p.Start(); p.BeginOutputReadLine(); p.BeginErrorReadLine();
                return p;
            }
            catch (Exception ex) { ShowError(ex.Message); return null; }
        }

        private void AppendLog(string prefix, string line)
        {
            if (prefix == "WALLET") line = "Native wallet diagnostic redacted.";
            if (IsDisposed) return;
            if (prefix == "NODE" && line.IndexOf("Found block ", StringComparison.OrdinalIgnoreCase) >= 0 && line.IndexOf(" at height ", StringComparison.OrdinalIgnoreCase) >= 0) Interlocked.Increment(ref minedBlocksSession);
            BeginInvoke((MethodInvoker)delegate
            {
                logBox.AppendText("[" + DateTime.Now.ToString("HH:mm:ss") + "] " + prefix + "  " + line + Environment.NewLine);
                if (logBox.TextLength > 120000) logBox.Select(0, 30000);
                logBox.ScrollToCaret();
            });
        }

        private IDictionary Rpc(string url, string method, IDictionary<string, object> parameters, int timeoutMs = 2000)
        {
            Dictionary<string, object> request = new Dictionary<string, object> {
                { "jsonrpc", "2.0" }, { "id", "0" },
                { "method", method }, { "params", parameters }
            };
            string payload = json.Serialize(request);
            string text;
            if (url == "http://127.0.0.1:39484/json_rpc")
            {
                // No unauthenticated fallback for ANY native wallet RPC.
                if (walletSession == null)
                    throw new InvalidOperationException("Native wallet authorization unavailable.");
                text = walletSession.PostJson(url, payload, timeoutMs);
            }
            else
            {
                // Daemon only: keep wallet secrets completely out of the
                // generic HTTP client and never follow redirects/proxies.
                byte[] body = Encoding.UTF8.GetBytes(payload);
                HttpWebRequest http = (HttpWebRequest)WebRequest.Create(url);
                http.Method = "POST";
                http.ContentType = "application/json";
                http.ContentLength = body.Length;
                http.Timeout = timeoutMs;
                http.ReadWriteTimeout = timeoutMs;
                http.Proxy = null;
                http.AllowAutoRedirect = false;
                using (Stream stream = http.GetRequestStream())
                    stream.Write(body, 0, body.Length);
                using (HttpWebResponse response = (HttpWebResponse)http.GetResponse())
                using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                    text = reader.ReadToEnd();
            }
            IDictionary parsed = json.DeserializeObject(text) as IDictionary;
            if (parsed == null)
                throw new InvalidOperationException("Invalid response from ForgeCoin.");
            if (parsed.Contains("error"))
            {
                if (url == "http://127.0.0.1:39484/json_rpc")
                    throw new InvalidOperationException("Native wallet RPC rejected the requested operation.");
                IDictionary error = parsed["error"] as IDictionary;
                throw new InvalidOperationException(error != null && error.Contains("message")
                    ? Convert.ToString(error["message"]) : "ForgeCoin RPC error");
            }
            return parsed.Contains("result") ? (IDictionary)parsed["result"] : parsed;
        }

        private IDictionary RestRpc(string url, IDictionary<string, object> request, int timeoutMs = 3000)
        {
            byte[] body = Encoding.UTF8.GetBytes(json.Serialize(request));
            HttpWebRequest http = (HttpWebRequest)WebRequest.Create(url);
            http.Method = "POST"; http.ContentType = "application/json";
            http.ContentLength = body.Length; http.Timeout = timeoutMs;
            http.ReadWriteTimeout = timeoutMs; http.Proxy = null;
            http.AllowAutoRedirect = false; http.ServicePoint.Expect100Continue = false;
            using (Stream s = http.GetRequestStream()) s.Write(body, 0, body.Length);
            string text;
            using (HttpWebResponse response = (HttpWebResponse)http.GetResponse()) using (StreamReader reader = new StreamReader(response.GetResponseStream())) text = reader.ReadToEnd();
            IDictionary parsed = json.DeserializeObject(text) as IDictionary;
            if (parsed == null) throw new InvalidOperationException("Invalid response from the ForgeCoin node.");
            if (parsed.Contains("status") && !string.Equals(Convert.ToString(parsed["status"]), "OK", StringComparison.OrdinalIgnoreCase))
            {
                string reason = parsed.Contains("error_details") ? Convert.ToString(parsed["error_details"]) : Convert.ToString(parsed["status"]);
                if (string.Equals(reason, "BUSY", StringComparison.OrdinalIgnoreCase)) reason = "The online node is still waiting for synchronization. Connect to another ForgeCoin peer, or stop the node and enable Offline Bootstrap Mining on the Node tab before starting it again.";
                throw new InvalidOperationException(reason);
            }
            return parsed;
        }

        private IDictionary HttpGetJson(string url)
        {
            // The miner monitor is never allowed to traverse a proxy,
            // follow redirects or read an arbitrarily large localhost reply.
            Uri endpoint = new Uri(url);
            if (endpoint.Scheme != "http" || endpoint.Host != "127.0.0.1" ||
                endpoint.Port != 39483 || endpoint.AbsolutePath != "/2/summary" ||
                endpoint.Query.Length != 0 || endpoint.Fragment.Length != 0)
                throw new InvalidOperationException("Invalid local miner API endpoint.");
            HttpWebRequest http = (HttpWebRequest)WebRequest.Create(endpoint);
            http.Method = "GET";
            http.Timeout = 1500;
            http.ReadWriteTimeout = 1500;
            http.Proxy = null;
            http.AllowAutoRedirect = false;
            http.KeepAlive = false;
            string body;
            using (HttpWebResponse response = (HttpWebResponse)http.GetResponse())
            using (Stream source = response.GetResponseStream())
            using (MemoryStream output = new MemoryStream())
            {
                if (response.StatusCode != HttpStatusCode.OK)
                    throw new InvalidOperationException("Local miner API unavailable.");
                byte[] chunk = new byte[8192];
                int size;
                while ((size = source.Read(chunk, 0, chunk.Length)) > 0)
                {
                    if (output.Length + size > 512 * 1024)
                        throw new InvalidOperationException("Local miner API response too large.");
                    output.Write(chunk, 0, size);
                }
                body = Encoding.UTF8.GetString(output.ToArray());
            }
            IDictionary parsed = json.DeserializeObject(body) as IDictionary;
            if (parsed == null)
                throw new InvalidOperationException("Invalid XMRig API response.");
            return parsed;
        }

        private static double ArrayNumber(object value, int index)
        {
            IEnumerable items = value as IEnumerable;
            if (items == null) return 0;
            int current = 0;
            foreach (object item in items)
            {
                if (current++ == index) return item == null ? 0 : Convert.ToDouble(item, CultureInfo.InvariantCulture);
            }
            return 0;
        }

        private void PostUi(Action update)
        {
            if (IsDisposed || Disposing) return;
            try
            {
                BeginInvoke((MethodInvoker)delegate
                {
                    if (!IsDisposed && !Disposing) update();
                });
            }
            catch (InvalidOperationException) { }
        }

        private static int CountItems(IEnumerable items)
        {
            if (items == null) return 0;
            int count = 0;
            foreach (object item in items) count++;
            return count;
        }

        private static string Field(IDictionary values, string name)
        {
            return values != null && values.Contains(name) ? Convert.ToString(values[name], CultureInfo.InvariantCulture) : "—";
        }

        private static string NumberField(IDictionary values, string name)
        {
            if (values == null || !values.Contains(name)) return "—";
            try { return Convert.ToDouble(values[name], CultureInfo.InvariantCulture).ToString("N0", CultureInfo.InvariantCulture); }
            catch { return Convert.ToString(values[name], CultureInfo.InvariantCulture); }
        }

        private static string FormatTimestamp(long timestamp)
        {
            if (timestamp <= 0) return "Unknown";
            try { return new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).AddSeconds(timestamp).ToLocalTime().ToString("yyyy-MM-dd HH:mm:ss zzz"); }
            catch { return "Unknown"; }
        }

        private static string FormatAge(long timestamp)
        {
            if (timestamp <= 0) return "Unknown";
            DateTime time;
            try { time = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).AddSeconds(timestamp); }
            catch { return "Unknown"; }
            TimeSpan age = DateTime.UtcNow - time;
            if (age.TotalSeconds < 0) return "Just now";
            if (age.TotalMinutes < 1) return Math.Max(0, (int)age.TotalSeconds).ToString(CultureInfo.InvariantCulture) + " sec";
            if (age.TotalHours < 1) return ((int)age.TotalMinutes).ToString(CultureInfo.InvariantCulture) + " min";
            if (age.TotalDays < 1) return ((int)age.TotalHours).ToString(CultureInfo.InvariantCulture) + " hr";
            return ((int)age.TotalDays).ToString(CultureInfo.InvariantCulture) + " days";
        }

        private static string FormatBytes(long bytes)
        {
            if (bytes >= 1048576) return ((double)bytes / 1048576d).ToString("N2", CultureInfo.InvariantCulture) + " MB";
            if (bytes >= 1024) return ((double)bytes / 1024d).ToString("N1", CultureInfo.InvariantCulture) + " KB";
            return Math.Max(0, bytes).ToString("N0", CultureInfo.InvariantCulture) + " B";
        }

        private static bool IsRunning(Process p) { try { return p != null && !p.HasExited; } catch { return false; } }
        private static string Quote(string s) { return "\"" + s.Replace("\"", "\\\"") + "\""; }
        private static long ToLong(object value) { return Convert.ToInt64(value, CultureInfo.InvariantCulture); }
        private static string FormatCoin(long atomic) { return ((decimal)atomic / AtomicUnits).ToString("0.########", CultureInfo.InvariantCulture); }
        private static string FormatRate(double rate)
        {
            if (rate >= 1000000000) return (rate / 1000000000d).ToString("N2", CultureInfo.InvariantCulture) + " GH/s";
            if (rate >= 1000000) return (rate / 1000000d).ToString("N2", CultureInfo.InvariantCulture) + " MH/s";
            if (rate >= 1000) return (rate / 1000d).ToString("N2", CultureInfo.InvariantCulture) + " kH/s";
            return rate.ToString("N1", CultureInfo.InvariantCulture) + " H/s";
        }
        private static string FormatDuration(long seconds)
        {
            TimeSpan span = TimeSpan.FromSeconds(Math.Max(0, seconds));
            return span.TotalDays >= 1 ? ((int)span.TotalDays).ToString(CultureInfo.InvariantCulture) + "d " + span.Hours + "h" : span.Hours.ToString("00") + ":" + span.Minutes.ToString("00") + ":" + span.Seconds.ToString("00");
        }
        private static string Shorten(string value, int max)
        {
            if (string.IsNullOrEmpty(value) || value.Length <= max) return value;
            int side = Math.Max(3, (max - 1) / 2);
            return value.Substring(0, side) + "…" + value.Substring(value.Length - side);
        }
        private static void ShowError(string text) { MessageBox.Show(text, "ForgeCoin", MessageBoxButtons.OK, MessageBoxIcon.Error); }

        private static void WaitThenKill(Process p)
        {
            try { if (!p.WaitForExit(3500)) p.Kill(); } catch { }
        }

        private void OnClosing(object sender, FormClosingEventArgs e)
        {
            // Ask before destroying native wallet session or stopping timers,
            // otherwise Cancel leaves an open UI with a dead wallet process.
            if (IsRunning(daemon))
            {
                DialogResult choice = MessageBox.Show(
                    "Stop the ForgeCoin node before closing?", "ForgeCoin",
                    MessageBoxButtons.YesNoCancel, MessageBoxIcon.Question);
                if (choice == DialogResult.Cancel) { e.Cancel = true; return; }
                if (choice == DialogResult.Yes) StopNode(null, EventArgs.Empty);
            }
            refreshTimer.Stop();
            miningTimer.Stop();
            if (IsRunning(poolMiner))
                try { poolMiner.Kill(); } catch { }
            if (walletOpen && walletSession != null)
                try { Rpc("http://127.0.0.1:39484/json_rpc", "close_wallet",
                          new Dictionary<string, object>(), 2500); } catch { }
            if (IsRunning(walletRpc))
                try { walletRpc.Kill(); walletRpc.WaitForExit(3000); } catch { }
            walletRpc = null;
            walletOpen = false;
            if (walletSession != null)
            {
                walletSession.Dispose();
                walletSession = null;
            }
        }
    }
}
