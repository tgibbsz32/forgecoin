#!/usr/bin/env node
"use strict";
const assert = require("node:assert/strict");
const test = require("node:test");
const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const {canonical,assess,main,BUDGET}=require("./verify_mfrg_purpose_attestations.cjs");
const PREFIX="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const SPL_PROGRAM="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
const ISSUED="2026-10-01T00:00:00Z", EXPIRES="2026-10-30T00:00:00Z", NOW="2026-10-28T00:00:00Z";
function base58(buffer) {
  let n=BigInt("0x"+buffer.toString("hex"));
  let s="";
  while(n){s=PREFIX[Number(n%58n)]+s;n/=58n;}
  for(const b of buffer){if(b===0)s="1"+s;else break;}
  return s;
}
function key(){const {publicKey,privateKey}=crypto.generateKeyPairSync("ed25519");
  return {address:base58(publicKey.export({format:"der",type:"spki"}).subarray(-32)),privateKey};
}
function fixture() {
  const mint=key(),owner=key(),account=key();
  const claim={
    purpose:"operations",token_account:account.address,token_owner:owner.address,
    amount_atomic:"1000000",nonce:"a".repeat(32),issued_utc:ISSUED,
    expires_utc:EXPIRES
  };
  const manifest={schema:"mfrg-purpose-attestations-v1",network:"mainnet-beta",
    mint:mint.address,claims:[claim]};
  function resign(){claim.signature_base64=crypto.sign(null,Buffer.from(canonical(mint.address,claim)),owner.privateKey).toString("base64");}
  resign();
  const snapshot={id:mint.address+":inventory",result:{context:{slot:1000},
    value:[{pubkey:account.address,account:{owner:SPL_PROGRAM,executable:false,
      data:{program:"spl-token",parsed:{type:"account",info:{
        mint:mint.address,owner:owner.address,tokenAmount:{decimals:6,amount:"1000000"},
        state:"initialized",isNative:false
      }}}}}]}};
  return {mint,owner,account,claim,manifest,snapshot,resign};
}
test("01 valid signed purpose consent remains explicitly non-production",()=>{
  const f=fixture(),x=assess(f.manifest,f.snapshot,NOW);
  assert.equal(x.offline_wallet_signature_checks_passed,true);
  assert.equal(x.claim_count,1);assert.equal(x.total_claimed_atomic,"1000000");
  for(const k of ["network_or_rpc_provenance_authenticated","mint_creation_authenticated",
   "inventory_completeness_verified","owner_signature_proves_beneficial_ownership",
   "program_or_multisig_authority_proven","founders_verified","treasury_funded_verified",
   "sale_or_issuance_authorized"])assert.equal(x[k],false,k);
});
test("02 forged signature rejected",()=>{const f=fixture();f.claim.signature_base64=crypto.randomBytes(64).toString("base64");
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/Invalid signed consent/);});
test("03 altering mint with same owner signature fails",()=>{const f=fixture();f.manifest.mint=key().address;f.snapshot.id=f.manifest.mint+":inventory";
  f.snapshot.result.value[0].account.data.parsed.info.mint=f.manifest.mint;
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/Invalid signed consent/);});
test("04 tampering purpose invalidates signature",()=>{const f=fixture();f.claim.purpose="liquidity";
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/Invalid signed consent/);});
test("05 tampering amount invalidates claim",()=>{const f=fixture();f.claim.amount_atomic="2000000";
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/differs from snapshot/);});
test("06 wrong wallet signer versus account owner denied",()=>{const f=fixture();f.claim.token_owner=key().address;
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/not parsed account owner/);});
test("07 unknown category rejected",()=>{const f=fixture();f.claim.purpose="founder_bonus";
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/Unknown allocation/);});
test("08 account missing from RPC evidence rejected",()=>{const f=fixture();f.snapshot.result.value=[];
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/absent/);});
test("09 duplicate token accounts rejected",()=>{const f=fixture();f.snapshot.result.value.push(structuredClone(f.snapshot.result.value[0]));
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/Duplicate token account/);});
test("10 duplicate allocation claim of one account rejected",()=>{const f=fixture();f.manifest.claims.push({...f.claim});
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/Double-counted/);});
test("11 delegate requires separate custody review",()=>{const f=fixture();f.snapshot.result.value[0].account.data.parsed.info.delegate=key().address;
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/requires separate custody review/);});
test("12 frozen account requires separate review",()=>{const f=fixture();f.snapshot.result.value[0].account.data.parsed.info.state="frozen";
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/requires separate custody review/);});
test("13 close authority requires separate review",()=>{const f=fixture();f.snapshot.result.value[0].account.data.parsed.info.closeAuthority=key().address;
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/requires separate custody review/);});
test("14 fundraising over 50M lifetime budget is rejected, even with valid signature",()=>{
  const f=fixture();f.claim.purpose="fundraising";
  f.claim.amount_atomic=(50000001n*1000000n).toString();
  f.snapshot.result.value[0].account.data.parsed.info.tokenAmount.amount=f.claim.amount_atomic;
  f.resign();
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/exceed/);
});
test("15 founder immediate over 15M rejected",()=>{const f=fixture();f.claim.purpose="founder_immediate";
  f.claim.amount_atomic=(15000001n*1000000n).toString();
  f.snapshot.result.value[0].account.data.parsed.info.tokenAmount.amount=f.claim.amount_atomic;
  f.resign();assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/exceed/);});
test("16 expiry and future-signed consent cannot pass",()=>{const f=fixture();
  assert.throws(()=>assess(f.manifest,f.snapshot,"2026-10-31T00:00:00Z"),/expired/);
  assert.throws(()=>assess(f.manifest,f.snapshot,"2026-09-30T00:00:00Z"),/Future/);});
test("17 invalid nonce rejected",()=>{const f=fixture();f.claim.nonce="not-random";
  f.resign();assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/nonce/);});
test("18 invalid or devnet mint rejected",()=>{const f=fixture();f.manifest.mint="9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw";
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/devnet/);});
test("19 wrong SPL program rejected",()=>{const f=fixture();f.snapshot.result.value[0].account.owner=key().address;
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/Non-standard SPL/);});
test("20 bad decimals rejected",()=>{const f=fixture();f.snapshot.result.value[0].account.data.parsed.info.tokenAmount.decimals=9;
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/Invalid token-account/);});
test("21 malformed Ed25519 encoding rejected",()=>{const f=fixture();f.claim.signature_base64="bad";
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/signature/);});
test("22 altered expiry and beneficiary scope invalidate signature",()=>{const f=fixture();f.claim.expires_utc="2026-10-29T00:00:00Z";
  assert.throws(()=>assess(f.manifest,f.snapshot,NOW),/Invalid signed consent/);});
test("23 purpose budgets cover 500M, founder 30M, fundraising 50M",()=>{
  const sum=Object.values(BUDGET).reduce((a,b)=>a+b,0n);
  assert.equal(sum,500000000n);
  assert.equal(BUDGET.founder_immediate+BUDGET.founder_deferred_team_label,30000000n);
  assert.equal(BUDGET.fundraising,50000000n);
});
test("24 cli reads only saved JSON and exits closed on tampered signature",()=>{
  const f=fixture(),d=fs.mkdtempSync(path.join(os.tmpdir(),"mfrg-attest-fake-"));
  try {
    const mf=path.join(d,"manifest.json"),inv=path.join(d,"inventory.json");
    fs.writeFileSync(mf,JSON.stringify(f.manifest));fs.writeFileSync(inv,JSON.stringify(f.snapshot));
    assert.equal(main(["--manifest",mf,"--inventory-json",inv,"--as-of-utc",NOW]),0);
    f.claim.signature_base64="tampered";
    fs.writeFileSync(mf,JSON.stringify(f.manifest));
    assert.equal(main(["--manifest",mf,"--inventory-json",inv,"--as-of-utc",NOW]),2);
  } finally {fs.rmSync(d,{recursive:true,force:true});}
});
