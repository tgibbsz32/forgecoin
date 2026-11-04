/* Real LMDB restart/duplicate/ambiguous/fail-closed test for a DORMANT
 * payout INTENT module. No wallet RPC, daemon, transfer, share or network.
 * Never enables FRG_TESTED_WALLET_PAYOUTS.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <lmdb.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "../jtgrassie/src/frg_payout_intent_journal.h"

#define CHECK(expr) do { int r_ = (expr); if (r_ != 0) { \
    fprintf(stderr, "%s failed at %s:%d: %s (%d)\n", #expr, __FILE__, \
            __LINE__, mdb_strerror(r_), r_); abort(); \
} } while (0)

static const uint8_t BATCH_ID[32] = {1};
static const uint8_t MANIFEST[32] = {2};
static const uint8_t ANCHOR[32] = {3};
static const uint8_t TXID[32] = {4};
static const uint8_t DIFFERENT_TXID[32] = {5};
static const uint8_t EMPTY[32] = {0};

static void open_ledger(const char *path, MDB_env **env, MDB_dbi *db)
{
    CHECK(mdb_env_create(env));
    CHECK(mdb_env_set_maxdbs(*env, 4));
    CHECK(mdb_env_set_mapsize(*env, 4 * 1024 * 1024));
    /* Explicitly no MDB_NOSYNC, MDB_NOMETASYNC or MDB_WRITEMAP. */
    CHECK(mdb_env_open(*env, path, 0, 0600));
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(*env, NULL, 0, &txn));
    CHECK(frg_payout_intent_open(txn, db));
    CHECK(mdb_txn_commit(txn));
}

static void read_record(MDB_env *env, MDB_dbi db,
                        uint32_t expected_state, bool expect_candidate)
{
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    frg_payout_intent_record_t record;
    CHECK(frg_payout_intent_read(txn, db, BATCH_ID, &record));
    assert(record.version == FRG_PAYOUT_INTENT_VERSION);
    assert(record.state == expected_state);
    assert(record.amount_atomic == UINT64_C(100000000));
    assert(record.max_fee_atomic == UINT64_C(12000));
    assert(record.anchor_height == UINT64_C(150));
    assert(memcmp(record.manifest_sha256, MANIFEST, 32) == 0);
    assert(memcmp(record.anchor_hash, ANCHOR, 32) == 0);
    assert(memcmp(record.candidate_txid, expect_candidate ? TXID : EMPTY, 32) == 0);
    bool held = false;
    CHECK(frg_payout_intent_held(txn, db, &held));
    assert(held);
    mdb_txn_abort(txn);
}

static void cleanup(MDB_env *env, MDB_dbi db, const char *directory)
{
    mdb_dbi_close(env, db);
    mdb_env_close(env);
    char file[512];
    snprintf(file, sizeof file, "%s/data.mdb", directory);
    CHECK(unlink(file));
    snprintf(file, sizeof file, "%s/lock.mdb", directory);
    CHECK(unlink(file));
    CHECK(rmdir(directory));
}

int main(void)
{
    char directory[] = "/tmp/frg-payout-intent-XXXXXX";
    assert(mkdtemp(directory));
    MDB_env *env = NULL;
    MDB_dbi db = 0;
    open_ledger(directory, &env, &db);
    MDB_txn *txn = NULL;
    bool held = true;

    CHECK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    CHECK(frg_payout_intent_held(txn, db, &held));
    assert(!held);
    frg_payout_intent_record_t record;
    assert(frg_payout_intent_read(txn, db, BATCH_ID, &record) == MDB_NOTFOUND);
    mdb_txn_abort(txn);

    /* No malformed batch can be persisted, including a fee cap that
     * exceeds the credited amount. */
    CHECK(mdb_txn_begin(env, NULL, 0, &txn));
    assert(frg_payout_intent_prepare(txn, db, EMPTY, MANIFEST, ANCHOR,
                                     150, 100000000, 12000) == EINVAL);
    assert(frg_payout_intent_prepare(txn, db, BATCH_ID, EMPTY, ANCHOR,
                                     150, 100000000, 12000) == EINVAL);
    assert(frg_payout_intent_prepare(txn, db, BATCH_ID, MANIFEST, EMPTY,
                                     150, 100000000, 12000) == EINVAL);
    assert(frg_payout_intent_prepare(txn, db, BATCH_ID, MANIFEST, ANCHOR,
                                     150, 0, 12000) == EINVAL);
    assert(frg_payout_intent_prepare(txn, db, BATCH_ID, MANIFEST, ANCHOR,
                                     150, 100, 101) == EINVAL);
    /* Aborted batch MUST not be replayed as successfully reserved. */
    CHECK(frg_payout_intent_prepare(txn, db, BATCH_ID, MANIFEST, ANCHOR,
                                    150, 100000000, 12000));
    mdb_txn_abort(txn);

    CHECK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    assert(frg_payout_intent_read(txn, db, BATCH_ID, &record) == MDB_NOTFOUND);
    CHECK(frg_payout_intent_held(txn, db, &held));
    assert(!held);
    mdb_txn_abort(txn);

    CHECK(mdb_txn_begin(env, NULL, 0, &txn));
    CHECK(frg_payout_intent_prepare(txn, db, BATCH_ID, MANIFEST, ANCHOR,
                                    150, 100000000, 12000));
    assert(frg_payout_intent_prepare(txn, db, BATCH_ID, MANIFEST, ANCHOR,
                                     150, 100000000, 12000) == MDB_KEYEXIST);
    assert(frg_payout_intent_prepare(txn, db, BATCH_ID, MANIFEST, ANCHOR,
                                     150, 100000000, 0) == MDB_KEYEXIST);
    CHECK(mdb_txn_commit(txn));
    read_record(env, db, FRG_PAYOUT_INTENT_PREPARED, false);

    /* Restart persistence of the pre-send intent, before ANY wallet call. */
    mdb_dbi_close(env, db);
    mdb_env_close(env);
    env = NULL;
    open_ledger(directory, &env, &db);
    read_record(env, db, FRG_PAYOUT_INTENT_PREPARED, false);

    CHECK(mdb_txn_begin(env, NULL, 0, &txn));
    CHECK(frg_payout_intent_mark_ambiguous(txn, db, BATCH_ID));
    assert(frg_payout_intent_mark_ambiguous(txn, db, BATCH_ID) == EALREADY);
    CHECK(mdb_txn_commit(txn));
    read_record(env, db, FRG_PAYOUT_INTENT_AMBIGUOUS, false);

    mdb_dbi_close(env, db);
    mdb_env_close(env);
    env = NULL;
    open_ledger(directory, &env, &db);
    read_record(env, db, FRG_PAYOUT_INTENT_AMBIGUOUS, false);

    CHECK(mdb_txn_begin(env, NULL, 0, &txn));
    assert(frg_payout_intent_note_candidate(txn, db, BATCH_ID, EMPTY) == EINVAL);
    CHECK(frg_payout_intent_note_candidate(txn, db, BATCH_ID, TXID));
    assert(frg_payout_intent_note_candidate(txn, db, BATCH_ID, TXID) == EALREADY);
    assert(frg_payout_intent_note_candidate(txn, db, BATCH_ID,
                                            DIFFERENT_TXID) == EALREADY);
    CHECK(mdb_txn_commit(txn));
    read_record(env, db, FRG_PAYOUT_INTENT_CANDIDATE_UNVERIFIED, true);
    mdb_dbi_close(env, db);
    mdb_env_close(env);
    env = NULL;
    open_ledger(directory, &env, &db);
    read_record(env, db, FRG_PAYOUT_INTENT_CANDIDATE_UNVERIFIED, true);

    /* A corrupted journal MUST hold payouts and return a hard error. */
    CHECK(mdb_txn_begin(env, NULL, 0, &txn));
    MDB_val key = { 32, (void *)BATCH_ID };
    uint8_t malformed = 0x42;
    MDB_val val = { 1, &malformed };
    CHECK(mdb_put(txn, db, &key, &val, 0));
    CHECK(mdb_txn_commit(txn));
    CHECK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    held = false;
    assert(frg_payout_intent_read(txn, db, BATCH_ID, &record) == MDB_BAD_VALSIZE);
    assert(frg_payout_intent_held(txn, db, &held) == MDB_BAD_VALSIZE);
    assert(held);
    mdb_txn_abort(txn);

    cleanup(env, db, directory);
    puts("PASS: LMDB payout intents survive restart, reject replay, ambiguous retry, invalid input and corrupt records; no balances debited");
    return 0;
}
