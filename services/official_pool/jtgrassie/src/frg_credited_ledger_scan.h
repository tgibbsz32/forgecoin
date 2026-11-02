/* Read-only, complete LMDB credited-candidate scanner.
 *
 * Scans every saved pool block record, including duplicate-height entries;
 * makes no ledger writes and never authorizes a payout.
 */
#ifndef FRG_CREDITED_LEDGER_SCAN_H
#define FRG_CREDITED_LEDGER_SCAN_H
#include <lmdb.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <time.h>
#include "frg_credited_history_audit.h"

/* Mirrors pool.c:block_t; enforce all memory layout assumptions in pool.c. */
typedef struct frg_history_saved_t {
    uint64_t height;
    char hash[64];
    char prev_hash[64];
    uint64_t difficulty;
    uint32_t status;
    uint64_t reward;
    time_t timestamp;
} frg_history_saved_t;

#define FRG_HISTORY_LOCKED 0u
#define FRG_HISTORY_UNLOCKED 1u
#define FRG_HISTORY_ORPHANED 2u

static inline int
frg_history_scan_credited(MDB_txn *txn, MDB_dbi db_blocks,
                          uint64_t requested_index, frg_history_saved_t *selected,
                          bool *has_selection, uint64_t *total)
{
    if (!txn || !selected || !has_selection || !total) return EINVAL;
    *has_selection = false;
    *total = 0;
    memset(selected, 0, sizeof(*selected));
    MDB_cursor *cursor = NULL;
    int rc = mdb_cursor_open(txn, db_blocks, &cursor);
    if (rc) return rc;
    MDB_cursor_op op = MDB_FIRST;
    MDB_val key = {0, NULL}, value = {0, NULL};
    while ((rc = mdb_cursor_get(cursor, &key, &value, op)) == 0)
    {
        op = MDB_NEXT;
        if (key.mv_size != sizeof(uint64_t) ||
            value.mv_size != sizeof(frg_history_saved_t) ||
            !key.mv_data || !value.mv_data)
        {
            rc = EPROTO;
            break;
        }
        frg_history_saved_t item = {0};
        uint64_t key_height = 0;
        memcpy(&item, value.mv_data, sizeof(item));
        memcpy(&key_height, key.mv_data, sizeof(key_height));
        if (item.height != key_height || item.status > FRG_HISTORY_ORPHANED ||
            !frg_fixed_hash64(item.hash) || !frg_fixed_hash64(item.prev_hash))
        {
            rc = EPROTO;
            break;
        }
        if (item.status != FRG_HISTORY_UNLOCKED) continue;
        if (!item.difficulty || !item.reward || *total == UINT64_MAX)
        {
            rc = EPROTO;
            break;
        }
        if (*total == requested_index)
        {
            *selected = item;
            *has_selection = true;
        }
        ++*total;
    }
    mdb_cursor_close(cursor);
    return rc == MDB_NOTFOUND ? 0 : rc;
}
#endif
