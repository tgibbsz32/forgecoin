/* Durable, fail-closed FRG pool accounting hold after a credited-block reorg.
 * Stored in the existing LMDB properties DB. There is intentionally NO
 * automatic unfreeze function: an operator must reconcile balances and
 * review an offline recovery procedure before changing this marker.
 * Wallet transfers and public mining remain separately disabled.
 */
#ifndef FRG_ACCOUNTING_QUARANTINE_H
#define FRG_ACCOUNTING_QUARANTINE_H

#include <lmdb.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define FRG_QUARANTINE_PROPERTY "frg.accounting.deep_reorg.quarantine.v1"

/* Return an error for malformed markers rather than treating them as absent.
 * A marker present with correct data holds accounting even after a restart.
 */
static inline int
frg_quarantine_read(MDB_txn *txn, MDB_dbi properties,
                    bool *held, uint64_t *first_height)
{
    if (!txn || !held)
        return EINVAL;
    *held = true; /* fail closed unless the read proves there is no marker */
    const char name[] = FRG_QUARANTINE_PROPERTY;
    MDB_val key = { sizeof(name) - 1, (void *)name };
    MDB_val value = { 0, NULL };
    int rc = mdb_get(txn, properties, &key, &value);
    if (rc == MDB_NOTFOUND)
    {
        *held = false;
        if (first_height) *first_height = 0;
        return 0;
    }
    if (rc) return rc;
    if (value.mv_size != sizeof(uint64_t) || !value.mv_data)
        return MDB_BAD_VALSIZE;
    if (first_height) memcpy(first_height, value.mv_data, sizeof(uint64_t));
    return 0;
}

/* Call ONLY after aborting the entire reward-crediting parent transaction.
 * The first recorded height is retained on subsequent alerts.
 */
static inline int
frg_quarantine_mark(MDB_env *env, MDB_dbi properties, uint64_t block_height)
{
    if (!env) return EINVAL;
    MDB_txn *txn = NULL;
    int rc = mdb_txn_begin(env, NULL, 0, &txn);
    if (rc) return rc;
    bool held = false;
    rc = frg_quarantine_read(txn, properties, &held, NULL);
    if (rc || held)
    {
        mdb_txn_abort(txn);
        return rc;
    }
    const char name[] = FRG_QUARANTINE_PROPERTY;
    MDB_val key = { sizeof(name) - 1, (void *)name };
    MDB_val value = { sizeof(block_height), &block_height };
    rc = mdb_put(txn, properties, &key, &value, MDB_NOOVERWRITE);
    if (rc)
    {
        mdb_txn_abort(txn);
        return rc;
    }
    return mdb_txn_commit(txn);
}

#endif
