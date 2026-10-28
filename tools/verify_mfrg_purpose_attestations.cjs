#!/usr/bin/env node
"use strict";
/**
 * Offline and read-only Solana Ed25519 wallet consent attestations for planned
 * mFRG treasury purposes. A valid signature proves control of a private key
 * corresponding to a *claimed* token owner public key at signing time, not
 * on-chain ownership, beneficial ownership, multisig approval or mainnet mint
 * identity. Does not sign, fetch, mint, transfer or alter any chain state.
 */
const fs = require("node:fs");
const crypto = require("node:crypto");

const BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const SPL_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
const DEVNET_TEST_MINT = "9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw";
const PREFIX = Buffer.from("302a300506032b6570032100", "hex");
const DOMAIN = "FORGECOIN_MFRG_TREASURY_PURPOSE_ATTESTATION_V1";
const MAX_CLAIMS = 100;
const FACTOR = 1000000n;
const MAX_AGE = 30 * 86400 * 1000;
const BUDGET = Object.freeze({
  fundraising: 50000000n,
  operations: 100000000n,
  ecosystem: 100000000n,
  staking: 85000000n,
  liquidity: 60000000n,
  engineering_security: 65000000n,
  founder_immediate: 15000000n,
  founder_deferred_team_label: 15000000n,
  emergency: 10000000n,
});

function reject(s) { throw new Error(s); }
function b58pub(s, label) {
  if (typeof s !== "string" || s.length < 32 || s.length > 44) reject(label + ": invalid Solana address length");
  let n = 0n;
  for (const c of s) {
    const idx = BASE58.indexOf(c);
    if (idx < 0) reject(label + ": invalid base58");
    n = n * 58n + BigInt(idx);
  }
  const bytes = [];
  while (n > 0n) { bytes.push(Number(n % 256n)); n /= 256n; }
  bytes.reverse();
  const leading = (s.match(/^1+/) || [""])[0].length;
  const buf = Buffer.concat([Buffer.alloc(leading), Buffer.from(bytes)]);
  if (buf.length !== 32) reject(label + ": not a 32-byte Solana public key");
  return buf;
}
function amount(s, label) {
  if (typeof s !== "string" || !/^(0|[1-9][0-9]*)$/.test(s) || s.length > 20) reject(label + ": exact atomic string required");
  const n = BigInt(s);
  if (n > ((1n << 64n) - 1n)) reject(label + ": uint64 overflow");
  return n;
}
function utc(s, label) {
  if (typeof s !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(s)) reject(label + ": require second-precision UTC Z time");
  const ms = Date.parse(s);
  if (!Number.isFinite(ms) || new Date(ms).toISOString() !== s.replace("Z", ".000Z")) reject(label + ": invalid UTC time");
  return ms;
}
function canonical(mint, claim) {
  return [
    DOMAIN, "mainnet-beta", mint, claim.purpose, claim.token_account,
    claim.token_owner, claim.amount_atomic, claim.nonce,
    claim.issued_utc, claim.expires_utc, ""
  ].join("\n");
}
function jsonFile(path) {
  return JSON.parse(fs.readFileSync(path, "utf8").replace(/^\uFEFF/, ""));
}
function inventoryByAddress(mint, response) {
  if (!response || response.id !== mint + ":inventory"
      || !response.result || !Array.isArray(response.result.value)
      || !Number.isSafeInteger(response.result.context?.slot)
      || response.result.context.slot <= 0) reject("Invalid withContext inventory RPC data");
  const accounts = new Map();
  for (const item of response.result.value) {
    const addr = item?.pubkey;
    b58pub(addr, "inventory token account");
    if (accounts.has(addr)) reject("Duplicate token account in inventory");
    const acct = item.account;
    if (acct?.owner !== SPL_PROGRAM || acct?.executable !== false
        || acct?.data?.program !== "spl-token"
        || acct?.data?.parsed?.type !== "account") reject("Non-standard SPL token-account entry");
    const info = acct.data.parsed.info;
    if (info?.mint !== mint || !info.owner
        || info.tokenAmount?.decimals !== 6
        || !["initialized","frozen"].includes(info.state)) reject("Invalid token-account mint, decimals or state");
    b58pub(info.owner, "token account authority");
    const raw = amount(info.tokenAmount.amount, "token account raw amount");
    accounts.set(addr, {owner:info.owner, raw, delegate:info.delegate || null,
      state:info.state, closeAuthority:info.closeAuthority || null});
  }
  return {slot:response.result.context.slot, accounts};
}
function assess(manifest, inventory, asOf) {
  if (manifest?.schema !== "mfrg-purpose-attestations-v1"
      || manifest?.network !== "mainnet-beta"
      || typeof manifest.mint !== "string"
      || manifest.mint === DEVNET_TEST_MINT) reject("Invalid or historic devnet mint identity");
  b58pub(manifest.mint, "mint");
  if (!Array.isArray(manifest.claims) || !manifest.claims.length
      || manifest.claims.length > MAX_CLAIMS) reject("Require 1..100 claims");
  const {slot,accounts} = inventoryByAddress(manifest.mint, inventory);
  const now = utc(asOf, "as-of");
  const seen = new Set(), nonces = new Set(), totals = Object.fromEntries(Object.keys(BUDGET).map(k=>[k,0n]));
  const claimedAddresses = [];
  for (const claim of manifest.claims) {
    if (!claim || !Object.prototype.hasOwnProperty.call(BUDGET, claim.purpose))
      reject("Unknown allocation purpose");
    b58pub(claim.token_account, "claimed token account");
    const rawSigner = b58pub(claim.token_owner, "claimed token owner");
    const observed = accounts.get(claim.token_account);
    if (!observed) reject("Claimed account absent from untrusted snapshot");
    if (seen.has(claim.token_account)) reject("Double-counted token account");
    seen.add(claim.token_account);
    const balance = amount(claim.amount_atomic, "claimed balance");
    if (balance === 0n || balance !== observed.raw) reject("Claimed amount differs from snapshot balance");
    if (claim.token_owner !== observed.owner) reject("Signed wallet is not parsed account owner authority");
    if (observed.delegate || observed.closeAuthority || observed.state !== "initialized")
      reject("Delegate, close authority or frozen state requires separate custody review");
    if (typeof claim.nonce !== "string" || !/^[a-f0-9]{32,64}$/.test(claim.nonce)) reject("Require a unique random 16..32 byte hex nonce");
    if (nonces.has(claim.nonce)) reject("Duplicate signed nonce");
    nonces.add(claim.nonce);
    const issued = utc(claim.issued_utc, "issued_utc"), expiry=utc(claim.expires_utc,"expires_utc");
    if (issued > now || expiry < now || expiry <= issued || expiry-issued > MAX_AGE)
      reject("Future, expired or overly broad consent attestation");
    if (typeof claim.signature_base64 !== "string"
        || !/^[A-Za-z0-9+/]{86}==$/.test(claim.signature_base64))
      reject("Expected exactly 64 bytes of standard base64 Ed25519 signature");
    const sig = Buffer.from(claim.signature_base64, "base64");
    if (sig.length !== 64 || sig.toString("base64") !== claim.signature_base64)
      reject("Noncanonical Ed25519 signature encoding");
    const spki = crypto.createPublicKey({key:Buffer.concat([PREFIX,rawSigner]),format:"der",type:"spki"});
    if (!crypto.verify(null,Buffer.from(canonical(manifest.mint,claim),"utf8"),spki,sig))
      reject("Invalid signed consent for exact mint, role, account and amount");
    totals[claim.purpose] += balance;
    if (totals[claim.purpose] > BUDGET[claim.purpose]*FACTOR) reject("Signed claims exceed budget for purpose: " + claim.purpose);
    claimedAddresses.push({purpose:claim.purpose, token_account:claim.token_account,
      claimed_amount_atomic:balance.toString(), token_owner:claim.token_owner});
  }
  return {
    offline_wallet_signature_checks_passed:true,
    claim_count:claimedAddresses.length, untrusted_inventory_slot:slot,
    signed_claims:claimedAddresses, total_claimed_atomic:claimedAddresses.reduce((n,x)=>n+BigInt(x.claimed_amount_atomic),0n).toString(),
    purposes_claimed:Object.fromEntries(Object.entries(totals).map(([key,value])=>[key,value.toString()])),
    budget_cap_policy_mfrg:Object.fromEntries(Object.entries(BUDGET).map(([key,value])=>[key,value.toString()])),
    mint:manifest.mint,
    network_or_rpc_provenance_authenticated:false,
    mint_creation_authenticated:false,
    inventory_completeness_verified:false,
    owner_signature_proves_beneficial_ownership:false,
    program_or_multisig_authority_proven:false,
    founders_verified:false, treasury_funded_verified:false,
    sale_or_issuance_authorized:false,
    note:"Ed25519 consent only proves a private-key signature for a claimed account-owner pubkey. It does not authenticate RPC data or beneficial control; program/PDA/multisig policies require independent approvals."
  };
}
function main(argv) {
  try {
    const flags = {};
    for (let i=0;i<argv.length;i+=2) {
      if (!["--manifest","--inventory-json","--as-of-utc"].includes(argv[i]) || !argv[i+1]) reject("Require --manifest, --inventory-json, --as-of-utc");
      flags[argv[i]] = argv[i+1];
    }
    if (Object.keys(flags).length !== 3) reject("Missing manifest, inventory or as-of UTC");
    const result=assess(jsonFile(flags["--manifest"]),jsonFile(flags["--inventory-json"]),flags["--as-of-utc"]);
    process.stdout.write(JSON.stringify(result,null,2)+"\n");
    return 0;
  } catch (err) {
    process.stderr.write(JSON.stringify({offline_wallet_signature_checks_passed:false,
      sale_or_issuance_authorized:false,error:err.message},null,2)+"\n");
    return 2;
  }
}
if (require.main === module) process.exitCode=main(process.argv.slice(2));
module.exports={b58pub,canonical,assess,main,BUDGET,DOMAIN};
