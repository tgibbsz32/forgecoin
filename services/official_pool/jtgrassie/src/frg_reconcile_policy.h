/* Pure native ForgeCoin pool canonical-block decision policy.
 *
 * Called on every stored candidate, INCLUDING already credited candidates:
 * a deep reorg after credit must freeze reconciliation, not be ignored.
 * This code does not reverse transfers or authorize live wallet payouts.
 */
#ifndef FRG_RECONCILE_POLICY_H
#define FRG_RECONCILE_POLICY_H

#include <stdbool.h>
#include <stdint.h>
#include "frg_reward_maturity.h"

/* Keep in step with the jtgrassie-derived pool.c block_status enum. */
enum frg_saved_block_status {
    FRG_SAVED_LOCKED = 0,
    FRG_SAVED_UNLOCKED = 1,
    FRG_SAVED_ORPHANED = 2
};
enum frg_reconcile_action {
    FRG_RECONCILE_DEFER = 0,
    FRG_RECONCILE_ALREADY_CREDITED = 1,
    FRG_RECONCILE_ALREADY_ORPHANED = 2,
    FRG_RECONCILE_MARK_ORPHAN = 3,
    FRG_RECONCILE_CREDIT = 4,
    FRG_RECONCILE_ABORT_DEEP_REORG = 5,
    FRG_RECONCILE_ABORT_INVALID = 6
};

static inline enum frg_reconcile_action
frg_reconcile_block(uint32_t stored_status, uint64_t saved_height,
                    uint64_t observed_height, uint64_t tip_height,
                    bool hash_matches, bool parent_matches,
                    bool daemon_marks_orphan)
{
    if (observed_height != saved_height)
        return FRG_RECONCILE_ABORT_INVALID;
    const bool no_longer_canonical =
        !hash_matches || !parent_matches || daemon_marks_orphan;
    switch (stored_status)
    {
    case FRG_SAVED_UNLOCKED:
        return no_longer_canonical ? FRG_RECONCILE_ABORT_DEEP_REORG
                                  : FRG_RECONCILE_ALREADY_CREDITED;
    case FRG_SAVED_ORPHANED:
        return FRG_RECONCILE_ALREADY_ORPHANED;
    case FRG_SAVED_LOCKED:
        if (!frg_reward_mature(saved_height, tip_height))
            return FRG_RECONCILE_DEFER;
        return no_longer_canonical ? FRG_RECONCILE_MARK_ORPHAN
                                  : FRG_RECONCILE_CREDIT;
    default:
        return FRG_RECONCILE_ABORT_INVALID;
    }
}

#endif
