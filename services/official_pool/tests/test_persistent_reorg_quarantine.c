/* Standalone real-LMDB persistence regression for FRG deep-reorg hold.
 * No running pool, daemon, wallet, Stratum, funds or network.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <lmdb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "../jtgrassie/src/frg_accounting_quarantine.h"
#include "../jtgrassie/src/frg_reconcile_policy.h"

#define CHECK(expr) do { int rc_ = (expr); if (rc_) { \
    fprintf(stderr, "LMDB %s failed: %s\n", #expr, mdb_strerror(rc_)); \
    abort(); } } while(0)

static void open_ledger(const char *path, MDB_env **out_env, MDB_dbi *out_db)
{
    CHECK(mdb_env_create(out_env));
    CHECK(mdb_env_set_maxdbs(*out_env, 4));
    CHECK(mdb_env_set_mapsize(*out_env, 2 * 1024 * 1024));
    CHECK(mdb_env_open(*out_env, path, 0, 0600));
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(*out_env, NULL, 0, &txn));
    CHECK(mdb_dbi_open(txn, "properties", MDB_CREATE, out_db));
    CHECK(mdb_txn_commit(txn));
}

static void assert_held(MDB_env *env, MDB_dbi db, bool expected,
                        uint64_t expected_height)
{
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    bool held = true;
    uint64_t height = UINT64_MAX;
    CHECK(frg_quarantine_read(txn, db, &held, &height));
    assert(held == expected);
    assert(height == expected_height);
    mdb_txn_abort(txn);
}

int main(void)
{
    char directory[] = "/tmp/frg-persistent-hold-XXXXXX";
    assert(mkdtemp(directory));
    MDB_env *env = NULL;
    MDB_dbi db = 0;
    open_ledger(directory, &env, &db);
    assert_held(env, db, false, 0);

    /* An unlocked candidate found noncanonical triggers the same policy
     * that the real pool callback uses, then the marker is persisted.
     */
    assert(frg_reconcile_block(FRG_SAVED_UNLOCKED, 11, 11, 101,
                              false, true, false) ==
           FRG_RECONCILE_ABORT_DEEP_REORG);
    CHECK(frg_quarantine_mark(env, db, 11));
    assert_held(env, db, true, 11);
    /* Other observations never overwrite first recorded incident. */
    CHECK(frg_quarantine_mark(env, db, 57));
    assert_held(env, db, true, 11);

    /* A process restart must not clear the quarantine. */
    mdb_dbi_close(env, db);
    mdb_env_close(env);
    env = NULL;
    open_ledger(directory, &env, &db);
    assert_held(env, db, true, 11);

    /* Any malformed marker must fail closed even though mdb_get succeeds. */
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(env, NULL, 0, &txn));
    const char name[] = FRG_QUARANTINE_PROPERTY;
    MDB_val key = { sizeof(name) - 1, (void *)name };
    const unsigned char bad = 0x42;
    MDB_val value = { sizeof(bad), (void *)&bad };
    CHECK(mdb_put(txn, db, &key, &value, 0));
    CHECK(mdb_txn_commit(txn));
    CHECK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    bool held = false;
    assert(frg_quarantine_read(txn, db, &held, NULL) == MDB_BAD_VALSIZE);
    assert(held);
    mdb_txn_abort(txn);
    assert(frg_quarantine_mark(env, db, 99) == MDB_BAD_VALSIZE);

    mdb_dbi_close(env, db);
    mdb_env_close(env);
    char filename[512];
    snprintf(filename, sizeof filename, "%s/data.mdb", directory);
    CHECK(unlink(filename));
    snprintf(filename, sizeof filename, "%s/lock.mdb", directory);
    CHECK(unlink(filename));
    CHECK(rmdir(directory));
    puts("PASS: durable LMDB reorg quarantine survives restart, retains first height, rejects damaged marker");
    return 0;
}
