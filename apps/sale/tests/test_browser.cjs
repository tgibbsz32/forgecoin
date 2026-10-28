'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..', '..', '..');
const js = fs.readFileSync(path.join(root,'docs','sale.js'),'utf8');
const paused = JSON.parse(fs.readFileSync(path.join(root,'docs','sale-status.json'),'utf8'));

function mockBrowser(status, hasWallet) {
  const elements = new Map();
  const ids = [
    'token-amount','quote-button','connect-wallet','wallet-state',
    'checkout-state','estimate-display','price-display','token-price',
    'sale-status','mint-address'
  ];
  for (const id of ids) {
    elements.set(id,{id,disabled:false,textContent:'',handlers:{},
      addEventListener(event,fn){this.handlers[event]=fn;}});
  }
  let connected=0, signed=0, fetched=0, fetchUrl='', paymentMethods=0;
  const provider = {
    publicKey:'11111111111111111111111111111111',
    async connect(){connected++;return {publicKey:this.publicKey};},
    async signTransaction(){signed++;throw Error('MUST NEVER SIGN');},
    async sendTransaction(){paymentMethods++;throw Error('MUST NEVER PAY');},
  };
  const docEvents={};
  const context = {
    window:hasWallet?{phantom:{solana:provider}}:{},
    document:{
      getElementById:id=>elements.get(id),
      addEventListener:(event,handler)=>{docEvents[event]=handler;}
    },
    fetch:async(url)=>{fetched++;fetchUrl=url;return {ok:true,async json(){return status;}};},
    console
  };
  vm.runInNewContext(js,context,{timeout:1000,filename:'sale.js'});
  return {
    e: id=>elements.get(id),events:docEvents,
    stats:()=>({connected,signed,fetched,fetchUrl,paymentMethods})
  };
}
async function tick(){await new Promise(resolve=>setImmediate(resolve));}
(async()=>{
  let tests=0;
  let browser=mockBrowser(paused,true);
  await tick();await tick();
  assert.equal(browser.e('token-amount').disabled,true);
  assert.equal(browser.e('quote-button').disabled,true);
  assert.equal(browser.e('sale-status').textContent,'Not open');
  assert.equal(browser.stats().connected,0);
  assert.equal(browser.stats().signed,0);
  assert.equal(browser.stats().fetchUrl,'sale-status.json');
  console.log('PASS initial UI paused and no wallet auto connection');tests++;

  await browser.e('connect-wallet').handlers.click();
  assert.equal(browser.stats().connected,1);
  assert.equal(browser.stats().signed,0);
  assert.equal(browser.stats().paymentMethods,0);
  assert.match(browser.e('wallet-state').textContent,/No purchase is available; no transaction was signed/i);
  assert.equal(browser.e('quote-button').disabled,true);
  console.log('PASS public-address-only wallet preview does not sign or pay');tests++;

  let submitPrevented=0;
  browser.events.submit({
    target:{closest:selector=>selector==='.checkout-form'?true:null},
    preventDefault(){submitPrevented++;}
  });
  assert.equal(submitPrevented,1);
  console.log('PASS checkout form submission is intercepted');tests++;

  browser=mockBrowser({...paused,sale_enabled:true,payments_enabled:true},true);
  await tick();await tick();
  assert.equal(browser.e('quote-button').disabled,true);
  assert.equal(browser.e('token-amount').disabled,true);
  assert.match(browser.e('wallet-state').textContent,/could not be verified/i);
  console.log('PASS tampered sale status cannot unlock checkout');tests++;

  browser=mockBrowser({...paused,token_mainnet_mint:'fake-mint',sale_price_usdc:'0.1'},true);
  await tick();await tick();
  assert.equal(browser.e('quote-button').disabled,true);
  assert.equal(browser.e('mint-address').textContent,'Not issued');
  console.log('PASS unreviewed mint and price cannot unlock checkout');tests++;

  browser=mockBrowser(paused,false);
  await tick();
  await browser.e('connect-wallet').handlers.click();
  assert.match(browser.e('wallet-state').textContent,/No supported injected Solana wallet/i);
  assert.equal(browser.e('quote-button').disabled,true);
  console.log('PASS no-wallet fallback remains safe');tests++;

  console.log('PASS static sale browser behavior assertions='+tests);
})().catch(error=>{console.error('FAIL',error);process.exitCode=2;});