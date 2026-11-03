/* Independent read-only LMDB verification for disposable real C-pool tests.
 * This deliberately uses the same on-disk structs as the production scanner,
 * but has no linkage to the live pool process and can never write balances.
 *
 * frg-pool-ledger-audit ROOT locked|credited|held HEIGHT HASH64 PARENT64
 *                      MINER_PUBLIC_ADDRESS FEE_PUBLIC_ADDRESS
 */
#define _GNU_SOURCE
#include <inttypes.h>
#include <lmdb.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../jtgrassie/src/frg_credited_ledger_scan.h"
#include "../jtgrassie/src/frg_accounting_quarantine.h"
#include "../jtgrassie/src/frg_currency.h"

#define ADDRESS_MAX 128

static void require(int good, const char *why)
{
    if (!good) { fprintf(stderr, "FAIL: %s\n", why); exit(2); }
}
static uint64_t read_balance(MDB_txn *txn, MDB_dbi balances, const char *address)
{
    char key_buf[ADDRESS_MAX] = {0};
    require(strlen(address) >= 90 && strlen(address) < ADDRESS_MAX,
            "invalid public balance address");
    memcpy(key_buf, address, strlen(address));
    MDB_val key = {ADDRESS_MAX, key_buf}, value = {0, NULL};
    int rc = mdb_get(txn, balances, &key, &value);
    require(rc == 0 && value.mv_size == sizeof(uint64_t), "balance missing or malformed");
    uint64_t atomic = 0;
    memcpy(&atomic, value.mv_data, sizeof(atomic));
    return atomic;
}
int main(int argc, char **argv)
{
    require(argc == 8, "expected ROOT MODE HEIGHT HASH PARENT MINER FEE");
    const char *mode = argv[2];
    require(!strcmp(mode, "locked") || !strcmp(mode, "credited") ||
            !strcmp(mode, "held"), "unsupported audit mode");
    char *end = NULL;
    const unsigned long long height_ull = strtoull(argv[3], &end, 10);
    require(end && *end == '\0' && height_ull > 0, "invalid expected height");
    const uint64_t height = (uint64_t)height_ull;
    require(strlen(argv[4]) == 64 && strlen(argv[5]) == 64,
            "expected chain hashes must be 64 hex bytes");
    require(frg_fixed_hash64(argv[4]) && frg_fixed_hash64(argv[5]),
            "expected chain hashes not hexadecimal");

    MDB_env *env = NULL;
    MDB_txn *txn = NULL;
    MDB_dbi blocks = 0, balances = 0, properties = 0;
    require(mdb_env_create(&env) == 0, "mdb_env_create failed");
    require(mdb_env_set_maxdbs(env, 8) == 0, "maxdbs failed");
    require(mdb_env_open(env, argv[1], MDB_RDONLY | MDB_NOTLS, 0600) == 0,
            "pool LMDB missing or unreadable");
    require(mdb_txn_begin(env, NULL, MDB_RDONLY, &txn) == 0,
            "read-only LMDB transaction failed");
    require(mdb_dbi_open(txn, "blocks", 0, &blocks) == 0,
            "native pool blocks DB missing");
    require(mdb_dbi_open(txn, "properties", 0, &properties) == 0,
            "native pool properties DB missing");
    bool held = false;
    uint64_t first_held = UINT64_MAX;
    require(frg_quarantine_read(txn, properties, &held, &first_held) == 0,
            "quarantine unreadable");
    require(held == (!strcmp(mode, "held")), "persistent quarantine does not match expected");
    if (held) require(first_held == height, "quarantine marked the wrong block height");

    MDB_cursor *cursor = NULL;
    require(mdb_cursor_open(txn, blocks, &cursor) == 0, "block cursor missing");
    MDB_val key = {sizeof(height), (void*)&height}, value = {0, NULL};
    int rc = mdb_cursor_get(cursor, &key, &value, MDB_SET);
    bool found = false;
    frg_history_saved_t record = {0};
    while (rc == 0)
    {
        require(key.mv_size == sizeof(height) &&
                value.mv_size == sizeof(record), "invalid pool block record layout");
        memcpy(&record, value.mv_data, sizeof(record));
        if (record.height == height &&
            !memcmp(record.hash, argv[4], 64) &&
            !memcmp(record.prev_hash, argv[5], 64))
        {
            found = true;
            break;
        }
        rc = mdb_cursor_get(cursor, &key, &value, MDB_NEXT_DUP);
    }
    require(found, "expected native pool block hash absent from durable LMDB");
    mdb_cursor_close(cursor);
    require(record.difficulty > 0, "invalid recorded native block difficulty");

    if (!strcmp(mode, "locked"))
    {
        require(record.status == FRG_HISTORY_LOCKED,
                "unmatured pool block unexpectedly unlocked or orphaned");
        puts("PASS: actual native pool-mined block durably LMDB-locked; payouts unverified");
    }
    else
    {
        require(record.status == FRG_HISTORY_UNLOCKED,
                "matured pool block not durably marked credited");
        require(record.reward > 0, "credited block reward missing");
        require(mdb_dbi_open(txn, "balance", 0, &balances) == 0,
                "native pool balance DB missing");
        uint64_t fee = frg_pool_fee_atomic(record.reward);
        uint64_t miner = record.reward - fee;
        const uint64_t got_miner = read_balance(txn, balances, argv[6]);
        const uint64_t got_fee = read_balance(txn, balances, argv[7]);
        require(got_miner == miner && got_fee == fee,
                "1% operator split does not exactly reconcile in atomic units");
        require(miner + fee == record.reward,
                "pool atomic balances do not account for exactly one reward");
        if (!strcmp(mode, "credited"))
            printf("PASS: live native LMDB credited block at height %" PRIu64
                   ", reward=%" PRIu64 ", miner=%" PRIu64 ", operator 1%%=%" PRIu64
                   ", no payout signer\n", height, record.reward, miner, fee);
        else
            printf("PASS: deep reorg LMDB quarantine persists at height %" PRIu64
                   " with frozen miner=%" PRIu64 ", operator=%" PRIu64 "\n",
                   height, miner, fee);
    }
    mdb_txn_abort(txn);
    mdb_env_close(env);
    return 0;
}
