/* ForgeCoin native pool reward confirmation and maturity bounds.
 *
 * A stored block's shares may be allocated ONLY after the canonical chain
 * independently confirms the block and at least 60 heights have elapsed.
 * These arithmetic helpers make no chain-canonicality decision and cannot
 * authorize a wallet payout; FRG_TESTED_WALLET_PAYOUTS remains disabled.
 */
#ifndef FRG_REWARD_MATURITY_H
#define FRG_REWARD_MATURITY_H

#include <stdbool.h>
#include <stdint.h>

#define FRG_MINED_REWARD_UNLOCK_WINDOW UINT64_C(60)

/* Subtraction avoids block_height + 60 overflowing uint64_t and avoids
 * an underflow if a stale/future stored candidate is checked.
 */
static inline bool
frg_reward_mature(uint64_t block_height, uint64_t tip_height)
{
    return tip_height >= block_height &&
           tip_height - block_height >= FRG_MINED_REWARD_UNLOCK_WINDOW;
}

/* Window of canonical headers at exactly tip-60, backwards count entries.
 * Must not silently scan an incomplete range near genesis. No allocations
 * are authorized here: process_blocks validates block hashes and parents.
 */
static inline bool
frg_mature_header_window(uint64_t tip_height, uint64_t count,
                         uint64_t *start, uint64_t *end)
{
    if (!start || !end || count == 0 ||
        tip_height < FRG_MINED_REWARD_UNLOCK_WINDOW)
        return false;
    const uint64_t last = tip_height - FRG_MINED_REWARD_UNLOCK_WINDOW;
    if (last < count - UINT64_C(1))
        return false;
    *end = last;
    *start = last - (count - UINT64_C(1));
    return true;
}

#endif
