"use strict";
(() => {
  const GENESIS = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c";
  const output = [...document.querySelectorAll("[data-metric]")];
  const status = document.getElementById("stats-status");
  const defaults = new Map(output.map(el => [el.dataset.metric,"Unavailable"]));
  const format = v => typeof v === "number" && Number.isFinite(v) && v >= 0
    ? v.toLocaleString("en-US",{maximumFractionDigits:4}) : "Unavailable";
  function reset() {
    for (const el of output) el.textContent = defaults.get(el.dataset.metric);
  }
  function set(key,value,suffix="") {
    const element=output.find(el=>el.dataset.metric===key);
    if (element && Number.isFinite(value)) element.textContent=format(value)+suffix;
  }
  async function refresh() {
    reset();
    status.textContent = "Checking the authenticated local monitor for verified 20261026 genesis data…";
    const abort = new AbortController();
    const deadline = setTimeout(()=>abort.abort(),5000);
    try {
      const reply=await fetch("api/monitor",{credentials:"omit",cache:"no-store",signal:abort.signal});
      if (!reply.ok) throw Error("monitor or daemon offline");
      const data=await reply.json();
      const n=data.network;
      if (!n || n.mainnetGenesis!==GENESIS || !Number.isSafeInteger(n.height) || n.height < 1 ||
          !Number.isSafeInteger(data.checkedAt) || Math.abs(Date.now()/1000-data.checkedAt)>120 ||
          data.status!=="genesis-verified-prelaunch" || data.launchApproved!==false ||
          data.payoutsEnabled!==false || data.miningAuthorized!==false) {
        throw Error("identity or freshness not verified");
      }
      set("networkHeight",n.height);
      set("networkDifficulty",n.difficulty);
      set("networkHashrate",n.networkHashrateEstimate," H/s (difficulty-derived)");
      set("networkPeers",n.peers);
      set("mempoolTransactions",n.txPoolSize);
      set("targetBlockSeconds",120," seconds (target)");
      if (data.pool && typeof data.pool==="object") {
        set("poolHashrate",data.pool.poolHashrate," H/s");
        set("networkHashrate",data.pool.networkHashrate," H/s (pool reported)");
        set("networkDifficulty",data.pool.networkDifficulty);
        set("networkHeight",data.pool.networkHeight);
        set("connectedSockets",data.pool.connectedMiners);
        set("poolBlocksFound",data.pool.poolBlocksFound);
        set("roundShares",data.pool.roundHashes);
      }
      status.textContent="Verified read-only node telemetry ("+new Date(data.checkedAt*1000).toISOString()+
        "). Public mining and payouts are NOT authorized. Unavailable fields have no trusted source.";
    } catch(e) {
      reset();
      status.textContent="No verified current FRG node/pool telemetry. Genesis-frozen network is not launched; mining and payouts remain disabled.";
    } finally {
      clearTimeout(deadline);
    }
  }
  refresh();
  setInterval(refresh,30000);
})();
