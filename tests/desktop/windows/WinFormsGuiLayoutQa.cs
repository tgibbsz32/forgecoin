using System;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

namespace ForgeCoinDesktop
{
    // Compile ONLY with /define:FRG_PRIVATE_UI_QA and /main:ForgeCoinDesktop.GuiLayoutQa.
    // This test runs the *real* MainForm in a clean Temp folder, with NO native
    // daemon/wallet/miner binary. It never reads existing user wallet files.
    internal static class GuiLayoutQa
    {
        private static int count;
        private static void Check(bool ok, string message)
        {
            count++;
            if (!ok) throw new InvalidOperationException(message);
        }

        private static T Field<T>(MainForm form, string field) where T : class
        {
            var f = typeof(MainForm).GetField(field,
                BindingFlags.Instance | BindingFlags.NonPublic);
            Check(f != null, "UI field missing: " + field);
            return f.GetValue(form) as T;
        }

        private static TabControl Tabs(Control parent)
        {
            foreach (Control c in parent.Controls)
            {
                var tab = c as TabControl;
                if (tab != null) return tab;
                var nested = Tabs(c);
                if (nested != null) return nested;
            }
            return null;
        }

        private static void CheckVisibleInside(Control child, Control viewport,
                                               string context)
        {
            // A scrollable wallet panel must make every tested button
            // reachable even at the minimum supported 900 x 680 size.
            var scroll = viewport as ScrollableControl;
            Check(scroll != null && scroll.AutoScroll,
                  context + ": parent must scroll");
            scroll.ScrollControlIntoView(child);
            Application.DoEvents();
            Rectangle childBounds = child.RectangleToScreen(child.ClientRectangle);
            Rectangle available = viewport.RectangleToScreen(viewport.ClientRectangle);
            Check(available.IntersectsWith(childBounds),
                  context + ": control is clipped and cannot be reached");
        }

        [STAThread]
        public static int Main()
        {
            string qaRoot = Path.Combine(Path.GetTempPath(),
                "frg-windows-gui-qa-" + Guid.NewGuid().ToString("N"));
            string qaBin = Path.Combine(qaRoot, "empty-bin");
            Directory.CreateDirectory(qaBin);
            Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_ROOT", qaRoot);
            Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_BIN", qaBin);
            try
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                using (var form = new MainForm())
                {
                    Check(form.Text == "ForgeCoin Desktop", "Unexpected window");
                    form.Show();
                    Application.DoEvents();

                    var tabs = Tabs(form);
                    Check(tabs != null && tabs.TabPages.Count == 7,
                          "Wallet, node, explorer, mining and pool tabs must be present");
                    TabPage walletPage = null;
                    TabPage nodePage = null;
                    TabPage miningPage = null;
                    TabPage poolPage = null;
                    foreach (TabPage page in tabs.TabPages)
                    {
                        if (page.Text == "Wallet") walletPage = page;
                        if (page.Text == "Node") nodePage = page;
                        if (page.Text == "Solo Mining") miningPage = page;
                        if (page.Text == "Pool Mining") poolPage = page;
                    }
                    Check(walletPage != null && nodePage != null,
                          "Wallet/Node tab missing");
                    // Test precise field controls; do not invoke Send, Start
                    // Mining, or the live Node event handlers.
                    var send = Field<Button>(form, "sendButton");
                    var solo = Field<Button>(form, "startMiningButton");
                    var pool = Field<Button>(form, "startPoolButton");
                    var restore = Field<Button>(form, "restoreWalletButton");
                    var create = Field<Button>(form, "createWalletButton");
                    var open = Field<Button>(form, "openWalletButton");
                    Check(!send.Enabled && !solo.Enabled && !pool.Enabled,
                          "Prelaunch spend/mining controls accidentally enabled");
                    Check(restore.Enabled && create.Enabled && open.Enabled,
                          "Private QA wallet create/restore/open controls missing");
                    Check(solo.Text == "Launch locked" &&
                          pool.Text == "Launch locked",
                          "Miner buttons should fit the small window");
                    Check(solo.AccessibleDescription.Contains("launch") &&
                          pool.AccessibleDescription.Contains("payout"),
                          "Disabled mining buttons lack accessibility guidance");

                    tabs.SelectedTab = walletPage;
                    var walletLayout = walletPage.Controls["WalletPageLayout"]
                        as TableLayoutPanel;
                    Check(walletLayout != null, "Scrollable wallet layout missing");
                    foreach (Size size in new [] {new Size(900,680),
                                                   new Size(1040,760)})
                    {
                        form.Size = size;
                        Application.DoEvents();
                        CheckVisibleInside(create, walletLayout, "Create wallet");
                        CheckVisibleInside(restore, walletLayout, "Restore seed");
                        CheckVisibleInside(send, walletLayout, "Send locked");
                    }

                    Check(Field<System.Diagnostics.Process>(form, "walletRpc") == null,
                          "GUI boot must never launch wallet RPC automatically");
                    Check(Field<System.Diagnostics.Process>(form, "daemon") == null,
                          "GUI boot must not launch native mainnet daemon");
                    Check(Field<System.Diagnostics.Process>(form, "poolMiner") == null,
                          "GUI boot must not launch pool miner");

                    // Check the default node mode cannot accidentally connect
                    // to external peers in this prelaunch test-only GUI.
                    tabs.SelectedTab = nodePage;
                    Application.DoEvents();
                    var offline = Field<CheckBox>(form, "bootstrapModeBox");
                    Check(!offline.Checked, "Offline node control default changed");
                    Check(offline.Text.Contains("mining is launch-locked"),
                          "Private offline node QA label missing");
                    var nodeStart = Field<Button>(form, "startNodeButton");
                    var peerBox = Field<TextBox>(form, "peerBox");
                    Check(!nodeStart.Enabled && !peerBox.Enabled,
                          "Preview boot unexpectedly allows public P2P node or peer");
                    offline.Checked = true;
                    Application.DoEvents();
                    Check(nodeStart.Enabled, "Explicit offline QA opt-in must enable local node control");
                    offline.Checked = false;
                    Application.DoEvents();
                    Check(!nodeStart.Enabled, "Unchecking offline QA must immediately disable node control");
                    Check(Field<System.Diagnostics.Process>(form, "daemon") == null,
                          "QA checkbox change must never start daemon");

                    form.Close();
                    Application.DoEvents();
                }
                Check(Directory.Exists(Path.Combine(qaRoot, "wallets")),
                      "QA directories must be isolated");
                Check(Directory.GetFiles(Path.Combine(qaRoot, "wallets")).Length == 0,
                      "Opening the QA GUI unexpectedly generated native wallet files");
                Console.WriteLine("PASS: " + count +
                    " actual Windows Forms layout, accessibility and release-lock checks; " +
                    "no user wallets, daemon, miner or network activated");
                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine("FAIL: isolated Windows Forms GUI QA: " +
                    ex.GetType().Name + " (" + ex.Message + ")");
                return 1;
            }
            finally
            {
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_ROOT", null);
                Environment.SetEnvironmentVariable("FRG_PRIVATE_UI_QA_BIN", null);
                try { Directory.Delete(qaRoot, true); } catch { }
            }
        }
    }
}
