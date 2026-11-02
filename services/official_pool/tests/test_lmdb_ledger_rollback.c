/* Real LMDB parent/child atomicity regression for FRG research-pool credits.
 * Failure is injected into an unpositioned MDB_CURRENT status cursor.
 * This is an isolated LMDB behavior fixture, not the running pool callback.
 * No daemon, funds, wallet, network sockets or payout authorization.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <lmdb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "../jtgrassie/src/frg_currency.h"

#define CHECK(call) do { int code_ = (call); if (code_) { \
    fprintf(stderr, "LMDB failed %s: %s\n", #call, mdb_strerror(code_)); \
    abort(); } } while (0)

static MDB_val val(const char *s)
{
    MDB_val out = {strlen(s), (void *)s};
    return out;
}

static void set_text(MDB_txn *txn, MDB_dbi db, const char *key,
                     const char *value)
{
    MDB_val k = val(key), v = val(value);
    CHECK(mdb_put(txn, db, &k, &v, 0));
}

static void expect_text(MDB_env *env, MDB_dbi db, const char *key,
                        const char *expected)
{
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    MDB_val k = val(key), v;
    int rc = mdb_get(txn, db, &k, &v);
    if (!expected)
        assert(rc == MDB_NOTFOUND);
    else {
        CHECK(rc);
        assert(v.mv_size == strlen(expected));
        assert(memcmp(v.mv_data, expected, v.mv_size) == 0);
    }
    mdb_txn_abort(txn);
}

static void credit_nested(MDB_env *env, MDB_txn *parent, MDB_dbi balances)
{
    MDB_txn *child = NULL;
    CHECK(mdb_txn_begin(env, parent, 0, &child));
    /* Intentional distinct ledger keys: exact 1% per 1.0 FRG reward. */
    assert(frg_pool_fee_atomic(UINT64_C(100000000)) == UINT64_C(1000000));
    set_text(child, balances, "pool_fee", "1000000");
    set_text(child, balances, "miner_a", "99000000");
    CHECK(mdb_txn_commit(child)); /* visible only when PARENT commits */
}

int main(void)
{
    char directory[] = "/tmp/frg-native-ledger-XXXXXX";
    assert(mkdtemp(directory) != NULL);
    MDB_env *env = NULL;
    CHECK(mdb_env_create(&env));
    CHECK(mdb_env_set_maxdbs(env, 4));
    CHECK(mdb_env_set_mapsize(env, 4 * 1024 * 1024));
    CHECK(mdb_env_open(env, directory, 0, 0600));

    MDB_dbi blocks = 0, balances = 0;
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(env, NULL, 0, &txn));
    CHECK(mdb_dbi_open(txn, "blocks", MDB_CREATE, &blocks));
    CHECK(mdb_dbi_open(txn, "balances", MDB_CREATE, &balances));
    set_text(txn, blocks, "block_61", "LOCKED");
    CHECK(mdb_txn_commit(txn));
    expect_text(env, blocks, "block_61", "LOCKED");

    /* Simulate the historical unsafe sequence: nested credits succeed, but
     * MDB_CURRENT cannot update a cursor with no current position. The new
     * pool code MUST abort this parent before it can persist credits.
     */
    CHECK(mdb_txn_begin(env, NULL, 0, &txn));
    credit_nested(env, txn, balances);
    MDB_cursor *cursor = NULL;
    CHECK(mdb_cursor_open(txn, blocks, &cursor));
    MDB_val key = val("block_61"), unlocked = val("UNLOCKED");
    int failed_status_write = mdb_cursor_put(cursor, &key, &unlocked, MDB_CURRENT);
    assert(failed_status_write != 0);
    mdb_cursor_close(cursor);
    mdb_txn_abort(txn);
    expect_text(env, blocks, "block_61", "LOCKED");
    expect_text(env, balances, "pool_fee", NULL);
    expect_text(env, balances, "miner_a", NULL);

    /* Happy path: position cursor, update status, commit the SAME parent
     * containing both nested ledger credits, then all become visible.
     */
    CHECK(mdb_txn_begin(env, NULL, 0, &txn));
    credit_nested(env, txn, balances);
    CHECK(mdb_cursor_open(txn, blocks, &cursor));
    MDB_val previous;
    CHECK(mdb_cursor_get(cursor, &key, &previous, MDB_SET));
    CHECK(mdb_cursor_put(cursor, &key, &unlocked, MDB_CURRENT));
    mdb_cursor_close(cursor);
    CHECK(mdb_txn_commit(txn));
    expect_text(env, blocks, "block_61", "UNLOCKED");
    expect_text(env, balances, "pool_fee", "1000000");
    expect_text(env, balances, "miner_a", "99000000");

    mdb_env_close(env);
    char name[512];
    snprintf(name, sizeof name, "%s/data.mdb", directory); CHECK(unlink(name));
    snprintf(name, sizeof name, "%s/lock.mdb", directory); CHECK(unlink(name));
    CHECK(rmdir(directory));
    puts("PASS: native LMDB failed block-status update rolls back fee and miner child credits");
    return 0;
}
