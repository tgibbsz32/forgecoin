/* Exact, side-effect-free mFRG presale quote math.
 * No price or settlement authority: server must independently verify current
 * sold count and atomically settle payment and delivery within an audited program.
 * Token and payment units use 6 decimals (mFRG and USDC on Solana).
 */
export const TIERS = Object.freeze([10000n,20000n,30000n,40000n,50000n]); // USDC micro-units per whole mFRG
export const UNITS = 1000000n;
export const ROUND_SUPPLY = 1000000n * UNITS;
export const MAX_SUPPLY = BigInt(TIERS.length) * ROUND_SUPPLY;
export function quoteMfrg({soldUnits,desiredUnits}) {
  if(typeof soldUnits!=="bigint" || typeof desiredUnits!=="bigint") throw new TypeError("BigInt units required");
  if(soldUnits < 0n || soldUnits > MAX_SUPPLY || desiredUnits <= 0n || desiredUnits > MAX_SUPPLY - soldUnits)
    throw new RangeError("Invalid purchase or insufficient inventory");
  let cursor=soldUnits, left=desiredUnits, numerator=0n; const allocations=[];
  while(left>0n){
    const tier=Number(cursor/ROUND_SUPPLY), inside=cursor%ROUND_SUPPLY;
    const amount=left<ROUND_SUPPLY-inside?left:ROUND_SUPPLY-inside;
    numerator+=amount*TIERS[tier];
    allocations.push({tier:tier+1,tokenUnits:amount,priceMicroUsdcPerToken:TIERS[tier]});
    cursor+=amount;left-=amount;
  }
  // Round up USDC micro-units once at the end (protects sale revenue).
  return {tokenUnits:desiredUnits,paymentMicroUsdc:(numerator+UNITS-1n)/UNITS,allocations,nextSoldUnits:cursor};
}
export function quoteFromUsdPayment({soldUnits,paymentMicroUsdc}) {
  if(typeof soldUnits!=="bigint" || typeof paymentMicroUsdc!=="bigint" || soldUnits<0n || soldUnits>MAX_SUPPLY || paymentMicroUsdc<=0n)
    throw new RangeError("Invalid payment");
  let low=0n,high=MAX_SUPPLY-soldUnits;
  while(low<high){const mid=(low+high+1n)/2n;
    if(quoteMfrg({soldUnits,desiredUnits:mid}).paymentMicroUsdc<=paymentMicroUsdc)low=mid;else high=mid-1n;
  }
  return low===0n?null:quoteMfrg({soldUnits,desiredUnits:low});
}
