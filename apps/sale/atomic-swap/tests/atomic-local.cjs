'use strict';
// Integration acceptance ONLY against an isolated local validator.
// No real buyer wallet, merchant account, USDC, FRG network or devnet/mainnet.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const anchor = require('@coral-xyz/anchor');
const {
  Connection, Keypair, PublicKey, SystemProgram, LAMPORTS_PER_SOL
} = require('@solana/web3.js');
const {
  TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID,
  createMint, getOrCreateAssociatedTokenAccount,
  getAssociatedTokenAddressSync, getAccount, mintTo, transfer,
  freezeAccount, thawAccount
} = require('@solana/spl-token');

const RPC_URL = 'http://127.0.0.1:18899';
const one = 1_000_000n;
const MAX = 5_000_000n * one;
const programId = new PublicKey('5NrwtM49RAn5iQicbod539qxhqYRkV3ZpiBudoUCUGNY');
const idlFile = path.join(__dirname,'..','idl','miniforge_swap.json');
let checks=0;
function pass(name){ checks++; console.log('PASS '+String(checks).padStart(2,'0')+' '+name); }
async function rejected(name, call){
  try{await call();}
  catch(error) {
    assert.ok(error && (error.message||error.logs),name+': exception was empty');
    pass(name+' (on-chain rejected)');
    return;
  }
  throw new Error(name+': operation unexpectedly succeeded');
}
async function getBalance(conn,address){
  return (await getAccount(conn,address)).amount;
}
async function airdrop(conn,key,sol=4){
  const tx=await conn.requestAirdrop(key.publicKey,sol*LAMPORTS_PER_SOL);
  await conn.confirmTransaction(tx,'confirmed');
}
async function send(program,method,args,accounts,signers=[]){
  return await program.methods[method](...args).accountsStrict(accounts)
    .signers(signers).rpc({skipPreflight:false,commitment:'confirmed'});
}
async function main() {
  if(!fs.existsSync(idlFile)) throw new Error('Must compile and generate Anchor IDL before local integration');
  const idl=JSON.parse(fs.readFileSync(idlFile,'utf8'));
  const declared=idl.address || idl.metadata?.address;
  assert.equal(declared,programId.toBase58(),'IDL program ID must match pinned local test program');
  const conn=new Connection(RPC_URL,'confirmed');
  const version=await conn.getVersion();
  assert.ok(version['solana-core'],'Local Solana validator required');
  // Strictly refuse remote clusters and any surprise mainnet client.
  assert.equal(conn.rpcEndpoint,RPC_URL);
  const programInfo=await conn.getAccountInfo(programId);
  assert.ok(programInfo?.executable,'Pinned local program not deployed at loopback test address');
  pass('loopback validator and pinned executable test program');

  const admin=Keypair.generate();
  const buyer=Keypair.generate();
  const merchant=Keypair.generate();
  const attacker=Keypair.generate();
  await airdrop(conn,admin,10);
  await airdrop(conn,buyer,5);
  await airdrop(conn,attacker,2);
  pass('disposable local-only administrator, buyer and attacker funded with faucet SOL');

  const provider=new anchor.AnchorProvider(conn,new anchor.Wallet(admin),{
    commitment:'confirmed', preflightCommitment:'confirmed'
  });
  const program=new anchor.Program(idl,provider);
  assert.equal(program.programId.toBase58(),programId.toBase58());

  // Neither mint exists on Solana mainnet, and neither token is real USDC.
  const mfrg=await createMint(conn,admin,admin.publicKey,admin.publicKey,6);
  const fakeUsdc=await createMint(conn,admin,admin.publicKey,null,6);
  const sellerMfrg=(await getOrCreateAssociatedTokenAccount(conn,admin,mfrg,admin.publicKey)).address;
  const treasuryUsdc=(await getOrCreateAssociatedTokenAccount(conn,admin,fakeUsdc,merchant.publicKey)).address;
  const buyerUsdc=(await getOrCreateAssociatedTokenAccount(conn,admin,fakeUsdc,buyer.publicKey)).address;
  const buyerMfrg=(await getOrCreateAssociatedTokenAccount(conn,admin,mfrg,buyer.publicKey)).address;
  const rogueTreasury=(await getOrCreateAssociatedTokenAccount(conn,admin,fakeUsdc,attacker.publicKey)).address;
  await mintTo(conn,admin,mfrg,sellerMfrg,admin,MAX);
  await mintTo(conn,admin,fakeUsdc,buyerUsdc,admin,10n*one);
  pass('two isolated 6-decimal mock mints and separate buyer/merchant token accounts');

  const [sale] = PublicKey.findProgramAddressSync(
    [Buffer.from('sale'),mfrg.toBuffer()],programId);
  const vault=getAssociatedTokenAddressSync(mfrg,sale,true);
  const [record]=PublicKey.findProgramAddressSync(
    [Buffer.from('buyer'),sale.toBuffer(),buyer.publicKey.toBuffer()],programId);
  const initAccounts={
    admin:admin.publicKey,saleMint:mfrg,usdcMint:fakeUsdc,
    treasuryOwner:merchant.publicKey,treasuryUsdc,
    sale,vault,tokenProgram:TOKEN_PROGRAM_ID,
    associatedTokenProgram:ASSOCIATED_TOKEN_PROGRAM_ID,
    systemProgram:SystemProgram.programId,
  };
  const now=Math.floor(Date.now()/1000);
  const start=now-10, end=now+600;
  const price=50_000; // FAKE price, 0.05 FAKE USDC/mFRG, NOT official sale terms
  await send(program,'initializeSale',[
    new anchor.BN(price),new anchor.BN(3n*one),new anchor.BN(start),new anchor.BN(end)
  ],initAccounts);
  let state=await program.account.sale.fetch(sale);
  assert.equal(state.paused,true,'Initialize must start PAUSED');
  assert.equal(state.sold.toString(),'0');
  assert.equal(state.treasuryUsdc.toBase58(),treasuryUsdc.toBase58());
  await transfer(conn,admin,sellerMfrg,vault,admin,MAX);
  assert.equal(await getBalance(conn,vault),MAX);
  pass('on-chain sale PDA initialized paused; entire 5M mock mFRG escrowed');

  const purchaseAccounts={
    buyer:buyer.publicKey,saleMint:mfrg,usdcMint:fakeUsdc,
    sale,vault,buyerUsdc,buyerMfrg,treasuryUsdc,
    buyerRecord:record,tokenProgram:TOKEN_PROGRAM_ID,
    systemProgram:SystemProgram.programId
  };
  await rejected('cannot purchase while paused',()=>send(
    program,'purchase',[new anchor.BN(2n*one),new anchor.BN(100_000)],
    purchaseAccounts,[buyer]));
  assert.equal(await getBalance(conn,treasuryUsdc),0n);
  await rejected('attacker cannot unpause administrator-owned sale',()=>send(
    program,'setPaused',[false],{sale,admin:attacker.publicKey},[attacker]));
  await send(program,'setPaused',[false],{sale,admin:admin.publicKey});
  state=await program.account.sale.fetch(sale);
  assert.equal(state.paused,false);
  pass('owner-only unpause enforced and sale becomes available');

  const beforeBuyer=await getBalance(conn,buyerUsdc);
  const first=await send(program,'purchase',[
    new anchor.BN(2n*one),new anchor.BN(100_000)
  ],purchaseAccounts,[buyer]);
  assert.ok(typeof first==='string' && first.length>=65);
  assert.equal(beforeBuyer-(await getBalance(conn,buyerUsdc)),100_000n);
  assert.equal(await getBalance(conn,treasuryUsdc),100_000n);
  assert.equal(await getBalance(conn,buyerMfrg),2n*one);
  assert.equal(await getBalance(conn,vault),MAX-2n*one);
  state=await program.account.sale.fetch(sale);
  assert.equal(state.sold.toString(),String(2n*one));
  pass('single native transaction transfers exactly 0.1 fake USDC and delivers 2 fake mFRG');

  const buyerBefore=await getBalance(conn,buyerUsdc);
  const treasuryBefore=await getBalance(conn,treasuryUsdc);
  const mfrgBefore=await getBalance(conn,buyerMfrg);
  await rejected('price/slippage ceiling rejects underpayment',()=>send(
    program,'purchase',[new anchor.BN(1n*one),new anchor.BN(49_999)],
    purchaseAccounts,[buyer]));
  assert.equal(await getBalance(conn,buyerUsdc),buyerBefore);
  assert.equal(await getBalance(conn,treasuryUsdc),treasuryBefore);
  pass('slippage rejection leaves USDC balances unchanged');

  await rejected('attacker-substituted USDC treasury rejected',()=>send(
    program,'purchase',[new anchor.BN(1n*one),new anchor.BN(50_000)],
    {...purchaseAccounts,treasuryUsdc:rogueTreasury},[buyer]));
  assert.equal(await getBalance(conn,rogueTreasury),0n);
  pass('treasury substitution cannot steal payment');

  // Force mFRG transfer #2 to fail *after* the USDC debit CPI.
  await freezeAccount(conn,admin,buyerMfrg,mfrg,admin);
  await rejected('frozen buyer mFRG account causes atomic rollback',()=>send(
    program,'purchase',[new anchor.BN(1n*one),new anchor.BN(50_000)],
    purchaseAccounts,[buyer]));
  assert.equal(await getBalance(conn,buyerUsdc),buyerBefore);
  assert.equal(await getBalance(conn,treasuryUsdc),treasuryBefore);
  assert.equal(await getBalance(conn,buyerMfrg),mfrgBefore);
  assert.equal(await getBalance(conn,vault),MAX-2n*one);
  pass('failed second CPI rolls back first CPI USDC debit completely');
  await thawAccount(conn,admin,buyerMfrg,mfrg,admin);

  await send(program,'purchase',[new anchor.BN(one),new anchor.BN(50_000)],
    purchaseAccounts,[buyer]);
  assert.equal(await getBalance(conn,treasuryUsdc),150_000n);
  assert.equal(await getBalance(conn,buyerMfrg),3n*one);
  state=await program.account.sale.fetch(sale);
  assert.equal(state.sold.toString(),String(3n*one));
  let user=await program.account.buyerRecord.fetch(record);
  assert.equal(user.bought.toString(),String(3n*one));
  pass('second purchase persists per-wallet cumulative total and verified delivery');

  await rejected('per-wallet cumulative purchase limit enforced',()=>send(
    program,'purchase',[new anchor.BN(one),new anchor.BN(50_000)],
    purchaseAccounts,[buyer]));
  await rejected('absolute 5M allocation cap enforced',()=>send(
    program,'purchase',[new anchor.BN(MAX),new anchor.BN(MAX)],
    purchaseAccounts,[buyer]));
  assert.equal(await getBalance(conn,treasuryUsdc),150_000n);
  pass('wallet limit and absolute sale inventory cap never overcollect buyer USDC');

  await rejected('admin cannot withdraw escrow before sale end',()=>send(
    program,'withdrawUnsold',[new anchor.BN(one)],{
      admin:admin.publicKey,saleMint:mfrg,sale,vault,
      adminMfrg:sellerMfrg,tokenProgram:TOKEN_PROGRAM_ID
    }));
  assert.equal(await getBalance(conn,vault),MAX-3n*one);
  pass('unsold inventory locked throughout sale');

  await send(program,'setPaused',[true],{sale,admin:admin.publicKey});
  await rejected('paused sale refuses resumed buyer payment',()=>send(
    program,'purchase',[new anchor.BN(one),new anchor.BN(50_000)],
    purchaseAccounts,[buyer]));
  pass('administrative emergency pause blocks transfers');

  console.log(JSON.stringify({
    status:'passed',
    checks,
    environment:'isolated_loopback_test_validator',
    program:programId.toBase58(),
    fake_mfrg_mint:mfrg.toBase58(),
    fake_usdc_mint:fakeUsdc.toBase58(),
    buyer_received_mfrg_atomic:(await getBalance(conn,buyerMfrg)).toString(),
    treasury_received_fake_usdc_atomic:(await getBalance(conn,treasuryUsdc)).toString(),
    remaining_vault_mfrg_atomic:(await getBalance(conn,vault)).toString(),
    sale_sold_atomic:(await program.account.sale.fetch(sale)).sold.toString(),
    real_usdc_used:false,
    mainnet_used:false
  },null,2));
}
main().catch(error => {
  console.error('LOCAL_SWAP_FAILED',error.stack||error.message||String(error));
  process.exitCode=2;
});
