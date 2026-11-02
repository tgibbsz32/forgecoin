'use strict';
/* Public anonymous view counters. Results are provider estimates, not verified humans. */
(async () => {
 const v=document.getElementById('homepage-pageviews'),u=document.getElementById('homepage-unique'),n=document.getElementById('homepage-traffic-note');
 if(!v||!u)return;
 const endpoint='https://counterapi.com/api/tgibbsz32.github.io/view/forgecoin-homepage';
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000);
 const value=async(url)=>{const r=await fetch(url,{cache:'no-store',credentials:'omit',signal:controller.signal});if(!r.ok)throw Error('unavailable');const j=await r.json();if(!j||!Number.isSafeInteger(j.value)||j.value<0)throw Error('invalid');return j.value.toLocaleString('en-US');};
 try{v.textContent=await value(endpoint);u.textContent=await value(endpoint+'?readOnly=true&unique=true');if(n)n.textContent='Counts begin with this integration. Unique visitors are approximate anonymous provider hashes, not identified people.';}
 catch{if(n)n.textContent='Visitor count service unavailable; no totals have been estimated.';}
 finally{clearTimeout(timer);}
})();
