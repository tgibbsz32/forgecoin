// Static informational quote engine for proposed mFRG presale.
// No RPC, wallet signing, network writes, buyer deposits or trusted sale inventory.
export const PRICE_MICRO_USDC=[10000n,20000n,30000n,40000n,50000n];
export const TOKEN_UNITS=1000000n;
export const ROUND_UNITS=1000000n*TOKEN_UNITS;
export const SUPPLY_UNITS=5n*ROUND_UNITS;
export function parseTokens(value){
  if(typeof value!=='string'|| !/^(?:0|[1-9]\d*)(?:\.\d{1,6})?$/.test(value))throw new Error('Enter a token quantity with at most six decimals');
  const [whole,decimal='']=value.split('.');
  const units=BigInt(whole)*TOKEN_UNITS+BigInt(decimal.padEnd(6,'0'));
  if(units<=0n||units>SUPPLY_UNITS)throw new Error('Purchase amount exceeds presale supply');
  return units;
}
export function quoteTokens({amount,soldUnits=0n}){
 const requested=parseTokens(amount);
 if(typeof soldUnits!=='bigint'||soldUnits<0n||soldUnits>SUPPLY_UNITS||requested>SUPPLY_UNITS-soldUnits)throw new Error('Not enough simulated inventory');
 let cursor=soldUnits,left=requested,total=0n;const tiers=[];
 while(left>0n){
  const tier=Number(cursor/ROUND_UNITS);
  const fill=ROUND_UNITS-cursor%ROUND_UNITS;
  const allocated=left<fill?left:fill;
  total+=allocated*PRICE_MICRO_USDC[tier];
  tiers.push({round:tier+1,units:allocated,price:PRICE_MICRO_USDC[tier]});
  cursor+=allocated;left-=allocated;
 }
 return {tokenUnits:requested,paymentMicroUsdc:(total+TOKEN_UNITS-1n)/TOKEN_UNITS,tiers};
}
export function formatUnits(units,decimals=6){
 if(typeof units!=='bigint'||units<0n)throw new Error('Invalid value');
 const divisor=10n**BigInt(decimals);
 return (units/divisor).toLocaleString('en-US')+'.'+(units%divisor).toString().padStart(decimals,'0').replace(/0+$/,'').padEnd(2,'0');
}
