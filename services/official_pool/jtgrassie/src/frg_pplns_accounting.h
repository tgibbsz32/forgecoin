/* Native FRG PPLNS bounded allocation, research-only.
 * Converts a single share's pro-rata allocation to 8-decimal atomic units
 * with a strict per-block remaining-reward cap. Does not authorize transfers.
 */
#ifndef FRG_PPLNS_ACCOUNTING_H
#define FRG_PPLNS_ACCOUNTING_H

#include <math.h>
#include <stdbool.h>
#include <stdint.h>

/* False on invalid difficulty, NaN/Inf or corrupted accounting inputs.
 * On success, *out is within [0, block_reward - credited_so_far].
 * Long double avoids overflow in share*reward intermediates; cap BEFORE
 * conversion to uint64_t to avoid undefined out-of-range float casts.
 */
static inline bool
frg_pplns_share_atomic(uint64_t share_difficulty, uint64_t block_difficulty,
                      double share_multiplier, uint64_t block_reward,
                      uint64_t credited_so_far, uint64_t *out)
{
    if (!out || !block_difficulty || !isfinite(share_multiplier) ||
        share_multiplier <= 0.0 || credited_so_far > block_reward)
        return false;
    const uint64_t remaining = block_reward - credited_so_far;
    const long double denominator =
        (long double)block_difficulty * (long double)share_multiplier;
    if (!(denominator > 0.0L) || !isfinite(denominator))
        return false;
    const long double proposed = floorl(
        ((long double)share_difficulty / denominator) *
        (long double)block_reward);
    if (!isfinite(proposed) || proposed < 0.0L)
        return false;
    if (proposed >= (long double)remaining)
        *out = remaining;
    else
        *out = (uint64_t)proposed;
    return true;
}

/* If shares cannot account for the full candidate reward, do not write
 * an unlocked block and silently strand the undistributed remainder.
 */
static inline bool
frg_pplns_fully_accounted(uint64_t block_reward, uint64_t credited_total)
{
    return block_reward != UINT64_C(0) && credited_total == block_reward;
}

#endif
