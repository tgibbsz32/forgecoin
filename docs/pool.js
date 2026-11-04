'use strict';
// Read-only public FRG address lookup. The public GitHub Pages site does not
// configure a pool API: it must NOT transmit entered addresses to an
// unverified or third-party endpoint. Operators may enable only a same-origin
// HTTPS proxy after independent backend assessment.
document.querySelector('#worker-lookup')?.addEventListener('submit',async event=>{
  event.preventDefault();
  const result=document.querySelector('#worker-result');
  const field=document.querySelector('#worker-key');
  if(!result||!field)return;
  const address=field.value.trim();
  if(!/^[1-9A-HJ-NP-Za-km-z]{90,140}$/.test(address)){
    result.textContent='Invalid public FRG address format. Never enter a recovery phrase or private key.';
    return;
  }
  const configured=document.querySelector('meta[name="forgecoin-pool-api"]')?.content?.trim();
  if(!configured){
    result.textContent='Native FRG miner lookup is not connected to a verified read-only backend. Your address was not submitted.';
    return;
  }
  let url;
  try{
    url=new URL(configured,location.href);
    if(url.origin!==location.origin||url.protocol!=='https:'||url.pathname!=='/api/miner-stats'
       ||url.search||url.hash||url.username||url.password)throw Error('untrusted pool API');
    url.searchParams.set('address',address);
  }catch{
    result.textContent='The pool statistics endpoint is not configured safely. Your address was not submitted.';
    return;
  }
  const controller=new AbortController(),deadline=setTimeout(()=>controller.abort(),7000);
  result.textContent='Checking available public worker statistics...';
  try{
    const response=await fetch(url,{method:'GET',credentials:'omit',redirect:'error',
      referrerPolicy:'no-referrer',cache:'no-store',signal:controller.signal,
      headers:{Accept:'application/json'}});
    if(!response.ok)throw Error('not available');
    const json=await response.json(),stats=json.stats,seen=Date.parse(json.asOf);
    if(json.state!=='backend_observed_unverified'||json.launchApproved!==false
       ||!stats||!Number.isSafeInteger(stats.hashrate)||stats.hashrate<0
       ||!Number.isSafeInteger(stats.workers)||stats.workers<0
       ||!Number.isFinite(seen)||Math.abs(Date.now()-seen)>120000)throw Error('invalid/stale');
    result.textContent='Local backend observation only (not independently verified): '
      +stats.hashrate.toLocaleString('en-US')+' H/s; '
      +stats.workers.toLocaleString('en-US')+' workers. '
      +'Balances, share history and payouts are not available.';
  }catch{
    result.textContent='Native FRG worker statistics are unavailable or stale. No live mining or payout information is being shown.';
  }finally{clearTimeout(deadline);}
});