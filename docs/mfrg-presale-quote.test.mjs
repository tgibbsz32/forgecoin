import assert from 'node:assert/strict';
import {test} from 'node:test';
import {parseTokens,quoteTokens,formatUnits,ROUND_UNITS} from './mfrg-presale-quote.mjs';
test('preview sells first million for 10000 USD',()=>{
 const r=quoteTokens({amount:'1000000'});
 assert.equal(r.paymentMicroUsdc,10000n*1000000n);
});
test('full sale totals 150000 USD',()=>assert.equal(quoteTokens({amount:'5000000'}).paymentMicroUsdc,150000n*1000000n));
test('tier boundary costs 0.3 USDC',()=>{
 const r=quoteTokens({amount:'20',soldUnits:ROUND_UNITS-10n*1000000n});
 assert.equal(r.paymentMicroUsdc,300000n);
 assert.deepEqual(r.tiers.map(x=>x.round),[1,2]);
});
test('partial token rounding does not undercharge',()=>assert.equal(quoteTokens({amount:'0.000001'}).paymentMicroUsdc,1n));
test('reject malformed and overflow',()=>{
 for(const s of ['1e6','NaN','-10','1.0000001','5000001','01',''])assert.throws(()=>parseTokens(s));
});
test('display correct unit values',()=>{
 assert.equal(formatUnits(12000000n),'12.00');
 assert.equal(formatUnits(12345000n),'12.345');
});
