use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    fs,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    time::Duration,
};

#[derive(Clone, Serialize, Deserialize)]
#[serde(default, rename_all = "camelCase")]
pub struct Settings {
    pub daemon_url: String,
    pub peer: String,
    pub xmrig_path: String,
    pub pool: String,
    pub tls: bool,
    pub threads: u16,
}
impl Default for Settings {
    fn default() -> Self {
        Self {
            daemon_url: "http://127.0.0.1:39481".into(),
            peer: String::new(), // No public fresh-mainnet peer exists before launch.
            xmrig_path: String::new(),
            pool: String::new(),
            tls: true,
            threads: 1,
        }
    }
}
pub struct Engine {
    _lock: fs::File,
    pub dir: PathBuf,
    pub settings: Settings,
    node: Option<Child>,
    wallet: Option<Child>,
    miner: Option<Child>,
    miner_api: Option<(u16, String)>,
    wallet_port: u16,
    login: Option<(String, String)>,
    opened: bool,
    refresh_enabled: bool,
    pending: Option<String>,
    solo: bool,
    client: Client,
}
fn error(e: impl std::fmt::Display) -> String {
    e.to_string()
}
fn command(path: &Path) -> Command {
    let mut c = Command::new(path);
    c.stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        c.creation_flags(0x08000000);
    }
    c
}
fn binary(name: &str) -> Result<PathBuf, String> {
    let installed = std::env::current_exe()
        .map_err(error)?
        .with_file_name(format!("{name}.exe"));
    if installed.is_file() {
        return Ok(installed);
    }
    #[cfg(debug_assertions)]
    {
        let dev = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("binaries")
            .join(format!("{name}-x86_64-pc-windows-msvc.exe"));
        if dev.is_file() {
            return Ok(dev);
        }
    }
    Err(format!(
        "Missing bundled {name}.exe. Rebuild the application with its sidecars."
    ))
}
fn running(child: &mut Option<Child>) -> bool {
    if let Some(c) = child {
        if matches!(c.try_wait(), Ok(None)) {
            return true;
        }
    }
    *child = None;
    false
}
fn stop(child: &mut Option<Child>) {
    if let Some(mut c) = child.take() {
        let _ = c.kill();
        let _ = c.wait();
    }
}
pub fn amount(value: &str) -> Result<u64, String> {
    let parts: Vec<_> = value.split('.').collect();
    if parts.len() > 2 || parts[0].is_empty() || !parts[0].bytes().all(|b| b.is_ascii_digit()) {
        return Err("Enter a positive amount with at most 8 decimal places.".into());
    }
    let fraction = parts.get(1).copied().unwrap_or("");
    if fraction.len() > 8 || !fraction.bytes().all(|b| b.is_ascii_digit()) {
        return Err("ForgeCoin uses 8 decimal places.".into());
    }
    let whole = parts[0].parse::<u64>().map_err(error)?;
    let fractional = format!("{fraction:0<8}").parse::<u64>().map_err(error)?;
    whole
        .checked_mul(100_000_000)
        .and_then(|v| v.checked_add(fractional))
        .filter(|v| *v > 0)
        .ok_or_else(|| "Amount is zero or too large.".into())
}
fn filename(s: &str) -> Result<(), String> {
    if s.is_empty()
        || s.len() > 64
        || !s
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || c == b'-' || c == b'_')
    {
        return Err("Wallet name must use 1–64 letters, digits, hyphens or underscores.".into());
    }
    Ok(())
}
fn validate_settings(s: &Settings) -> Result<(), String> {
    if !s.peer.is_empty() {
        let peer = reqwest::Url::parse(&format!("tcp://{}", s.peer)).map_err(error)?;
        if peer.host_str().is_none()
            || peer.port().is_none()
            || !peer.username().is_empty()
            || peer.password().is_some()
            || !matches!(peer.path(), "" | "/")
            || peer.query().is_some()
            || peer.fragment().is_some()
        {
            return Err("ForgeCoin peer must be host:port.".into());
        }
    }
    let u = reqwest::Url::parse(&s.daemon_url).map_err(error)?;
    if !matches!(u.scheme(), "http" | "https")
        || u.host_str().is_none()
        || !u.username().is_empty()
        || u.password().is_some()
        || u.query().is_some()
        || u.fragment().is_some()
        || u.path() != "/"
    {
        return Err("Node must be an HTTP(S) host and port without a path or credentials.".into());
    }
    if s.threads == 0 || s.threads > 256 {
        return Err("Choose 1–256 CPU threads.".into());
    }
    if !s.pool.is_empty() {
        let u = reqwest::Url::parse(&format!("stratum://{}", s.pool)).map_err(error)?;
        if u.host_str().is_none()
            || u.port().is_none()
            || !u.username().is_empty()
            || u.password().is_some()
            || !matches!(u.path(), "" | "/")
            || u.query().is_some()
            || u.fragment().is_some()
        {
            return Err("Pool must be host:port, without credentials or a path.".into());
        }
    }
    Ok(())
}
impl Engine {
    pub fn new(dir: PathBuf) -> Result<Self, String> {
        fs::create_dir_all(dir.join("wallets-mainnet-20261026")).map_err(error)?;
        let instance_lock = fs::OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(dir.join("desktop.lock"))
            .map_err(error)?;
        instance_lock
            .try_lock()
            .map_err(|_| "ForgeCoin Desktop is already using this data folder.".to_string())?;
        let mut settings: Settings = match fs::read(dir.join("settings.json")) {
            Ok(v) => serde_json::from_slice(&v).map_err(error)?,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Settings::default(),
            Err(e) => return Err(error(e)),
        };
        if settings.peer.trim().is_empty() {
            settings.peer = Settings::default().peer;
        }
        if settings.daemon_url.contains(":19481") || settings.peer.ends_with(":19480") {
            return Err("Retired development-network settings detected. Back up old wallets and choose RPC port 39481 and peer port 39480. Wallets and chain data are never migrated automatically.".into());
        }
        validate_settings(&settings)?;
        Ok(Self {
            _lock: instance_lock,
            dir,
            settings,
            node: None,
            wallet: None,
            miner: None,
            miner_api: None,
            wallet_port: 0,
            login: None,
            opened: false,
            refresh_enabled: false,
            pending: None,
            solo: false,
            client: Client::builder()
                .timeout(Duration::from_secs(30))
                .no_proxy()
                .redirect(reqwest::redirect::Policy::none())
                .build()
                .map_err(error)?,
        })
    }
    fn rpc(&self, wallet: bool, method: &str, params: Value) -> Result<Value, String> {
        let url = if wallet {
            format!("http://127.0.0.1:{}/json_rpc", self.wallet_port)
        } else {
            format!(
                "{}/json_rpc",
                self.settings.daemon_url.trim_end_matches('/')
            )
        };
        let body =
            json!({"jsonrpc":"2.0","id":"desktop","method":method,"params":params}).to_string();
        let send = || {
            self.client
                .post(&url)
                .header("Content-Type", "application/json")
                .body(body.clone())
        };
        // Never include wallet secrets in the unauthenticated challenge request.
        let mut response = if wallet {
            self.client
                .post(&url)
                .json(&json!({"jsonrpc":"2.0","id":"auth","method":"get_version"}))
                .send()
        } else {
            send().send()
        }
        .map_err(|_| {
            "Cannot reach RPC service. Check the node address and service status.".to_string()
        })?;
        if wallet {
            let (user, password) = self
                .login
                .as_ref()
                .ok_or("Wallet service is not connected.")?;
            if response.status() != 401 {
                return Err(
                    "Wallet RPC did not require authentication. Connection refused.".into(),
                );
            }
            let challenge = response
                .headers()
                .get("www-authenticate")
                .ok_or("Missing wallet authentication challenge.")?
                .to_str()
                .map_err(error)?;
            let mut prompt = digest_auth::parse(challenge).map_err(error)?;
            let context = digest_auth::AuthContext::new_post(
                user,
                password,
                "/json_rpc",
                Some(body.as_bytes()),
            );
            let auth = prompt.respond(&context).map_err(error)?.to_string();
            response = send().header("Authorization", auth).send().map_err(|_| {
                "Wallet RPC request failed; check transaction history before retrying a send."
                    .to_string()
            })?;
        }
        let data: Value = response
            .error_for_status()
            .map_err(error)?
            .json()
            .map_err(|_| "RPC returned an invalid response.".to_string())?;
        if let Some(e) = data.get("error") {
            return Err(format!(
                "RPC error {}: {}",
                e["code"],
                e["message"].as_str().unwrap_or("Unknown error")
            ));
        }
        data.get("result")
            .cloned()
            .ok_or_else(|| "RPC response is missing its result.".into())
    }
    fn daemon(&self, method: &str, params: Value) -> Result<Value, String> {
        let url = format!(
            "{}/{}",
            self.settings.daemon_url.trim_end_matches('/'),
            method
        );
        let data: Value = self
            .client
            .post(url)
            .json(&params)
            .send()
            .map_err(error)?
            .error_for_status()
            .map_err(error)?
            .json()
            .map_err(error)?;
        if data["status"] == "BUSY" {
            return Err("The node is still synchronizing. Wait until it is ready, then try again. If it stays here, stop and restart the local node in Settings.".into());
        }
        if data["status"] != "OK" {
            return Err(format!("Node: {}", data["status"]));
        }
        Ok(data)
    }
    fn start_wallet(&mut self) -> Result<(), String> {
        if running(&mut self.wallet) {
            return Ok(());
        }
        self.opened = false;
        self.pending = None;
        self.login = None;
        let listener = std::net::TcpListener::bind("127.0.0.1:0").map_err(error)?;
        self.wallet_port = listener.local_addr().map_err(error)?.port();
        drop(listener);
        let mut c = command(&binary("forge-wallet-rpc")?);
        c.current_dir(&self.dir)
            .args([
                "--rpc-bind-ip",
                "127.0.0.1",
                "--rpc-bind-port",
                &self.wallet_port.to_string(),
                "--wallet-dir",
            ])
            .arg(self.dir.join("wallets-mainnet-20261026"))
            .args([
                "--daemon-address",
                &self.settings.daemon_url,
                "--log-level",
                "0",
                "--log-file",
            ])
            .arg(self.dir.join("wallet-rpc.log"));
        self.wallet = Some(c.spawn().map_err(error)?);
        let login_path = self
            .dir
            .join(format!("monero-wallet-rpc.{}.login", self.wallet_port));
        for _ in 0..100 {
            if !running(&mut self.wallet) {
                return Err("Wallet RPC exited. Check its installation and wallet-rpc.log.".into());
            }
            if let Ok(login) = fs::read_to_string(&login_path) {
                if let Some((u, p)) = login.trim().split_once(':') {
                    self.login = Some((u.into(), p.into()));
                    if self.rpc(true, "get_version", json!({})).is_ok() {
                        self.rpc(true, "auto_refresh", json!({"enable":false}))?;
                        self.refresh_enabled = false;
                        return Ok(());
                    }
                }
            }
            std::thread::sleep(Duration::from_millis(100));
        }
        stop(&mut self.wallet);
        self.login = None;
        Err("Wallet RPC did not become ready.".into())
    }
    pub fn action(&mut self, action: &str, p: Value) -> Result<Value, String> {
        let text = |key: &str| p[key].as_str().unwrap_or("").to_string();
        match action {
            "status" => {
                let node = running(&mut self.node);
                let wallet = running(&mut self.wallet);
                let pool = running(&mut self.miner);
                let node_info = self
                    .client
                    .post(format!(
                        "{}/json_rpc",
                        self.settings.daemon_url.trim_end_matches('/')
                    ))
                    .timeout(Duration::from_secs(2))
                    .json(&json!({"jsonrpc":"2.0","id":"health","method":"get_info"}))
                    .send()
                    .ok()
                    .and_then(|r| r.json::<Value>().ok())
                    .map(|v| v["result"].clone())
                    .unwrap_or(Value::Null);
                let node_connected = node_info["status"] == "OK";
                let node_ready = node_connected && node_info["synchronized"] == true;
                if wallet && self.opened && node_connected != self.refresh_enabled {
                    self.rpc(true, "auto_refresh", json!({"enable":node_connected}))?;
                    self.refresh_enabled = node_connected;
                }
                if !wallet {
                    self.opened = false;
                    self.pending = None;
                    self.login = None;
                }
                Ok(
                    json!({"node":node,"nodeConnected":node_connected,"nodeReady":node_ready,"nodeHeight":node_info["height"],"nodeDifficulty":node_info["difficulty"],"nodeTargetSeconds":node_info["target"],"nodeTarget":node_info["target_height"],"wallet":self.opened,"pool":pool,"solo":self.solo,"settings":self.settings,"walletDirectory":self.dir.join("wallets-mainnet-20261026")}),
                )
            }
            "wallet_names" => {
                let mut names = Vec::new();
                for entry in fs::read_dir(self.dir.join("wallets-mainnet-20261026")).map_err(error)? {
                    let entry = entry.map_err(error)?;
                    if !entry.file_type().map_err(error)?.is_file() {
                        continue;
                    }
                    let path = entry.path();
                    if path.extension().and_then(|s| s.to_str()) != Some("keys") {
                        continue;
                    }
                    if let Some(name) = path.file_stem().and_then(|s| s.to_str()) {
                        if filename(name).is_ok() {
                            names.push(name.to_string());
                        }
                    }
                }
                names.sort();
                names.dedup();
                Ok(json!(names))
            }
            "set_threads" => {
                let threads = p["threads"]
                    .as_u64()
                    .filter(|n| (1..=256).contains(n))
                    .ok_or("Choose a whole number from 1 to 256 CPU threads.")?;
                let mut settings = self.settings.clone();
                settings.threads = threads as u16;
                fs::write(
                    self.dir.join("settings.json"),
                    serde_json::to_vec_pretty(&settings).map_err(error)?,
                )
                .map_err(error)?;
                self.settings = settings;
                Ok(json!(true))
            }
            "settings" => {
                if running(&mut self.node) {
                    return Err("Stop the local node before changing settings.".into());
                }
                if running(&mut self.wallet) || running(&mut self.miner) || self.solo {
                    return Err("Close the wallet and stop mining before changing settings.".into());
                }
                let s: Settings = serde_json::from_value(p).map_err(error)?;
                validate_settings(&s)?;
                fs::write(
                    self.dir.join("settings.json"),
                    serde_json::to_vec_pretty(&s).map_err(error)?,
                )
                .map_err(error)?;
                self.settings = s;
                Ok(json!(true))
            }
            "start_node" => {
                if self.settings.peer.is_empty() {
                    return Err(
                        "Set a trusted ForgeCoin P2P peer in Settings before starting the node."
                            .into(),
                    );
                }
                if running(&mut self.node) {
                    return Ok(json!(true));
                }
                fs::create_dir_all(self.dir.join("chain-mainnet-20261026")).map_err(error)?;
                self.node = Some(
                    command(&binary("forged")?)
                        .args(["--data-dir"])
                        .arg(self.dir.join("chain-mainnet-20261026"))
                        .args([
                            "--p2p-bind-ip",
                            "0.0.0.0",
                            "--p2p-bind-port",
                            "39480",
                            "--rpc-bind-ip",
                            "127.0.0.1",
                            "--rpc-bind-port",
                            "39481",
                            "--no-igd",
                            "--add-exclusive-node",
                            &self.settings.peer,
                            // ForgeCoin must not use inherited Monero checkpoint hashes.
                            "--fast-block-sync",
                            "0",
                            "--disable-dns-checkpoints",
                            "--check-updates",
                            "disabled",
                            "--non-interactive",
                            "--log-level",
                            "0",
                        ])
                        .spawn()
                        .map_err(error)?,
                );
                Ok(json!(true))
            }
            "stop_node" => {
                if self.solo {
                    self.daemon("stop_mining", json!({}))?;
                    self.solo = false;
                }
                stop(&mut self.node);
                Ok(json!(true))
            }
            "node_info" => self.rpc(false, "get_info", json!({})),
            "open" | "create" | "restore" => {
                if self.opened {
                    return Err("Close the current wallet first.".into());
                }
                let name = text("name");
                filename(&name)?;
                let password = text("password");
                if password.is_empty() {
                    return Err("A wallet password is required.".into());
                }
                self.start_wallet()?;
                let method = match action {
                    "create" => "create_wallet",
                    "restore" => "restore_deterministic_wallet",
                    _ => "open_wallet",
                };
                let mut params = json!({"filename":name,"password":password});
                if action == "create" {
                    params["language"] = json!("English");
                }
                if action == "restore" {
                    if text("seed").split_whitespace().count() != 25 {
                        return Err("Enter the 25-word recovery phrase.".into());
                    }
                    params["seed"] = json!(text("seed"));
                    params["restore_height"] = json!(p["height"].as_u64().unwrap_or(0));
                }
                self.rpc(true, method, params)?;
                self.opened = true;
                self.pending = None;
                Ok(json!(true))
            }
            "close" => {
                if self.opened {
                    self.rpc(true, "store", json!({}))?;
                    self.rpc(true, "close_wallet", json!({}))?;
                }
                self.opened = false;
                self.pending = None;
                stop(&mut self.wallet);
                self.login = None;
                Ok(json!(true))
            }
            "balance" => {
                let v = self.rpc(true, "get_balance", json!({"account_index":0}))?;
                Ok(
                    json!({"balance":v["balance"].as_u64().ok_or("Missing balance")?.to_string(),"unlocked":v["unlocked_balance"].as_u64().ok_or("Missing unlocked balance")?.to_string(),"height":self.rpc(true,"get_height",json!({}))?["height"]}),
                )
            }
            "address" => self.rpc(true, "get_address", json!({"account_index":0})),
            "history" => {
                let data=self.rpc(true,"get_transfers",json!({"in":true,"out":true,"pending":true,"failed":true,"pool":false,"account_index":0}))?;
                let mut rows = Vec::new();
                for kind in ["in", "out", "pending", "failed", "pool"] {
                    if let Some(items) = data[kind].as_array() {
                        for item in items {
                            rows.push(json!({"txid":item["txid"],"kind":kind,"amount":item["amount"].as_u64().unwrap_or(0).to_string(),"fee":item["fee"].as_u64().unwrap_or(0).to_string(),"height":item["height"],"timestamp":item["timestamp"]}));
                        }
                    }
                }
                rows.sort_by_key(|v| std::cmp::Reverse(v["timestamp"].as_u64().unwrap_or(0)));
                Ok(json!(rows))
            }
            "seed" => self.rpc(true, "query_key", json!({"key_type":"mnemonic"})),
            "prepare" => {
                self.pending = None;
                let address = text("address");
                let atomic = amount(&text("amount"))?;
                let valid = self.rpc(
                    true,
                    "validate_address",
                    json!({"address":address,"any_net_type":false,"allow_openalias":false}),
                )?;
                if valid["valid"] != true {
                    return Err("Invalid ForgeCoin mainnet address.".into());
                }
                let v=self.rpc(true,"transfer",json!({"destinations":[{"address":address,"amount":atomic}],"account_index":0,"priority":0,"do_not_relay":true,"get_tx_metadata":true}))?;
                let fee = v["fee"].as_u64().ok_or("Missing fee")?;
                self.pending = Some(
                    v["tx_metadata"]
                        .as_str()
                        .filter(|s| !s.is_empty())
                        .ok_or("Wallet did not return transaction metadata.")?
                        .into(),
                );
                Ok(json!({"address":address,"amount":atomic.to_string(),"fee":fee.to_string()}))
            }
            "cancel" => {
                self.pending = None;
                Ok(json!(true))
            }
            "send" => {
                let metadata = self.pending.take().ok_or("Review a transaction first.")?;
                let v = self.rpc(true, "relay_tx", json!({"hex":metadata}))?;
                Ok(json!({"txid":v["tx_hash"]}))
            }
            "start_solo" => {
                return Err("Fresh mainnet has not launched: solo mining is deliberately disabled.".into());
                if running(&mut self.miner) || self.solo {
                    return Err("Stop the active miner first.".into());
                }
                let u = reqwest::Url::parse(&self.settings.daemon_url).map_err(error)?;
                if !matches!(u.host_str(), Some("127.0.0.1" | "localhost" | "[::1]")) {
                    return Err("Solo mining requires a local ForgeCoin node.".into());
                }
                let info = self.rpc(false, "get_info", json!({}))
                    .map_err(|_| "Cannot reach the local node. Start it in Settings and wait for synchronization.".to_string())?;
                if info["synchronized"] != true {
                    return Err("The local node is still synchronizing. Wait for Ready before starting Solo mining. If it stays here, stop and restart the node in Settings.".into());
                }
                let address = self.rpc(true, "get_address", json!({"account_index":0}))?["address"]
                    .as_str()
                    .ok_or("Open a wallet first.")?
                    .to_string();
                self.daemon("start_mining",json!({"miner_address":address,"threads_count":self.settings.threads,"do_background_mining":false,"ignore_battery":false}))?;
                self.solo = true;
                Ok(json!(true))
            }
            "start_pool" => {
                return Err("Fresh mainnet has not launched: pool mining is deliberately disabled.".into());
                if running(&mut self.miner) || self.solo {
                    return Err("Stop the active miner first.".into());
                }
                validate_settings(&self.settings)?;
                if self.settings.pool.is_empty() {
                    return Err("Set a third-party ForgeCoin pool in Settings first.".into());
                }
                let path = Path::new(&self.settings.xmrig_path);
                if !path.is_absolute()
                    || !path.is_file()
                    || path
                        .file_name()
                        .and_then(|n| n.to_str())
                        .map(|n| n.eq_ignore_ascii_case("xmrig.exe"))
                        != Some(true)
                {
                    return Err(
                        "Choose the full path to your trusted xmrig.exe in Settings.".into(),
                    );
                }
                let address = self.rpc(true, "get_address", json!({"account_index":0}))?["address"]
                    .as_str()
                    .ok_or("Open a wallet first.")?
                    .to_string();
                let listener = std::net::TcpListener::bind("127.0.0.1:0").map_err(error)?;
                let api_port = listener.local_addr().map_err(error)?.port();
                let api_token = rand::random::<[u8; 32]>()
                    .iter()
                    .map(|b| format!("{b:02x}"))
                    .collect::<String>();
                drop(listener);
                // Monitoring is authenticated, read-only, and bound only to loopback.
                // An explicit config prevents inheriting another installation's pools or HTTP API.
                let config = json!({"autosave":false,"background":false,"colors":false,
                    "http":{"enabled":true,"host":"127.0.0.1","port":api_port,"access-token":api_token,"restricted":true},"randomx":{"rdmsr":false,"wrmsr":false},
                    "cpu":{"enabled":true,"rx":vec![-1;usize::from(self.settings.threads)]},
                    "opencl":false,"cuda":false,
                    "pools":[{"algo":"rx/0","url":self.settings.pool,"user":address,"pass":"x","tls":self.settings.tls,"enabled":true}],
                    "log-file":self.dir.join("miner.log")});
                let config_path = self.dir.join("miner.json");
                fs::write(
                    &config_path,
                    serde_json::to_vec_pretty(&config).map_err(error)?,
                )
                .map_err(error)?;
                let mut c = command(path);
                c.current_dir(&self.dir).arg("--config").arg(config_path);
                self.miner = Some(c.spawn().map_err(|e| if e.raw_os_error()==Some(740) { "XMRig requires administrator launch. Use a trusted standard XMRig build without the Windows Run as administrator compatibility flag; the wallet app runs without elevation.".into() } else { error(e) })?);
                self.miner_api = Some((api_port, api_token));
                Ok(json!(true))
            }
            "stop_mining" => {
                stop(&mut self.miner);
                self.miner_api = None;
                if self.solo {
                    self.daemon("stop_mining", json!({}))?;
                    self.solo = false;
                }
                Ok(json!(true))
            }
            "mining_live" => match p["mode"].as_str().unwrap_or("solo") {
                "solo" => {
                    let info = self
                        .client
                        .post(format!(
                            "{}/mining_status",
                            self.settings.daemon_url.trim_end_matches('/')
                        ))
                        .timeout(Duration::from_secs(1))
                        .json(&json!({}))
                        .send()
                        .ok()
                        .and_then(|r| r.error_for_status().ok())
                        .and_then(|r| r.json::<Value>().ok());
                    match info.filter(|v| v["status"] == "OK") {
                        Some(v) => Ok(
                            json!({"state":if v["active"] == true {"Mining"} else {"Stopped"},"running":v["active"],"speed":v["speed"],"threads":v["threads_count"],"apiAvailable":true}),
                        ),
                        None => Ok(
                            json!({"state":"Node unavailable","running":false,"speed":null,"apiAvailable":false}),
                        ),
                    }
                }
                "pool" => {
                    if !running(&mut self.miner) {
                        self.miner_api = None;
                        return Ok(
                            json!({"state":"Stopped","running":false,"speed":0,"apiAvailable":false}),
                        );
                    }
                    let info = self.miner_api.as_ref().and_then(|(port, token)| {
                        self.client
                            .get(format!("http://127.0.0.1:{port}/2/summary"))
                            .bearer_auth(token)
                            .timeout(Duration::from_secs(1))
                            .send()
                            .ok()
                            .and_then(|r| r.error_for_status().ok())
                            .and_then(|r| r.json::<Value>().ok())
                    });
                    match info {
                        Some(v) => Ok(
                            json!({"state":if v["paused"] == true {"Paused"} else if v["hashrate"]["total"][0].as_f64().unwrap_or(0.0) > 0.0 {"Mining"} else {"Starting / waiting for work"},"running":true,"speed":v["hashrate"]["total"][0],"accepted":v["results"]["shares_good"],"apiAvailable":true}),
                        ),
                        None => Ok(
                            json!({"state":"Process running; statistics unavailable","running":true,"speed":null,"apiAvailable":false}),
                        ),
                    }
                }
                _ => Err("Choose Solo or Pool mining.".into()),
            },
            "mining_info" => self.daemon("mining_status", json!({})),
            "miner_log" => {
                use std::io::{Read, Seek, SeekFrom};
                let path = match p["mode"].as_str().unwrap_or("pool") {
                    "solo" => self.dir.join("chain-mainnet-20261026").join("forgecoin.log"),
                    "pool" => self.dir.join("miner.log"),
                    _ => return Err("Choose Solo or Pool mining for the activity log.".into()),
                };
                let mut file = match fs::File::open(path) {
                    Ok(file) => file,
                    Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(json!("No activity yet. Start the local node for Solo mining, or start your configured pool miner.")),
                    Err(e) => return Err(format!("Unable to read mining activity: {e}")),
                };
                let length = file.metadata().map_err(error)?.len();
                file.seek(SeekFrom::Start(length.saturating_sub(12000)))
                    .map_err(error)?;
                let mut bytes = Vec::new();
                file.take(12000).read_to_end(&mut bytes).map_err(error)?;
                Ok(json!(String::from_utf8_lossy(&bytes)
                    .lines()
                    .rev()
                    .take(60)
                    .collect::<Vec<_>>()
                    .into_iter()
                    .rev()
                    .collect::<Vec<_>>()
                    .join("\n")))
            }
            _ => Err("Unknown desktop action.".into()),
        }
    }
}
impl Drop for Engine {
    fn drop(&mut self) {
        if self.solo {
            let _ = self.daemon("stop_mining", json!({}));
        }
        stop(&mut self.miner);
        if self.opened {
            let _ = self.rpc(true, "store", json!({}));
            let _ = self.rpc(true, "close_wallet", json!({}));
        }
        stop(&mut self.wallet);
        stop(&mut self.node);
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn mining_logs_select_source_and_refresh() {
        let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("target")
            .join(format!("log-smoke-{}", std::process::id()));
        let mut e = Engine::new(dir).unwrap();
        assert!(e
            .action("miner_log", json!({"mode":"solo"}))
            .unwrap()
            .as_str()
            .unwrap()
            .contains("No activity yet"));
        fs::create_dir_all(e.dir.join("chain")).unwrap();
        fs::write(e.dir.join("chain/forgecoin.log"), "Solo found block").unwrap();
        fs::write(e.dir.join("miner.log"), "Pool accepted share").unwrap();
        assert_eq!(
            e.action("miner_log", json!({"mode":"solo"})).unwrap(),
            "Solo found block"
        );
        assert_eq!(
            e.action("miner_log", json!({"mode":"pool"})).unwrap(),
            "Pool accepted share"
        );
        fs::write(
            e.dir.join("miner.log"),
            (0..100).map(|n| format!("entry {n}\n")).collect::<String>(),
        )
        .unwrap();
        let log = e.action("miner_log", json!({"mode":"pool"})).unwrap();
        assert_eq!(log.as_str().unwrap().lines().count(), 60);
        assert!(log.as_str().unwrap().ends_with("entry 99"));
        assert!(e.action("miner_log", json!({"mode":"../wallets"})).is_err());
    }
    #[test]
    fn exact_amounts() {
        assert_eq!(amount("0.00000001").unwrap(), 1);
        assert_eq!(amount("90071992.54740993").unwrap(), 9007199254740993);
        assert_eq!(amount("1.25").unwrap(), 125000000);
    }
    #[test]
    fn rejects_bad_amounts() {
        for s in [
            "0",
            "-1",
            "NaN",
            "1e2",
            "1.000000001",
            "184467440738",
            "1.2.3",
            ".1",
        ] {
            assert!(amount(s).is_err(), "{s}");
        }
    }
    #[test]
    fn rejects_paths_and_urls() {
        assert!(filename("../wallet").is_err());
        let mut s = Settings::default();
        s.pool = "host:123/path".into();
        assert!(validate_settings(&s).is_err());
        s.pool = "pool.example:3333".into();
        assert!(validate_settings(&s).is_ok());
        s.daemon_url = "file:///wallet".into();
        assert!(validate_settings(&s).is_err());
    }
    #[test]
    #[ignore = "Requires externally enforced egress denial; protocol fixture is not PoW acceptance"]
    fn offline_mining_compatibility() {
        // This acknowledgement is a prerequisite, not enforcement. A host firewall
        // or disconnected VM must deny non-loopback egress before any launch.
        assert_eq!(
            std::env::var("FORGE_TEST_EGRESS_DENIED").as_deref(),
            Ok("externally-enforced"),
            "Establish OS-level non-loopback egress denial before running this test"
        );
        let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("target")
            .join(format!("mining-smoke-{}", std::process::id()));
        let mut e = Engine::new(dir).unwrap();
        let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
        let port = listener.local_addr().unwrap().port();
        drop(listener);
        e.settings.daemon_url = format!("http://127.0.0.1:{port}");
        fs::create_dir_all(e.dir.join("chain")).unwrap();
        e.node = Some(
            command(&binary("forged").unwrap())
                .arg("--data-dir")
                .arg(e.dir.join("chain"))
                .args([
                    "--offline",
                    "--fixed-difficulty",
                    "100",
                    "--rpc-bind-ip",
                    "127.0.0.1",
                    "--rpc-bind-port",
                    &port.to_string(),
                    "--no-igd",
                    "--no-zmq",
                    "--non-interactive",
                    "--disable-dns-checkpoints",
                    "--check-updates",
                    "disabled",
                    "--log-level",
                    "0",
                ])
                .spawn()
                .unwrap(),
        );
        let mut ready = false;
        for _ in 0..60 {
            if e.rpc(false, "get_info", json!({})).is_ok() {
                ready = true;
                break;
            }
            std::thread::sleep(Duration::from_millis(250));
        }
        assert!(ready, "Offline node failed to start");
        assert_eq!(
            e.rpc(false, "hard_fork_info", json!({"version":17}))
                .unwrap()["earliest_height"],
            500,
            "Bundled node must schedule the difficulty upgrade at block 500"
        );
        assert_eq!(
            e.rpc(false, "hard_fork_info", json!({"version":18}))
                .unwrap()["earliest_height"],
            600,
            "Bundled node must schedule the million difficulty upgrade at block 600"
        );
        assert_eq!(
            e.rpc(false, "hard_fork_info", json!({"version":19}))
                .unwrap()["earliest_height"],
            700,
            "Bundled node must schedule LWMA at block 700"
        );
        e.action(
            "create",
            json!({"name":"mining-test","password":"disposable-test-password"}),
        )
        .unwrap();
        let address = e.action("address", json!({})).unwrap()["address"].clone();
        assert_eq!(e.action("history", json!({})).unwrap(), json!([]));
        let template = e
            .rpc(
                false,
                "get_block_template",
                json!({"wallet_address":address,"reserve_size":8}),
            )
            .unwrap();
        assert_eq!(template["seed_hash"].as_str().unwrap().len(), 64);
        assert!(
            template["blockhashing_blob"]
                .as_str()
                .unwrap()
                .starts_with("10"),
            "Expected v16 / RandomX block template"
        );
        let previous_url = e.settings.daemon_url.clone();
        e.action("set_threads", json!({"threads":2}))
            .expect("Thread changes must work with wallet and node running");
        assert_eq!(e.settings.daemon_url, previous_url);
        for invalid in [json!(0), json!(257), json!(1.5), json!(-1)] {
            assert!(e.action("set_threads", json!({"threads":invalid})).is_err());
        }
        assert_eq!(e.settings.threads, 2);
        let saved: Settings =
            serde_json::from_slice(&fs::read(e.dir.join("settings.json")).unwrap()).unwrap();
        assert_eq!(saved.threads, 2);
        e.action("start_solo", json!({})).unwrap();
        assert_eq!(e.action("mining_info", json!({})).unwrap()["active"], true);
        assert_eq!(
            e.action("mining_live", json!({"mode":"solo"})).unwrap()["state"],
            "Mining"
        );
        assert_eq!(
            e.action("mining_info", json!({})).unwrap()["threads_count"],
            2
        );
        e.action("set_threads", json!({"threads":1})).unwrap();
        assert_eq!(
            e.action("mining_info", json!({})).unwrap()["threads_count"],
            2,
            "Saving must not interrupt the active miner"
        );
        let mut mined = false;
        for _ in 0..120 {
            if e.rpc(false, "get_info", json!({})).unwrap()["height"]
                .as_u64()
                .unwrap()
                > 1
            {
                mined = true;
                break;
            }
            std::thread::sleep(Duration::from_millis(500));
        }
        e.action("stop_mining", json!({})).unwrap();
        assert!(mined, "Solo miner did not find an offline block");
        assert_eq!(e.action("mining_info", json!({})).unwrap()["active"], false);
        e.rpc(true, "refresh", json!({}))
            .expect("Wallet must scan ForgeCoin v16 blocks from height 1");
        let reward_balance = e.action("balance", json!({})).unwrap();
        assert!(
            reward_balance["balance"]
                .as_str()
                .unwrap()
                .parse::<u64>()
                .unwrap()
                > 0,
            "Mined rewards must appear in total balance"
        );
        assert_eq!(
            reward_balance["unlocked"], "0",
            "New mining rewards must remain locked"
        );
        assert!(
            !e.action("history", json!({}))
                .unwrap()
                .as_array()
                .unwrap()
                .is_empty(),
            "Mined rewards must appear in history"
        );
        if let Ok(path) = std::env::var("FORGE_TEST_XMRIG") {
            let config = json!({"autosave":false,"colors":false,"donate-level":0,"http":{"enabled":false},"randomx":{"rdmsr":false,"wrmsr":false,"mode":"light"},"cpu":{"enabled":true,"rx":[-1]},"opencl":false,"cuda":false,"pools":[{"algo":"rx/0","coin":"monero","url":format!("127.0.0.1:{port}"),"user":address,"daemon":true}],"log-file":e.dir.join("xmrig-test.log")});
            let config_path = e.dir.join("xmrig-test.json");
            fs::write(&config_path, serde_json::to_vec(&config).unwrap()).unwrap();
            e.miner = Some(
                command(Path::new(&path))
                    .arg("--config")
                    .arg(config_path)
                    .spawn()
                    .unwrap(),
            );
            let mut accepted = false;
            for _ in 0..120 {
                assert!(running(&mut e.miner), "XMRig exited unexpectedly");
                if let Ok(log) = fs::read_to_string(e.dir.join("xmrig-test.log")) {
                    assert!(
                        !log.contains("algo rx/graft"),
                        "ForgeCoin must use standard RandomX, not address-based coin autodetection"
                    );
                    if log.contains("accepted (") {
                        accepted = true;
                        break;
                    }
                }
                std::thread::sleep(Duration::from_millis(500));
            }
            stop(&mut e.miner);
            assert!(
                accepted,
                "XMRig did not produce an accepted offline block within 60 seconds"
            );
            // Protocol smoke test only: this fixture does not validate RandomX PoW.
            use std::io::{BufRead, BufReader, Write};
            let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
            listener.set_nonblocking(true).unwrap();
            e.settings.pool = listener.local_addr().unwrap().to_string();
            e.settings.xmrig_path = path;
            e.settings.tls = false;
            let expected_address = address.clone();
            let server = std::thread::spawn(move || {
                let started = std::time::Instant::now();
                let mut stream = loop {
                    if let Ok((stream, _)) = listener.accept() {
                        break stream;
                    }
                    assert!(started.elapsed() < Duration::from_secs(15), "No pool login");
                    std::thread::sleep(Duration::from_millis(50));
                };
                stream.set_nonblocking(false).unwrap();
                stream
                    .set_read_timeout(Some(Duration::from_secs(45)))
                    .unwrap();
                let mut reader = BufReader::new(stream.try_clone().unwrap());
                let mut line = String::new();
                reader.read_line(&mut line).unwrap();
                let login: Value = serde_json::from_str(&line).unwrap();
                assert_eq!(login["method"], "login");
                assert_eq!(login["params"]["login"], expected_address);
                let response = json!({"id":login["id"],"jsonrpc":"2.0","error":null,"result":{"id":"test","status":"OK","job":{"blob":template["blockhashing_blob"],"job_id":"offline-test","target":"ffffffff","seed_hash":template["seed_hash"],"height":template["height"],"algo":"rx/0"}}});
                writeln!(stream, "{response}").unwrap();
                line.clear();
                reader.read_line(&mut line).unwrap();
                let share: Value = serde_json::from_str(&line).unwrap();
                assert_eq!(share["method"], "submit");
                assert_eq!(share["params"]["job_id"], "offline-test");
                writeln!(
                    stream,
                    "{}",
                    json!({"id":share["id"],"jsonrpc":"2.0","error":null,"result":{"status":"OK"}})
                )
                .unwrap();
                std::thread::sleep(Duration::from_millis(200));
            });
            e.action("start_pool", json!({})).unwrap();
            server.join().unwrap();
            assert!(e
                .action("miner_log", json!({}))
                .unwrap()
                .as_str()
                .unwrap()
                .contains("accepted ("));
            let live = e.action("mining_live", json!({"mode":"pool"})).unwrap();
            assert_eq!(
                live["apiAvailable"], true,
                "XMRig live statistics must be readable"
            );
            assert_eq!(live["running"], true);
            let (api_port, _) = e.miner_api.as_ref().unwrap();
            assert_eq!(
                e.client
                    .get(format!("http://127.0.0.1:{api_port}/2/summary"))
                    .send()
                    .unwrap()
                    .status()
                    .as_u16(),
                401,
                "Statistics require authentication"
            );
            e.action("stop_mining", json!({})).unwrap();
            assert!(!running(&mut e.miner));
            assert_eq!(
                e.action("mining_live", json!({"mode":"pool"})).unwrap()["state"],
                "Stopped"
            );
        }
        e.action("close", json!({})).unwrap();
    }
    #[test]
    #[ignore = "Starts bundled wallet RPC using disposable wallets, never existing wallets"]
    fn wallet_roundtrip() {
        let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("target")
            .join(format!("wallet-smoke-{}", std::process::id()));
        let mut e = Engine::new(dir).unwrap();
        e.action(
            "create",
            json!({"name":"smoke","password":"disposable-test-password"}),
        )
        .unwrap();
        assert_eq!(
            e.action("wallet_names", json!({})).unwrap(),
            json!(["smoke"])
        );
        let address = e.action("address", json!({})).unwrap()["address"].clone();
        assert_eq!(e.action("balance", json!({})).unwrap()["balance"], "0");
        let seed = e.action("seed", json!({})).unwrap()["key"].clone();
        assert_eq!(seed.as_str().unwrap().split_whitespace().count(), 25);
        e.action("close", json!({})).unwrap();
        assert!(e
            .action("open", json!({"name":"smoke","password":"wrong"}))
            .is_err());
        e.action(
            "open",
            json!({"name":"smoke","password":"disposable-test-password"}),
        )
        .unwrap();
        assert_eq!(e.action("address", json!({})).unwrap()["address"], address);
        e.action("close", json!({})).unwrap();
        e.action(
            "restore",
            json!({"name":"restored","password":"disposable-test-password","seed":seed,"height":0}),
        )
        .unwrap();
        assert_eq!(e.action("address", json!({})).unwrap()["address"], address);
        e.action("close", json!({})).unwrap();
    }
}
