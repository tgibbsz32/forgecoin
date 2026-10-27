'use strict';
/* Development-only static gates. On-chain balance assertions live in atomic-local.cjs. */
const assert = require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const saleDir=path.resolve(root,'..');
const project=path.resolve(saleDir,'..','..');
const program=fs.readFileSync(path.join(root,'programs/miniforge_swap/src/lib.rs'),'utf8');
const cargo=fs.readFileSync(path.join(root,'programs/miniforge_swap/Cargo.toml'),'utf8');
const ignore=fs.readFileSync(path.join(root,'.gitignore'),'utf8');
const idl=JSON.parse(fs.readFileSync(path.join(root,'idl/miniforge_swap.json'),'utf8'));
const status=JSON.parse(fs.readFileSync(path.join(project,'docs/sale-status.json'),'utf8'));
const website=fs.readFileSync(path.join(project,'docs/sale.js'),'utf8');
let count=0;
function check(phrase,assertion){assertion();console.log('PASS '+(++count)+' '+phrase);}
check('IDL matches dedicated test-only public program identifier',()=>{
  assert.equal(idl.address,'5NrwtM49RAn5iQicbod539qxhqYRkV3ZpiBudoUCUGNY');
  for(const name of ['initialize_sale','purchase','set_paused','set_price','withdraw_unsold'])
    assert.ok(idl.instructions.find(x=>x.name===name),name);
});
check('5M on-chain sale cap enforced',()=>{
  assert.match(program,/SALE_CAP_ATOMIC:\s*u64\s*=\s*5_000_000_000_000/);
  assert.match(program,/new_sold <= SALE_CAP_ATOMIC/);
});
check('devnet mint pinned in normal non-test build',()=>{
  assert.match(program,/9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw/);
  assert.match(program,/WrongDevnetMint/);
  assert.match(program,/cfg\(not\(feature = "local-mock-mints"\)\)/);
  assert.match(cargo,/default\s*=\s*\["devnet-only"\]/);
  assert.match(program,/compile_error!/);
});
check('atomic two-sided token-program transfer mechanism present',()=>{
  assert.match(program,/USDC debit/);
  assert.match(program,/Program escrow PDA/);
  assert.equal((program.match(/token::transfer_checked\(/g)||[]).length,3);
  assert.match(program,/SlippageExceeded/);
  assert.match(program,/BuyerCapExceeded/);
  assert.match(program,/PriceLocked/);
});
check('test keypairs and binaries excluded from repository',()=>{
  assert.match(ignore,/\.secrets\//);
  assert.match(ignore,/target\//);
  assert.match(ignore,/node_modules\//);
});
check('published sale remains impossible to activate via status data',()=>{
  assert.equal(status.sale_enabled,false);
  assert.equal(status.payments_enabled,false);
  assert.equal(status.fulfillment_enabled,false);
  assert.equal(status.token_mainnet_mint,null);
  assert.match(website,/CHECKOUT_LOCKED = true/);
  assert.match(website,/quoteButton.disabled = true/);
});
console.log('PASS CONTRACT_STATIC_GUARDS='+count);
