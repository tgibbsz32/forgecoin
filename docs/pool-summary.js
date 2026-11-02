'use strict';
/* Shared fail-closed summary. No fabricated network/solo miner readings.
   A trusted same-origin HTTPS API may be declared in the page's meta tag. */
(async()=> {
 const slots=[...document.querySelectorAll('.pool-summary [data-poolmetric]')];
 const pool=document.getElementById('pool-miners-workers'),solo=document.getElementById('solo-miners-workers');
 const api=document.querySelector('meta[name="forgecoin-pool-api"]')?.content?.trim();
 if(!slots.length&&!pool&&!solo)return;
 if(!api)return;
 let url;try{url=new URL(api,location.href);if(url.origin!==location.origin||url.protocol!=='https:')return;}catch{return;}
 const render=async()=>{
  const controller=new AbortController(),t=setTimeout(()=>controller.abort(),7000);
  try{
   const response=await fetch(url,{credentials:'omit',cache:'no-store',signal:controller.signal,headers:{Accept:'application/json'}});
   if(!response.ok)throw Error('unavailable');
   const j=await response.json(),now=Math.floor(Date.now()/1000);
   if(j.schema!=='frg-pool-stats-v1'||j.source!=='verified-native-pool'||j.network!=='frg-mainnet-20261026'||j.ready!==true||!Number.isInteger(j.observedAt)||Math.abs(now-j.observedAt)>120||!j.metrics||typeof j.metrics!=='object')throw Error('not verified');
   for(const el of slots){const v=j.metrics[el.dataset.poolmetric];el.textContent=typeof v==='string'&&v.trim()&&v.length<=90?v:'Unavailable';}
   const pair=(m,w)=>Number.isSafeInteger(m)&&m>=0&&Number.isSafeInteger(w)&&w>=0?m.toLocaleString()+' / '+w.toLocaleString():'Unavailable';
   if(pool)pool.textContent=pair(j.metrics.poolMinersCount,j.metrics.poolWorkersCount);
   if(solo)solo.textContent=pair(j.metrics.soloMinersCount,j.metrics.soloWorkersCount);
  }catch{
   for(const el of slots)el.textContent='Unavailable';
   if(pool)pool.textContent='Unavailable';if(solo)solo.textContent='Unavailable';
  }finally{clearTimeout(t);}
 };
 await render();setInterval(render,30000);
})();
