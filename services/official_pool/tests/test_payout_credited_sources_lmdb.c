/* Real LMDB credited-source commitment and atomic offline reservation QA.
 * No wallet keys, daemon, network, transfers, balance debits or signing.
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

#include "../jtgrassie/src/frg_payout_credited_sources.h"

static unsigned checks;
#define VERIFY(value) do { ++checks; assert((value)); } while (0)
#define OK(expr) do { int rc_ = (expr); ++checks; if (rc_) { \
  fprintf(stderr, "LMDB %s at %d: %s\n", #expr, __LINE__, \
          mdb_strerror(rc_)); abort(); } } while (0)

static int cmp_height(const MDB_val *a, const MDB_val *b)
{
    uint64_t x = 0, y = 0;
    memcpy(&x, a->mv_data, sizeof x);
    memcpy(&y, b->mv_data, sizeof y);
    return (x > y) - (x < y);
}

static int cmp_record(const MDB_val *a, const MDB_val *b)
{
    frg_history_saved_t x = {0}, y = {0};
    memcpy(&x, a->mv_data, sizeof x);
    memcpy(&y, b->mv_data, sizeof y);
    return (x.timestamp > y.timestamp) - (x.timestamp < y.timestamp);
}

static void open_ledger(const char *dir, MDB_env **env,
                        MDB_dbi *blocks, MDB_dbi *intents)
{
    OK(mdb_env_create(env));
    OK(mdb_env_set_maxdbs(*env, 6));
    OK(mdb_env_set_mapsize(*env, 4 * 1024 * 1024));
    OK(mdb_env_open(*env, dir, 0, 0600));
    MDB_txn *txn = NULL;
    OK(mdb_txn_begin(*env, NULL, 0, &txn));
    OK(mdb_dbi_open(txn, "blocks", MDB_INTEGERKEY | MDB_DUPSORT |
                    MDB_DUPFIXED | MDB_CREATE, blocks));
    OK(mdb_set_compare(txn, *blocks, cmp_height));
    OK(mdb_set_dupsort(txn, *blocks, cmp_record));
    OK(frg_payout_intent_open(txn, intents));
    OK(mdb_txn_commit(txn));
}

static void close_ledger(MDB_env *env, MDB_dbi blocks, MDB_dbi intents)
{
    mdb_dbi_close(env, blocks);
    mdb_dbi_close(env, intents);
    mdb_env_close(env);
}

static frg_history_saved_t make_block(uint64_t height, uint32_t status,
                                      uint64_t reward, time_t timestamp)
{
    frg_history_saved_t b = {0};
    b.height = height;
    b.status = status;
    b.reward = reward;
    b.difficulty = 500000;
    b.timestamp = timestamp;
    memcpy(b.hash,
      "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",64);
    memcpy(b.prev_hash,
      "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",64);
    b.hash[2] = "0123456789abcdef"[height & 15];
    return b;
}

static void put_block(MDB_env *env, MDB_dbi db, frg_history_saved_t *b)
{
    MDB_txn *txn = NULL;
    OK(mdb_txn_begin(env, NULL, 0, &txn));
    MDB_val k = {sizeof b->height, &b->height};
    MDB_val v = {sizeof *b, b};
    OK(mdb_put(txn, db, &k, &v, 0));
    OK(mdb_txn_commit(txn));
}

static void delete_block(MDB_env *env, MDB_dbi db, frg_history_saved_t *b)
{
    MDB_txn *txn = NULL;
    MDB_cursor *cur = NULL;
    OK(mdb_txn_begin(env, NULL, 0, &txn));
    OK(mdb_cursor_open(txn, db, &cur));
    MDB_val k = {sizeof b->height, &b->height};
    MDB_val v = {sizeof *b, b};
    OK(mdb_cursor_get(cur, &k, &v, MDB_GET_BOTH));
    OK(mdb_cursor_del(cur, 0));
    mdb_cursor_close(cur);
    OK(mdb_txn_commit(txn));
}

static int fingerprint(MDB_env *env, MDB_dbi db, uint64_t tip,
                       uint8_t digest[32], uint64_t *sources,
                       uint64_t *reward)
{
    MDB_txn *txn = NULL;
    int rc = mdb_txn_begin(env, NULL, MDB_RDONLY, &txn);
    if (rc) return rc;
    rc = frg_payout_credited_sources_digest(
        txn, db, FRG_PAYOUT_FROZEN_CHAIN_ID, tip, digest, sources, reward);
    mdb_txn_abort(txn);
    return rc;
}

static void cleanup(const char *folder)
{
    char file[512];
    int n = snprintf(file, sizeof file, "%s/data.mdb", folder);
    VERIFY(n > 0 && (size_t)n < sizeof file);
    OK(unlink(file));
    n = snprintf(file, sizeof file, "%s/lock.mdb", folder);
    VERIFY(n > 0 && (size_t)n < sizeof file);
    OK(unlink(file));
    OK(rmdir(folder));
}

int main(void)
{
    char folder[] = "/tmp/frg-credited-payout-XXXXXX";
    VERIFY(mkdtemp(folder));
    MDB_env *env = NULL;
    MDB_dbi blocks = 0, intents = 0;
    open_ledger(folder, &env, &blocks, &intents);

    uint8_t digest[32] = {0}, digest2[32] = {0};
    uint64_t count = UINT64_MAX, rewards = UINT64_MAX;
    VERIFY(fingerprint(env, blocks, 180, digest, &count, &rewards) == ENODATA);
    VERIFY(count == UINT64_MAX && rewards == UINT64_MAX);

    frg_history_saved_t b110 = make_block(110, FRG_HISTORY_UNLOCKED,
                                         UINT64_C(2380000000), 1110);
    frg_history_saved_t b100 = make_block(100, FRG_HISTORY_UNLOCKED,
                                         UINT64_C(2390000000), 1100);
    frg_history_saved_t locked = make_block(160, FRG_HISTORY_LOCKED, 0, 1160);
    frg_history_saved_t orphan = make_block(110, FRG_HISTORY_ORPHANED, 0, 1111);
    put_block(env, blocks, &b110);
    put_block(env, blocks, &orphan);
    put_block(env, blocks, &locked);
    put_block(env, blocks, &b100);

    VERIFY(fingerprint(env, blocks, 169, digest, &count, &rewards) == EPROTO);
    VERIFY(count == UINT64_MAX && rewards == UINT64_MAX);
    OK(fingerprint(env, blocks, 170, digest, &count, &rewards));
    VERIFY(count == 2);
    VERIFY(rewards == UINT64_C(4770000000));
    uint64_t count2 = 0, rewards2 = 0;
    OK(fingerprint(env, blocks, 180, digest2, &count2, &rewards2));
    VERIFY(count2 == count && rewards2 == rewards);
    VERIFY(memcmp(digest, digest2, 32) == 0);
    /* The anchor height is NOT incorporated into source identity. */
    OK(fingerprint(env, blocks, 190, digest2, &count2, &rewards2));
    VERIFY(memcmp(digest, digest2, 32) == 0);

    /* A new locked/noncredited row does not change credited source ID. */
    frg_history_saved_t locked2 = make_block(165, FRG_HISTORY_LOCKED, 0, 1165);
    put_block(env, blocks, &locked2);
    OK(fingerprint(env, blocks, 180, digest2, &count2, &rewards2));
    VERIFY(memcmp(digest, digest2, 32) == 0);

    /* Duplicate unlocked heights MUST NOT be silently counted twice. */
    frg_history_saved_t duplicate = make_block(110, FRG_HISTORY_UNLOCKED,
                                                UINT64_C(2380000000), 1120);
    put_block(env, blocks, &duplicate);
    VERIFY(fingerprint(env, blocks, 180, digest2, &count2, &rewards2)
           == EPROTO);
    delete_block(env, blocks, &duplicate);

    /* Unknown status on ANY row (even skipped) fails closed. */
    frg_history_saved_t corrupt = make_block(161, 9, 0, 1161);
    put_block(env, blocks, &corrupt);
    VERIFY(fingerprint(env, blocks, 180, digest2, &count2, &rewards2)
           == EPROTO);
    delete_block(env, blocks, &corrupt);

    /* Source credit amount mutation changes the committed fingerprint. */
    delete_block(env, blocks, &b100);
    b100.reward += 1;
    put_block(env, blocks, &b100);
    OK(fingerprint(env, blocks, 180, digest2, &count2, &rewards2));
    VERIFY(memcmp(digest, digest2, 32) != 0);
    memcpy(digest, digest2, 32);

    char a[96], b[96];
    a[0] = '4'; memset(a + 1, 'A', 94); a[95] = 0;
    b[0] = '5'; memset(b + 1, 'B', 94); b[95] = 0;
    frg_payout_recipient_t recipients[2] = {
        {a, UINT64_C(100000000)}, {b, UINT64_C(200000000)}
    };
    const uint8_t anchor_hash[32] = {9};
    uint8_t batch_id[32] = {0}, manifest[32] = {0};
    uint8_t expected_id[32] = {0}, expected_manifest[32] = {0};
    uint64_t amount = 0, expected_amount = 0;

    /* Derive the expected manifest from the independently scanned LMDB. */
    OK(frg_payout_manifest_hash(FRG_PAYOUT_FROZEN_CHAIN_ID,
        digest, anchor_hash, 180, recipients, 2, 12000,
        expected_id, expected_manifest, &expected_amount));

    OK(frg_payout_batch_reserve_from_credited_lmdb(
        env, blocks, intents, FRG_PAYOUT_FROZEN_CHAIN_ID,
        anchor_hash, 180, recipients, 2, 12000,
        batch_id, manifest, &amount));
    VERIFY(amount == expected_amount && amount == 300000000);
    VERIFY(memcmp(batch_id, expected_id, 32) == 0);
    VERIFY(memcmp(manifest, expected_manifest, 32) == 0);

    MDB_txn *txn = NULL;
    OK(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn));
    frg_payout_intent_record_t record;
    OK(frg_payout_intent_read(txn, intents, batch_id, &record));
    VERIFY(record.state == FRG_PAYOUT_INTENT_PREPARED);
    VERIFY(record.anchor_height == 180);
    VERIFY(record.amount_atomic == 300000000);
    VERIFY(memcmp(record.manifest_sha256, manifest, 32) == 0);
    mdb_txn_abort(txn);

    memset(batch_id, 0xaa, 32);
    memset(manifest, 0xbb, 32);
    amount = UINT64_MAX;
    VERIFY(frg_payout_batch_reserve_from_credited_lmdb(
        env, blocks, intents, FRG_PAYOUT_FROZEN_CHAIN_ID,
        anchor_hash, 180, recipients, 2, 12000,
        batch_id, manifest, &amount) == EBUSY);
    VERIFY(batch_id[0] == 0xaa && manifest[0] == 0xbb &&
           amount == UINT64_MAX);

    close_ledger(env, blocks, intents);
    open_ledger(folder, &env, &blocks, &intents);
    VERIFY(frg_payout_batch_reserve_from_credited_lmdb(
        env, blocks, intents, FRG_PAYOUT_FROZEN_CHAIN_ID,
        anchor_hash, 180, recipients, 2, 12000,
        batch_id, manifest, &amount) == EBUSY);
    OK(mdb_txn_begin(env, NULL, 0, &txn));
    OK(frg_payout_intent_mark_ambiguous(txn, intents, expected_id));
    OK(mdb_txn_commit(txn));
    VERIFY(frg_payout_batch_reserve_from_credited_lmdb(
        env, blocks, intents, FRG_PAYOUT_FROZEN_CHAIN_ID,
        anchor_hash, 180, recipients, 2, 12000,
        batch_id, manifest, &amount) == EBUSY);
    close_ledger(env, blocks, intents);
    cleanup(folder);

    printf("PASS: %u native credited LMDB source-digest/atomic-reservation "
           "assertions; no wallet or payout enabled\n", checks);
    return 0;
}
