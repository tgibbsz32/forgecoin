import assert from 'node:assert/strict';
import {test} from 'node:test';
import {quoteMfrg,quoteFromUsdPayment,UNITS,ROUND_SUPPLY,MAX_SUPPLY} from './mfrg-quote.mjs';
test('full inventory revenue equals 150000 USDC',()=>{
 const q=quoteMfrg({soldUnits:0n,desiredUnits:MAX_SUPPLY});
 assert.equal(q.paymentMicroUsdc,150000n*UNITS);
 assert.equal(q.allocations.length,5);
});
test('crossing tier boundary charges two prices',()=>{
 const q=quoteMfrg({soldUnits:ROUND_SUPPLY-10n*UNITS,desiredUnits:20n*UNITS});
 assert.equal(q.paymentMicroUsdc,300000n);
 assert.deepEqual(q.allocations.map(x=>x.tier),[1,2]);
});
test('exact microtoken precision and rounding',()=>{
 const q=quoteMfrg({soldUnits:0n,desiredUnits:1n});
 assert.equal(q.paymentMicroUsdc,1n);
});
test('payment to token quote cannot overrun',()=>{
 const q=quoteFromUsdPayment({soldUnits:ROUND_SUPPLY,paymentMicroUsdc:20000000n});
 assert.equal(q.tokenUnits,1000n*UNITS);
});
test('rejects invalid amounts',()=>{
 assert.throws(()=>quoteMfrg({soldUnits:MAX_SUPPLY,desiredUnits:1n}),RangeError);
 assert.throws(()=>quoteMfrg({soldUnits:0n,desiredUnits:-1n}),RangeError);
});
