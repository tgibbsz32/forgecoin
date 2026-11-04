/* Native canonical payout reservation: real LMDB; NO wallet/daemon/miner.
 * Test addresses and hashes are synthetic NON-SPENDABLE examples.
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

#include "../jtgrassie/src/frg_payout_batch_reservation.h"

static unsigned tests = 0;
#define VERIFY(condition) do { ++tests; assert(condition); } while (0)
#define OK(expression) do { int rc_ = (expression); ++tests; \
    if (rc_ != 0) { fprintf(stderr, "LMDB error %d at line %d\n", \
                             rc_, __LINE__); abort(); } } while (0)

static void open_ledger(const char *path, unsigned flags,
                        MDB_env **env, MDB_dbi *db)
{
    OK(mdb_env_create(env));
    OK(mdb_env_set_maxdbs(*env, 4));
    OK(mdb_env_set_mapsize(*env, 8 * 1024 * 1024));
    OK(mdb_env_open(*env, path, flags, 0600));
    MDB_txn *txn = NULL;
    OK(mdb_txn_begin(*env, NULL, 0, &txn));
    OK(frg_payout_intent_open(txn, db));
    OK(mdb_txn_commit(txn));
}

static void close_ledger(MDB_env *env, MDB_dbi db)
{
    mdb_dbi_close(env, db);
    mdb_env_close(env);
}

static void cleanup_dir(const char *directory)
{
    char path[512];
    int n = snprintf(path, sizeof path, "%s/data.mdb", directory);
    VERIFY(n > 0 && (size_t)n < sizeof path);
    VERIFY(unlink(path) == 0);
    n = snprintf(path, sizeof path, "%s/lock.mdb", directory);
    VERIFY(n > 0 && (size_t)n < sizeof path);
    VERIFY(unlink(path) == 0);
    VERIFY(rmdir(directory) == 0);
}

int main(void)
{
    char folder[] = "/tmp/frg-reservation-sync-XXXXXX";
    VERIFY(mkdtemp(folder) != NULL);
    MDB_env *env = NULL;
    MDB_dbi db;
    open_ledger(folder, 0, &env, &db);

    char a[96], b[96];
    a[0] = '4'; memset(a + 1, 'A', 94); a[95] = 0;
    b[0] = '5'; memset(b + 1, 'B', 94); b[95] = 0;
    frg_payout_recipient_t recipients[2] = {
        {a, UINT64_C(100000000)}, {b, UINT64_C(230000000)}
    };
    const uint8_t source[32] = {7}, next_source[32] = {8};
    const uint8_t anchor[32] = {3}, candidate[32] = {4};
    uint8_t wrong_chain[16], id[32], digest[32];
    memcpy(wrong_chain, FRG_PAYOUT_FROZEN_CHAIN_ID, 16);
    wrong_chain[0] ^= 0x01;
    memset(id, 0xaa, 32);
    memset(digest, 0xbb, 32);
    uint64_t total = UINT64_MAX;

    VERIFY(frg_payout_batch_reserve(env, db, wrong_chain, source, anchor,
        150, recipients, 2, 12000, id, digest, &total) == EINVAL);
    VERIFY(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        source, anchor, 59, recipients, 2, 12000,
        id, digest, &total) == EINVAL);
    VERIFY(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        source, anchor, 150, recipients, 2, UINT64_C(330000001),
        id, digest, &total) == EINVAL);
    VERIFY(id[0] == 0xaa && digest[0] == 0xbb && total == UINT64_MAX);

    MDB_txn *txn = NULL;
    OK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    bool held = true;
    OK(frg_payout_intent_held(txn, db, &held));
    VERIFY(!held); /* Invalid calls cannot even prepare a journal record. */
    mdb_txn_abort(txn);

    uint8_t expected_id[32] = {0}, expected_manifest[32] = {0};
    uint64_t expected_total = 0;
    OK(frg_payout_manifest_hash(FRG_PAYOUT_FROZEN_CHAIN_ID, source,
        anchor, 150, recipients, 2, 12000,
        expected_id, expected_manifest, &expected_total));
    OK(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        source, anchor, 150, recipients, 2, 12000, id, digest, &total));
    VERIFY(total == UINT64_C(330000000));
    VERIFY(total == expected_total);
    VERIFY(memcmp(id, expected_id, 32) == 0);
    VERIFY(memcmp(digest, expected_manifest, 32) == 0);

    OK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    frg_payout_intent_record_t record;
    OK(frg_payout_intent_read(txn, db, id, &record));
    VERIFY(record.state == FRG_PAYOUT_INTENT_PREPARED);
    VERIFY(record.amount_atomic == total);
    VERIFY(record.max_fee_atomic == 12000);
    VERIFY(record.anchor_height == 150);
    VERIFY(memcmp(record.manifest_sha256, digest, 32) == 0);
    OK(frg_payout_intent_held(txn, db, &held));
    VERIFY(held);
    mdb_txn_abort(txn);

    memset(id, 0xcc, 32); memset(digest, 0xdd, 32);
    total = UINT64_MAX;
    VERIFY(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        source, anchor, 150, recipients, 2, 12000,
        id, digest, &total) == EBUSY);
    VERIFY(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        next_source, anchor, 150, recipients, 2, 12000,
        id, digest, &total) == EBUSY);
    VERIFY(id[0] == 0xcc && digest[0] == 0xdd && total == UINT64_MAX);

    /* A real LMDB close/reopen must retain the hold before any transfer. */
    close_ledger(env, db);
    env = NULL;
    open_ledger(folder, 0, &env, &db);
    OK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    OK(frg_payout_intent_read(txn, db, expected_id, &record));
    VERIFY(record.state == FRG_PAYOUT_INTENT_PREPARED);
    mdb_txn_abort(txn);
    VERIFY(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        next_source, anchor, 150, recipients, 2, 12000,
        id, digest, &total) == EBUSY);

    /* Timeout/unknown-wallet outcome must preserve the immutable batch. */
    OK(mdb_txn_begin(env, NULL, 0, &txn));
    OK(frg_payout_intent_mark_ambiguous(txn, db, expected_id));
    OK(mdb_txn_commit(txn));
    VERIFY(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        next_source, anchor, 150, recipients, 2, 12000,
        id, digest, &total) == EBUSY);

    /* Wallet-reported txid is only a candidate, NOT a confirmed payment. */
    OK(mdb_txn_begin(env, NULL, 0, &txn));
    OK(frg_payout_intent_note_candidate(txn, db, expected_id, candidate));
    OK(mdb_txn_commit(txn));
    close_ledger(env, db);
    env = NULL;
    open_ledger(folder, 0, &env, &db);
    OK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    OK(frg_payout_intent_read(txn, db, expected_id, &record));
    VERIFY(record.state == FRG_PAYOUT_INTENT_CANDIDATE_UNVERIFIED);
    VERIFY(memcmp(record.candidate_txid, candidate, 32) == 0);
    mdb_txn_abort(txn);
    VERIFY(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        next_source, anchor, 150, recipients, 2, 12000,
        id, digest, &total) == EBUSY);

    /* A corrupt/malformed persisted journal cannot be treated as empty. */
    OK(mdb_txn_begin(env, NULL, 0, &txn));
    const uint8_t garbage[2] = {1, 2};
    MDB_val key = {32, expected_id}, val = {sizeof garbage, (void *)garbage};
    OK(mdb_put(txn, db, &key, &val, 0));
    OK(mdb_txn_commit(txn));
    VERIFY(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        next_source, anchor, 150, recipients, 2, 12000,
        id, digest, &total) == MDB_BAD_VALSIZE);
    VERIFY(id[0] == 0xcc && digest[0] == 0xdd && total == UINT64_MAX);

    close_ledger(env, db);
    cleanup_dir(folder);

    /* Lossy LMDB options must never become a pre-transfer safety proof. */
    char unsafe[] = "/tmp/frg-reservation-unsync-XXXXXX";
    VERIFY(mkdtemp(unsafe) != NULL);
    open_ledger(unsafe, MDB_NOSYNC, &env, &db);
    VERIFY(frg_payout_batch_reserve(env, db, FRG_PAYOUT_FROZEN_CHAIN_ID,
        source, anchor, 150, recipients, 2, 12000,
        id, digest, &total) == EACCES);
    close_ledger(env, db);
    cleanup_dir(unsafe);

    printf("PASS: %u native real-LMDB canonical payout reservation assertions; "
           "durable hold, no retries, no debits, no network\n", tests);
    return 0;
}
