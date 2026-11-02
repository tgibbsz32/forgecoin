'use strict';
/* Public leaderboard displays opt-in, fresh and verified numeric hashrates only.
   Mining software strings are client-reported, not a security attestation. */
(async()=>{
 const body=document.getElementById('leaderboard-rows'),status=document.getElementById('leaderboard-status');
 if(!body)return;
 const api=document.querySelector('meta[name="forgecoin-leaderboard-api"]')?.content?.trim();
 if(!api)return;
 let url;try{url=new URL(api,location.href);if(url.origin!==location.origin||url.protocol!=='https:')return;}catch{return;}
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),7000);
 try{
  const response=await fetch(url,{credentials:'omit',cache:'no-store',signal:controller.signal,headers:{Accept:'application/json'}});
  if(!response.ok)throw Error('unavailable');
  const j=await response.json(),now=Math.floor(Date.now()/1000);
  if(j.schema!=='frg-miner-leaderboard-v1'||j.network!=='frg-mainnet-20261026'||j.source!=='verified-native-pool'||j.ready!==true||!Number.isInteger(j.observedAt)||Math.abs(now-j.observedAt)>120||!Array.isArray(j.miners))throw Error('unverified');
  const good=j.miners.filter(m=>m&&m.optIn===true&&(m.mode==='solo'||m.mode==='pool')&&Number.isFinite(m.hashrateHs)&&m.hashrateHs>=0&&Number.isSafeInteger(m.workers)&&m.workers>=0&&typeof m.name==='string'&&m.name.trim().length>0&&m.name.length<=60).sort((a,b)=>b.hashrateHs-a.hashrateHs).slice(0,50);
  body.replaceChildren();
  if(!good.length)throw Error('no opt-in records');
  for(const [i,m] of good.entries()){
   const row=document.createElement('tr');
   const fmt=h=>h>=1e9?(h/1e9).toFixed(2)+' GH/s':h>=1e6?(h/1e6).toFixed(2)+' MH/s':h>=1e3?(h/1e3).toFixed(2)+' kH/s':h.toFixed(1)+' H/s';
   for(const val of [String(i+1),m.name,fmt(m.hashrateHs),String(m.workers),m.mode==='solo'?'Solo':'Pool',typeof m.software==='string'&&m.software.length<=80?m.software:'Not reported']){
    const cell=document.createElement('td');cell.textContent=val;row.append(cell);
   }
   body.append(row);
  }
  if(status)status.textContent='Verified, opt-in FRG leaderboard observed at '+new Date(j.observedAt*1000).toLocaleString()+'. Software names are miner-reported.';
 }catch{body.replaceChildren();const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=6;td.textContent='No verified opt-in leaderboard data available.';tr.append(td);body.append(tr);if(status)status.textContent='Leaderboard unavailable until a verified native FRG feed is connected.';}
 finally{clearTimeout(timeout);}
})();
