import { useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import "./App.css";

type Settings = { daemonUrl: string; peer: string; xmrigPath: string; pool: string; tls: boolean; threads: number };
type Status = { node: boolean; nodeConnected: boolean; nodeReady: boolean; nodeHeight: number | null; nodeDifficulty: number | null; nodeTargetSeconds: number | null; nodeTarget: number | null; wallet: boolean; pool: boolean; solo: boolean; settings: Settings; walletDirectory: string };
type Balance = { balance: string; unlocked: string; height: number };
type Tx = { txid: string; kind: string; amount: string; fee: string; timestamp: number; height: number };
type Review = { address: string; amount: string; fee: string };
const defaults: Settings = { daemonUrl: "http://127.0.0.1:39481", peer: "", xmrigPath: "", pool: "", tls: true, threads: 1 };
const rpc = <T,>(action: string, params?: unknown) => invoke<T>("desktop", { action, params });
function coins(value: string) { const n=BigInt(value); return `${n/100000000n}.${(n%100000000n).toString().padStart(8,"0")}`; }

export default function App() {
  const [page,setPage]=useState("Wallet"), [tab,setTab]=useState("Overview");
  const [status,setStatus]=useState<Status>(), [settings,setSettings]=useState(defaults);
  const [walletNames,setWalletNames]=useState<string[]>([]);
  const [balance,setBalance]=useState<Balance>(), [address,setAddress]=useState(""), [history,setHistory]=useState<Tx[]>([]);
  const [busy,setBusy]=useState(false), [error,setError]=useState(""), [notice,setNotice]=useState("");
  const [mode,setMode]=useState("open"), [name,setName]=useState(""), [password,setPassword]=useState(""), [seed,setSeed]=useState(""), [height,setHeight]=useState("0");
  const [recovery,setRecovery]=useState(""), [recipient,setRecipient]=useState(""), [amount,setAmount]=useState(""), [review,setReview]=useState<Review>();
  const [miningMode,setMiningMode]=useState("solo"), [nodeInfo,setNodeInfo]=useState<{height:number; target_height:number; synchronized:boolean}>();
  const [miningLive,setMiningLive]=useState<{state:string;running:boolean;speed:number|null;threads?:number;accepted?:number;apiAvailable:boolean}>();
  const [miningLiveError,setMiningLiveError]=useState("");
  const [minerLog,setMinerLog]=useState(""), [liveLog,setLiveLog]=useState(true), [logError,setLogError]=useState("");
  const lock=useRef(false);
  const logView=useRef<HTMLPreElement>(null);
  async function refresh() {
    const s=await rpc<Status>("status"); setStatus(s);
    setWalletNames(await rpc<string[]>("wallet_names"));
    if(s.wallet) {
      const b=await rpc<Balance>("balance"); setBalance(b);
      const a=await rpc<{address:string}>("address"); setAddress(a.address);
      setHistory(await rpc<Tx[]>("history"));
    } else { setBalance(undefined); setAddress(""); setHistory([]); setRecovery(""); setReview(undefined); }
  }
  async function run(task:()=>Promise<void>) {
    if(lock.current) return; lock.current=true; setBusy(true); setError(""); setNotice("");
    try { await task(); } catch(e) { setError(String(e)); }
    finally { setBusy(false); lock.current=false; }
  }
  useEffect(()=> { void run(async()=> { const s=await rpc<Status>("status"); setStatus(s); setSettings(s.settings); await refresh(); });
    const timer=setInterval(()=> { if(!lock.current) { lock.current=true; setBusy(true); void refresh().catch(e=>setError(String(e))).finally(()=>{lock.current=false;setBusy(false);}); } },15000);
    return ()=>clearInterval(timer);
  },[]);
  useEffect(()=> {
    setMiningLive(undefined);setMiningLiveError("");
    if(page!=="Miner")return;
    let cancelled=false,reading=false;
    const update=async()=>{
      if(reading||lock.current)return;
      reading=true;
      try{const info=await rpc<{state:string;running:boolean;speed:number|null;threads?:number;accepted?:number;apiAvailable:boolean}>("mining_live",{mode:miningMode});if(!cancelled){setMiningLive(info);setMiningLiveError("");}}
      catch(e){if(!cancelled){setMiningLive(undefined);setMiningLiveError(String(e));}}
      finally{reading=false;}
    };
    void update();const timer=setInterval(()=>void update(),2000);
    return()=>{cancelled=true;clearInterval(timer);};
  },[page,miningMode]);
  useEffect(()=> {setMinerLog("");setLogError("");},[page,miningMode]);
  useEffect(()=> {if(liveLog&&logView.current)logView.current.scrollTop=logView.current.scrollHeight;},[minerLog,liveLog]);
  useEffect(()=> {
    if(page!=="Miner"||!liveLog) return;
    let cancelled=false, reading=false;
    const read=async()=> {
      if(reading||lock.current) return;
      reading=true;
      try { const log=await rpc<string>("miner_log",{mode:miningMode}); if(!cancelled){setMinerLog(log||"No activity yet.");setLogError("");} }
      catch(e){if(!cancelled)setLogError(String(e));}
      finally{reading=false;}
    };
    void read();
    const timer=liveLog?setInterval(()=>void read(),2000):undefined;
    return ()=>{cancelled=true;if(timer)clearInterval(timer);};
  },[page,miningMode,liveLog]);
  useEffect(()=> { setRecovery(""); },[page,tab]);
  useEffect(()=> { if(!recovery) return; const timer=setTimeout(()=>setRecovery(""),30000); const hide=()=>setRecovery(""); window.addEventListener("blur",hide); return ()=> {clearTimeout(timer);window.removeEventListener("blur",hide);}; },[recovery]);
  const act=(action:string)=>run(async()=> { await rpc(action); await refresh(); });
  const field=(key:keyof Settings,value:string|boolean|number)=>setSettings(s=>({...s,[key]:value}));
  const mining=Boolean(status?.pool||status?.solo);
  const threadControl=<form onSubmit={e=>{e.preventDefault();void run(async()=>{await rpc("set_threads",{threads:settings.threads});await refresh();setNotice(mining?"Thread count saved. Stop and start mining to apply it.":"Thread count saved. It will be used when mining starts.");});}}><label>CPU threads<input required type="number" min="1" max="256" step="1" value={settings.threads} onChange={e=>field("threads",Number(e.target.value))}/></label><button disabled={busy}>Save thread count</button><p className="hint">You can save this while your wallet and node are running. If mining is active, stop and start mining to apply the new count.</p></form>;
  return <div className="app">
    <aside><div className="brand"><span className="mark">F</span><div>ForgeCoin<small>DESKTOP WALLET</small></div></div>
      <nav aria-label="Main navigation">{["Wallet","Miner","Transactions","Settings"].map((p,i)=><button key={p} className={page===p?"active":""} onClick={()=>setPage(p)}><span>{["◈","⛏","↔","⚙"][i]}</span>{p}</button>)}</nav>
      <div className="sidebar-bottom"><span className={`dot ${status?.wallet?"online":""}`}/>{status?.wallet?"Wallet open":"Wallet closed"}<small>Mainnet · 8 decimal places</small></div>
    </aside>
    <main><header><div><p className="eyebrow">YOUR FORGECOIN, ON YOUR DESKTOP</p><h1>{page}</h1></div><button disabled={busy} onClick={()=>run(refresh)}>{busy?"Working…":"Refresh"}</button></header>
      {error&&<div className="alert" role="alert">{error}</div>}{notice&&<div className="notice" role="status">{notice}</div>}
      {page==="Wallet"&&<>
        {!status?.wallet?<section className="card narrow"><h2>Your wallet starts here</h2><p>Open an app wallet, create a new one, or recover with your phrase.</p>
          <div className="tabs">{["open","create","restore"].map(m=><button key={m} disabled={busy} className={mode===m?"selected":""} onClick={()=>{setMode(m);setPassword("");setSeed("");}}>{m==="open"?"Open":m==="create"?"Create":"Recover"}</button>)}</div>
          <form onSubmit={e=>{e.preventDefault();void run(async()=>{try {await rpc(mode,{name,password,seed,height:Number(height)});setTab(mode==="create"?"Recovery":"Overview");await refresh();setNotice(mode==="create"?"Wallet created. Back up your recovery phrase before receiving funds.":"Wallet opened.");} finally {setPassword("");setSeed("");}});}}>
            {mode==="open"?<><label>Saved wallet<select required value={walletNames.includes(name)?name:""} onChange={e=>setName(e.target.value)}><option value="" disabled>Select a wallet</option>{walletNames.map(walletName=><option key={walletName} value={walletName}>{walletName}</option>)}</select></label>{walletNames.length===0&&<p className="hint">No saved wallets found. Create or recover a wallet first.</p>}</>:<label>Wallet name<input required autoComplete="off" pattern="[A-Za-z0-9_-]{1,64}" value={name} onChange={e=>setName(e.target.value)} placeholder="MyWallet"/></label>}
            <label>{mode==="open"?"Password":"New wallet password"}<input required type="password" autoComplete="off" value={password} onChange={e=>setPassword(e.target.value)}/></label>
            {mode==="restore"&&<><label>25-word recovery phrase<textarea required spellCheck={false} autoComplete="off" value={seed} onChange={e=>setSeed(e.target.value)}/></label><label>Restore from block height<input required type="number" min="0" step="1" max={Number.MAX_SAFE_INTEGER} value={height} onChange={e=>setHeight(e.target.value)}/></label><p className="hint">Use 0 if you do not know the wallet’s creation height.</p></>}
            <p className="hint">{mode==="open"?"Select your saved wallet and enter its password to open it. Keep your wallet name and password in a safe place.":"Keep a record of your wallet name and password. You will need the password to open this wallet again."}</p><button className="primary" disabled={busy||(mode==="open"&&walletNames.length===0)}>{mode==="open"?"Open wallet":mode==="create"?"Create wallet":"Recover wallet"}</button>
          </form><p className="hint">Encrypted wallet files stay on this computer. Passwords and recovery phrases are never saved in app settings.</p>
        </section>:<>
          <div className="balance-grid"><section className="card balance"><p>Available to send</p><div className="big-number">{balance?coins(balance.unlocked):"—"}<span>FORGE</span></div><p>Total balance <strong>{balance?coins(balance.balance):"—"}</strong></p>{balance&&BigInt(balance.balance)>BigInt(balance.unlocked)&&<p>Locked balance <strong>{coins((BigInt(balance.balance)-BigInt(balance.unlocked)).toString())}</strong><small> Mining rewards unlock after 60 blocks. Other incoming funds may also be temporarily locked.</small></p>}</section><section className="card"><p>Wallet scan height</p><h2>{balance?.height.toLocaleString()??"—"}</h2><p className="hint">{status?.nodeConnected?"Connected to node. Balances reflect scanned blocks; check sync before sending.":"Node offline. Showing saved balances. Start the local node in Settings to sync."}</p><button disabled={busy} onClick={()=>act("close")}>Close wallet</button></section></div>
          <div className="tabs">{["Overview","Send","Receive","Recovery"].map(t=><button className={tab===t?"selected":""} key={t} onClick={()=>setTab(t)}>{t}</button>)}</div>
          {tab==="Overview"&&<section className="card"><h2>Ready when you are</h2><p>Receive ForgeCoin at your address, review a payment before sending, or put your CPU to work.</p><div className="actions"><button className="primary" onClick={()=>setTab("Receive")}>Receive ForgeCoin</button><button onClick={()=>setTab("Send")}>Send</button><button onClick={()=>setPage("Miner")}>Open miner</button></div></section>}
          {tab==="Receive"&&<section className="card"><h2>Your receive address</h2><p>Use this address for ForgeCoin mainnet payments and mining rewards.</p><textarea aria-label="Receive address" readOnly className="address" value={address}/><button onClick={()=>run(async()=>{await navigator.clipboard.writeText(address);setNotice("Address copied.");})}>Copy address</button></section>}
          {tab==="Send"&&<section className="card narrow"><h2>Send ForgeCoin</h2>{review?<><p>Review this payment. Confirmation broadcasts it to the network.</p><label>Recipient<textarea readOnly value={review.address}/></label><p>Amount <strong>{coins(review.amount)} FORGE</strong></p><p>Network fee <strong>{coins(review.fee)} FORGE</strong></p><p>Total <strong>{coins((BigInt(review.amount)+BigInt(review.fee)).toString())} FORGE</strong></p><div className="actions"><button className="primary" disabled={busy} onClick={()=>run(async()=>{try {const v=await rpc<{txid:string}>("send");setNotice(`Payment submitted: ${v.txid}`);setRecipient("");setAmount("");await refresh();} finally {setReview(undefined);}})}>Confirm and send</button><button disabled={busy} onClick={()=>run(async()=>{await rpc("cancel");setReview(undefined);})}>Cancel</button></div></>:<form onSubmit={e=>{e.preventDefault();void run(async()=>setReview(await rpc<Review>("prepare",{address:recipient,amount})));}}><label>Recipient address<input required autoComplete="off" value={recipient} onChange={e=>setRecipient(e.target.value)}/></label><label>Amount (FORGE)<input required inputMode="decimal" pattern="[0-9]+(\.[0-9]{1,8})?" value={amount} onChange={e=>setAmount(e.target.value)} placeholder="0.00000000"/></label><button className="primary" disabled={busy}>Review payment</button></form>}</section>}
          {tab==="Recovery"&&<section className="card narrow"><h2>Back up your wallet</h2><p>Your recovery phrase can spend your funds. Write it down and keep it private.</p>{recovery?<><div className="seed" role="region" aria-label="Recovery phrase">{recovery}</div><p className="hint">Automatically hides after 30 seconds or when this window loses focus.</p><button onClick={()=>setRecovery("")}>Hide phrase</button></>:<button disabled={busy} onClick={()=>run(async()=>{const v=await rpc<{key:string}>("seed");setRecovery(v.key);})}>Reveal recovery phrase</button>}</section>}
        </>}
      </>}
      {page==="Miner"&&<><section className="card"><div className="section-title"><div><h2>CPU mining</h2><p>Rewards go to your open wallet’s primary address.</p></div><span className="badge">{miningLive?.state??(status?.pool?"Pool process running":status?.solo?"Solo started":"Stopped")}</span></div><div className="tabs"><button disabled={busy||mining} className={miningMode==="solo"?"selected":""} onClick={()=>setMiningMode("solo")}>Solo</button><button disabled={busy||mining} className={miningMode==="pool"?"selected":""} onClick={()=>setMiningMode("pool")}>Pool mining</button></div>
        <p className="hint" role="note">Choose solo mining or connect to a ForgeCoin pool. The project-provided pool is planned to be the only initially advertised pool until independent operators adopt ForgeCoin. Its proposed operator fee is 1% of eligible pool rewards, and its initial capacity target is 100 simultaneous miner/worker connections. The pool is not yet operational or load-tested; 100 connections is a planned limit, not a guaranteed available slot. Solo mining remains available and does not pay a pool operator fee. Independent pools can be configured when available.</p>{miningMode==="solo"?<><h3>Mine with your local node</h3><p>Uses ForgeCoin’s built-in RandomX miner. Start and synchronize your local node first. Solo rewards depend on finding a block.</p><p role="status"><strong>{!status?.nodeConnected?"Node offline":status.nodeReady?"Ready for Solo mining":"Synchronizing / waiting for peers"}</strong>{status?.nodeConnected&&` - Height ${status.nodeHeight ?? 0}${status.nodeTarget ? ` / ${status.nodeTarget}` : ""}`}</p>{!status?.nodeConnected&&<button disabled={busy||status?.node} onClick={()=>act("start_node")}>Start local node</button>}</>:<><h3>Connect your own pool</h3><p>Uses your XMRig installation with RandomX (rx/0). Your pool must explicitly support ForgeCoin. This app does not operate a pool.</p><p>Pool <strong>{status?.settings.pool||"Not configured"}</strong></p><p className="hint">XMRig’s own donation policy applies. A running process does not confirm accepted shares.</p></>}
        {miningMode==="solo"&&<><p>Network difficulty <strong>{status?.nodeDifficulty?.toLocaleString()??"—"}</strong> · Target interval <strong>{status?.nodeTargetSeconds??120} seconds</strong></p><p className="hint">Network upgrade: minimum difficulty 500,000 from block 500; 1,000,000 from block 600. Faster difficulty adjustment begins at block 700. Existing blocks and balances are preserved.</p></>}<p>Saved thread count <strong>{status?.settings.threads??1}</strong></p>{threadControl}<div className="actions"><button className="primary" disabled={busy||!status?.wallet||mining||(miningMode==="solo"&&!status?.nodeReady)} onClick={()=>act(miningMode==="solo"?"start_solo":"start_pool")}>Start {miningMode} mining</button><button disabled={busy||!mining} onClick={()=>act("stop_mining")}>Stop mining</button><button onClick={()=>setPage("Settings")}>Configure</button></div>{!status?.wallet&&<p className="hint">Open a wallet to choose the reward address.</p>}
      </section><section className="card"><h2>{miningMode==="solo"?"Solo node activity":"Pool miner activity"}</h2><p className="hint">{miningMode==="solo"?"Recent node and mining messages, including blocks found.":"Connection errors and accepted shares reported by XMRig."}</p><label className="check"><input type="checkbox" checked={liveLog} onChange={e=>setLiveLog(e.target.checked)}/>Live log (updates every 2 seconds)</label><button disabled={busy} onClick={()=>run(async()=>{try{setMinerLog(await rpc<string>("miner_log",{mode:miningMode})||"No activity yet.");setLogError("");}catch(e){setLogError(String(e));}})}>Refresh log</button>{logError&&<p role="alert">{logError}</p>}<pre ref={logView} className="miner-log" aria-label="Mining activity log">{minerLog||"Waiting for activity…"}</pre></section><section className="card"><h2>Live mining operation</h2><p><strong>{miningLive?.state??"Checking miner…"}</strong></p><div className="big-number">{miningLive?.speed==null?"—":miningLive.speed.toLocaleString(undefined,{maximumFractionDigits:1})}<span>H/s</span></div>{miningLive?.threads!==undefined&&<p>Active CPU threads <strong>{miningLive.threads}</strong></p>}{miningLive?.accepted!==undefined&&<p>Accepted pool shares <strong>{miningLive.accepted}</strong></p>}<p className="hint">Updates every 2 seconds while this screen is open. {miningMode==="pool"?"Hashrate is XMRig’s recent average and may take a few seconds to appear.":"Reports the local node’s current mining operation."}</p>{miningLiveError&&<p role="alert">{miningLiveError}</p>}</section></>}
      {page==="Transactions"&&<section className="card"><h2>Transaction history</h2><p>Incoming, outgoing, pending and failed transfers for account 0. Unconfirmed incoming payments appear after confirmation.</p>{!status?.wallet?<p>Open a wallet to view its transactions.</p>:history.length===0?<div className="empty">No transactions in the scanned wallet yet.</div>:<div className="table-wrap"><table><thead><tr><th>Date</th><th>Status</th><th>Amount (FORGE)</th><th>Transaction ID</th></tr></thead><tbody>{history.map(t=><tr key={`${t.kind}-${t.txid}`}><td>{new Date(t.timestamp*1000).toLocaleString()}</td><td>{t.kind}</td><td className="mono">{coins(t.amount)}</td><td className="txid">{t.txid}</td></tr>)}</tbody></table></div>}</section>}
      {page==="Settings"&&<><section className="card narrow"><h2>Mining threads</h2>{threadControl}</section><section className="card narrow"><h2>Connection & mining</h2><p>Close the wallet, stop mining and stop the local node before saving connection changes.</p><form onSubmit={e=>{e.preventDefault();void run(async()=>{await rpc("settings",settings);await refresh();setNotice("Settings saved.");});}}><label>ForgeCoin node URL<input required value={settings.daemonUrl} onChange={e=>field("daemonUrl",e.target.value)}/></label><p className="hint">Use a node you trust. A remote node sees connection metadata; wallet keys remain local.</p><label>ForgeCoin P2P peer for the local node (host:port)<input value={settings.peer} onChange={e=>field("peer",e.target.value)} placeholder="150.136.209.227:39480"/></label><p className="hint">Prefilled with the ForgeCoin public peer. The local node syncs through this peer; your wallet connects locally.</p><label>XMRig executable path<input value={settings.xmrigPath} onChange={e=>field("xmrigPath",e.target.value)} placeholder="C:\Mining\xmrig.exe"/></label><label>Third-party ForgeCoin pool (host:port)<input value={settings.pool} onChange={e=>field("pool",e.target.value)} placeholder="Your pool’s host:port"/></label><label className="check"><input type="checkbox" checked={settings.tls} onChange={e=>field("tls",e.target.checked)}/>Use TLS for pool connection</label><button className="primary" disabled={busy||status?.wallet||status?.node||mining}>Save settings</button></form></section>
        <section className="card"><h2>Local node</h2><p>Syncs through the configured ForgeCoin public peer and serves wallet requests locally at 127.0.0.1:39481.</p><div className="actions"><button disabled={busy||status?.node} onClick={()=>act("start_node")}>Start node</button><button disabled={busy||!status?.node} onClick={()=>act("stop_node")}>Stop node</button><button disabled={busy} onClick={()=>run(async()=>setNodeInfo(await rpc("node_info")))}>Check connection</button></div>{nodeInfo&&<p>Height {nodeInfo.height.toLocaleString()} · Target {nodeInfo.target_height.toLocaleString()} · {nodeInfo.synchronized?"Synchronized":"Syncing / waiting for peers"}</p>}<h3>Wallet storage</h3><p className="path">{status?.walletDirectory}</p><p className="hint">Existing wallets outside this folder are not moved. To import, close their current wallet program and copy both the wallet file and its .keys file here, or use Recover. Keep your original backup.</p></section></>}
      <footer>ForgeCoin Desktop <span>Local keys. Your choice of node and pool.</span></footer>
    </main>
  </div>;
}




