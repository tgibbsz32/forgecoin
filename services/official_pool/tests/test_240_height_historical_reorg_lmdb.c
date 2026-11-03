/* Disposable native 240-height / 120-credited-block reorg acceptance replay.
 *
 * Uses the exact real pool LMDB candidate scanner, strict daemon RPC-envelope
 * validator, payout safety gate and persistent quarantine function. Synthetic
 * headers are NOT mined/PoW-validated, and no pool/daemon/wallet is started.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <inttypes.h>
#include <json-c/json.h>
#include <lmdb.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "../jtgrassie/src/frg_credited_ledger_scan.h"
#include "../jtgrassie/src/frg_accounting_quarantine.h"
#include "../jtgrassie/src/frg_currency.h"
#include "../jtgrassie/src/frg_reconcile_policy.h"

#define CHECK(x) do { int rc_ = (x); if (rc_) { \
    fprintf(stderr, "LMDB %s: %s\n", #x, mdb_strerror(rc_)); abort(); } } while (0)

#define TEST_TIP UINT64_C(240)
#define CREDITED_COUNT UINT64_C(120)
#define FORK_HEIGHT UINT64_C(100)
#define BLOCK_REWARD UINT64_C(100000000)
#define BLOCK_DIFFICULTY UINT64_C(500000)

typedef struct ledger {
    MDB_env *env;
    MDB_dbi blocks, properties, balances;
} ledger;

static int compare_height(const MDB_val *a, const MDB_val *b)
{
    uint64_t aa = 0, bb = 0;
    assert(a->mv_size == sizeof(aa) && b->mv_size == sizeof(bb));
    memcpy(&aa, a->mv_data, sizeof(aa));
    memcpy(&bb, b->mv_data, sizeof(bb));
    return aa < bb ? -1 : aa > bb;
}
static int compare_block_time(const MDB_val *a, const MDB_val *b)
{
    frg_history_saved_t aa = {0}, bb = {0};
    assert(a->mv_size == sizeof(aa) && b->mv_size == sizeof(bb));
    memcpy(&aa, a->mv_data, sizeof(aa));
    memcpy(&bb, b->mv_data, sizeof(bb));
    return aa.timestamp < bb.timestamp ? -1 : 1;
}
static MDB_val string_key(const char *name)
{
    MDB_val v = {strlen(name), (void *)name};
    return v;
}
static void ledger_open(const char *path, ledger *l)
{
    memset(l, 0, sizeof(*l));
    CHECK(mdb_env_create(&l->env));
    CHECK(mdb_env_set_maxdbs(l->env, 8));
    CHECK(mdb_env_set_mapsize(l->env, 8 * 1024 * 1024));
    CHECK(mdb_env_open(l->env, path, 0, 0600));
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(l->env, NULL, 0, &txn));
    CHECK(mdb_dbi_open(txn, "blocks", MDB_INTEGERKEY|MDB_DUPSORT|MDB_DUPFIXED|MDB_CREATE,
                       &l->blocks));
    CHECK(mdb_set_compare(txn, l->blocks, compare_height));
    CHECK(mdb_set_dupsort(txn, l->blocks, compare_block_time));
    CHECK(mdb_dbi_open(txn, "properties", MDB_CREATE, &l->properties));
    CHECK(mdb_dbi_open(txn, "balance", MDB_CREATE, &l->balances));
    CHECK(mdb_txn_commit(txn));
}
static void ledger_close(ledger *l)
{
    mdb_dbi_close(l->env, l->blocks);
    mdb_dbi_close(l->env, l->properties);
    mdb_dbi_close(l->env, l->balances);
    mdb_env_close(l->env);
    memset(l, 0, sizeof(*l));
}
static void to_hash(uint64_t height, bool new_fork, char raw[64])
{
    char text[65] = {0};
    const uint64_t x = (new_fork ? UINT64_C(1000000) : UINT64_C(1000)) + height;
    assert(snprintf(text, sizeof(text), "%064" PRIx64, x) == 64);
    memcpy(raw, text, 64);
}
static void printable(const char raw[64], char text[65])
{
    memcpy(text, raw, 64);
    text[64] = '\0';
}
static frg_history_saved_t make_block(uint64_t height, uint32_t status,
                                     time_t serial, bool new_fork)
{
    frg_history_saved_t block = {0};
    block.height = height;
    block.status = status;
    block.reward = status == FRG_HISTORY_UNLOCKED ? BLOCK_REWARD : 0;
    block.difficulty = BLOCK_DIFFICULTY;
    block.timestamp = serial;
    to_hash(height, new_fork, block.hash);
    to_hash(height ? height-1 : 0, new_fork && height > FORK_HEIGHT, block.prev_hash);
    return block;
}
static void put_balance(MDB_txn *txn, MDB_dbi db, const char *name, uint64_t value)
{
    MDB_val key = string_key(name), val = {sizeof(value), &value};
    CHECK(mdb_put(txn, db, &key, &val, 0));
}
static uint64_t get_balance(ledger *l, const char *name)
{
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(l->env, NULL, MDB_RDONLY, &txn));
    MDB_val key = string_key(name), val = {0, NULL};
    int rc = mdb_get(txn, l->balances, &key, &val);
    assert(rc == 0 && val.mv_size == sizeof(uint64_t));
    uint64_t amount = 0;
    memcpy(&amount, val.mv_data, sizeof(amount));
    mdb_txn_abort(txn);
    return amount;
}
static void put_record(MDB_txn *txn, MDB_dbi db, frg_history_saved_t *block)
{
    MDB_val key = {sizeof(block->height), &block->height};
    MDB_val val = {sizeof(*block), block};
    CHECK(mdb_put(txn, db, &key, &val, 0));
}
static void populate_mature_ledger(ledger *l)
{
    const uint64_t fee = frg_pool_fee_atomic(BLOCK_REWARD);
    assert(fee == UINT64_C(1000000));
    uint64_t miners = 0, fees = 0;
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(l->env, NULL, 0, &txn));
    for (uint64_t h = 1; h <= CREDITED_COUNT; ++h)
    {
        assert(frg_reward_mature(h, TEST_TIP));
        assert(frg_reconcile_block(FRG_SAVED_LOCKED, h, h, TEST_TIP,
                                   true, true, false) == FRG_RECONCILE_CREDIT);
        frg_history_saved_t block = make_block(h, FRG_HISTORY_UNLOCKED,
                                               (time_t)(1700000000 + h), false);
        put_record(txn, l->blocks, &block);
        miners += BLOCK_REWARD - fee;
        fees += fee;
    }
    /* Same-height duplicate records are permitted in the actual native DB,
     * but only the previously credited one is eligible for historical audit.
     */
    frg_history_saved_t orphan = make_block(75, FRG_HISTORY_ORPHANED, 1700003000, true);
    frg_history_saved_t locked = make_block(160, FRG_HISTORY_LOCKED, 1700003010, false);
    put_record(txn, l->blocks, &orphan);
    put_record(txn, l->blocks, &locked);
    put_balance(txn, l->balances, "miner", miners);
    put_balance(txn, l->balances, "fee", fees);
    CHECK(mdb_txn_commit(txn));
    assert(miners == CREDITED_COUNT * UINT64_C(99000000));
    assert(fees == CREDITED_COUNT * UINT64_C(1000000));
}
static frg_history_saved_t saved_at(ledger *l, uint64_t index, uint64_t count)
{
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(l->env, NULL, MDB_RDONLY, &txn));
    frg_history_saved_t selected = {0};
    bool found = false;
    uint64_t seen = 0;
    CHECK(frg_history_scan_credited(txn, l->blocks, index, &selected, &found, &seen));
    mdb_txn_abort(txn);
    assert(found && seen == count);
    return selected;
}
static char *rpc_reply(const frg_history_saved_t *record, bool rewrite,
                       bool wrong_height, bool rpc_error, bool bad_status)
{
    struct json_object *root = json_object_new_object();
    assert(root);
    if (rpc_error)
    {
        struct json_object *err = json_object_new_object();
        json_object_object_add(err, "code", json_object_new_int(-1));
        json_object_object_add(root, "error", err);
    }
    else json_object_object_add(root, "error", NULL); /* json-c JSON null */
    struct json_object *result = json_object_new_object();
    json_object_object_add(result, "status", json_object_new_string(
        bad_status ? "BUSY" : "OK"));
    struct json_object *header = json_object_new_object();
    const bool branched = rewrite && record->height >= FORK_HEIGHT;
    frg_history_saved_t canonical = make_block(record->height,
                                               FRG_HISTORY_UNLOCKED,
                                               record->timestamp, branched);
    char hash[65], parent[65];
    printable(canonical.hash, hash);
    printable(canonical.prev_hash, parent);
    json_object_object_add(header, "height", json_object_new_int64(
        (int64_t)(record->height + (wrong_height ? 1u : 0u))));
    json_object_object_add(header, "difficulty", json_object_new_int64(BLOCK_DIFFICULTY));
    json_object_object_add(header, "reward", json_object_new_int64(BLOCK_REWARD));
    json_object_object_add(header, "timestamp", json_object_new_int64(canonical.timestamp));
    json_object_object_add(header, "hash", json_object_new_string(hash));
    json_object_object_add(header, "prev_hash", json_object_new_string(parent));
    json_object_object_add(header, "orphan_status", json_object_new_boolean(0));
    json_object_object_add(result, "block_header", header);
    json_object_object_add(root, "result", result);
    const char *rendered = json_object_to_json_string_ext(root, JSON_C_TO_STRING_PLAIN);
    assert(rendered);
    char *out = strdup(rendered);
    assert(out);
    json_object_put(root);
    return out;
}
static enum frg_history_verdict
evaluate(const frg_history_saved_t *stored, const char *reply)
{
    return frg_history_evaluate_rpc(reply, stored->height,
                                    stored->hash, stored->prev_hash,
                                    stored->difficulty, stored->reward);
}
static void held_state(ledger *l, bool should_hold, uint64_t first_height)
{
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(l->env, NULL, MDB_RDONLY, &txn));
    bool held = !should_hold;
    uint64_t h = UINT64_MAX;
    CHECK(frg_quarantine_read(txn, l->properties, &held, &h));
    assert(held == should_hold && h == first_height);
    mdb_txn_abort(txn);
}
static void assert_balances_unchanged(ledger *l)
{
    assert(get_balance(l, "miner") == CREDITED_COUNT * UINT64_C(99000000));
    assert(get_balance(l, "fee") == CREDITED_COUNT * UINT64_C(1000000));
}
static void clean_sweep(ledger *l, uint64_t count)
{
    bool verified = false;
    assert(!frg_history_payout_allowed(false, verified, false));
    for (uint64_t index = 0; index < count; ++index)
    {
        const frg_history_saved_t record = saved_at(l, index, count);
        char *reply = rpc_reply(&record, false, false, false, false);
        assert(!frg_history_payout_allowed(false, verified, true));
        assert(evaluate(&record, reply) == FRG_HISTORY_MATCH);
        free(reply);
    }
    verified = true;
    assert(frg_history_payout_allowed(false, verified, false));
}
int main(void)
{
    char dir[] = "/tmp/frg-240-height-reorg-XXXXXX";
    assert(mkdtemp(dir));
    ledger l;
    ledger_open(dir, &l);
    populate_mature_ledger(&l);
    held_state(&l, false, 0);
    assert_balances_unchanged(&l);
    clean_sweep(&l, CREDITED_COUNT);

    /* Wrong-height and failed-RPC replies must HOLD payout eligibility but
     * must not falsely persist a canonical reorganization incident.
     */
    const frg_history_saved_t sample = saved_at(&l, 80, CREDITED_COUNT);
    char *reply = rpc_reply(&sample, false, true, false, false);
    assert(evaluate(&sample, reply) == FRG_HISTORY_UNVERIFIED);
    free(reply);
    reply = rpc_reply(&sample, false, false, true, false);
    assert(evaluate(&sample, reply) == FRG_HISTORY_UNVERIFIED);
    free(reply);
    reply = rpc_reply(&sample, false, false, false, true);
    assert(evaluate(&sample, reply) == FRG_HISTORY_UNVERIFIED);
    free(reply);
    assert(evaluate(&sample, "{bad json") == FRG_HISTORY_UNVERIFIED);
    assert(evaluate(&sample, NULL) == FRG_HISTORY_UNVERIFIED);
    held_state(&l, false, 0);
    assert(!frg_history_payout_allowed(false, false, true));

    /* Simulate process restart before any fork. The C pool resets its volatile
     * verified flag; a fresh full sweep is mandatory before wallet eligibility.
     */
    ledger_close(&l);
    ledger_open(dir, &l);
    assert(!frg_history_payout_allowed(false, false, false));
    clean_sweep(&l, CREDITED_COUNT);

    /* Tip 240, fork starts at credited height 100: a 141-block rewrite
     * relative to that credited block; far beyond the 10-block RPC window.
     * Old credited entries remain untouched until the historical audit
     * reaches them.
     */
    assert(TEST_TIP - FORK_HEIGHT + 1 >= 61);
    uint64_t conflict_height = 0;
    for (uint64_t i = 0; i < CREDITED_COUNT; ++i)
    {
        const frg_history_saved_t record = saved_at(&l, i, CREDITED_COUNT);
        reply = rpc_reply(&record, true, false, false, false);
        const enum frg_history_verdict verdict = evaluate(&record, reply);
        free(reply);
        if (verdict == FRG_HISTORY_CONFLICT)
        {
            conflict_height = record.height;
            assert(conflict_height == FORK_HEIGHT);
            CHECK(frg_quarantine_mark(l.env, l.properties, conflict_height));
            break;
        }
        assert(verdict == FRG_HISTORY_MATCH);
    }
    assert(conflict_height == FORK_HEIGHT);
    held_state(&l, true, FORK_HEIGHT);
    assert(!frg_history_payout_allowed(true, true, false));
    assert_balances_unchanged(&l);

    /* First incident wins even after further late historical conflicts. */
    CHECK(frg_quarantine_mark(l.env, l.properties, FORK_HEIGHT+9));
    held_state(&l, true, FORK_HEIGHT);

    ledger_close(&l);
    ledger_open(dir, &l);
    held_state(&l, true, FORK_HEIGHT);
    assert(!frg_history_payout_allowed(true, true, false));
    assert_balances_unchanged(&l);

    /* No automatic reconciliation, reset, balance debit or wallet payout. */
    ledger_close(&l);
    char path[512];
    assert(snprintf(path,sizeof path,"%s/data.mdb",dir)>0);
    CHECK(unlink(path));
    assert(snprintf(path,sizeof path,"%s/lock.mdb",dir)>0);
    CHECK(unlink(path));
    CHECK(rmdir(dir));
    puts("PASS: 240-height synthetic chain, 120 credited blocks, 141-deep reorg,"
         " real LMDB history scan, strict JSON-RPC, durable restart quarantine,"
         " 1% fee unchanged, wallet payout gate held");
    return 0;
}
