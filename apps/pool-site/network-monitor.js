"use strict";
/* Supplements the established 57-field pool dashboard with verified network
   telemetry. Does not infer pool balances, mining readiness or payout state. */
(() => {
  const expectedGenesis = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c";
  const parent=document.querySelector("#overview") || document.querySelector("#statistics");
  if(!parent)return;
  const status=document.createElement("p");
  status.id="frg-node-monitor-status";
  status.setAttribute("role","status");
  status.textContent="Read-only Oracle network monitor: checking verified genesis…";
  parent.insertBefore(status,parent.firstChild);
  const slots={
    networkHeight:"height",
    networkTip:"topHash",
    networkDifficulty:"difficulty",
    networkPeers:"peers",
    networkMempool:"txPoolSize",
    networkHashrate:"networkHashrateEstimate"
  };
  const targets=Object.fromEntries(Object.keys(slots).map(k=>[k,document.querySelector('[data-poolmetric="'+k+'"]')]));
  const reset=()=>{Object.values(targets).forEach(el=>{if(el)el.textContent="Unavailable";});};
  async function refresh(){
    const controller=new AbortController();
    const clock=setTimeout(()=>controller.abort(),5000);
    try{
      const response=await fetch("api/monitor",{credentials:"omit",cache:"no-store",signal:controller.signal});
      if(!response.ok)throw Error("unavailable");
      const d=await response.json(),n=d.network;
      if(!n||n.mainnetGenesis!==expectedGenesis||d.status!=="genesis-verified-prelaunch"||
        d.launchApproved!==false||d.miningAuthorized!==false||d.payoutsEnabled!==false||
        !Number.isSafeInteger(d.checkedAt)||Math.abs(Date.now()/1000-d.checkedAt)>120)throw Error("unverified");
      for(const [name,key] of Object.entries(slots)){
        const el=targets[name],value=n[key];
        if(!el)continue;
        if(name==="networkTip" && typeof value==="string"&&/^[0-9a-fA-F]{64}$/.test(value)) el.textContent=value;
        else if(typeof value==="number"&&Number.isFinite(value)&&value>=0)
          el.textContent=value.toLocaleString("en-US")+(name==="networkHashrate"?" H/s (difficulty estimate)":"");
        else el.textContent="Unavailable";
      }
      status.textContent="Verified 20261026 genesis on Oracle · read-only, "+new Date(d.checkedAt*1000).toLocaleString()+
        " · NOT launched for public mining or payouts.";
    }catch(err){reset();status.textContent="Oracle network monitor unavailable. No live miner, pool or payout metrics are being reported.";}
    finally{clearTimeout(clock);}
  }
  refresh();
  setInterval(refresh,30000);
})();
