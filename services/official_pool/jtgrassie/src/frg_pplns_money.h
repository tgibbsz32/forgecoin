/* Exact uint64-atomic payouts at the audited default PPLNS multiplier 2.0.
 * No floating point used for miner balances or fractional fee accounting.
 * __uint128_t supported by Linux GCC/Clang on x86_64 and aarch64.
 */
#ifndef FRG_PPLNS_MONEY_H
#define FRG_PPLNS_MONEY_H
#include <stdint.h>
static inline uint64_t frg_pplns_share_reward_atomic(
    uint64_t share_difficulty, uint64_t block_difficulty, uint64_t reward)
{
    if (!share_difficulty || !block_difficulty || !reward) return 0;
    __uint128_t numerator=(__uint128_t)share_difficulty*reward;
    __uint128_t denominator=(__uint128_t)block_difficulty*2u;
    __uint128_t amount=numerator/denominator;
    return amount > reward ? reward : (uint64_t)amount;
}
#endif
