/* Disposable real-LMDB credited-block history scanner regression.
 * NO daemon, wallet, mining or payout interaction.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <lmdb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "../jtgrassie/src/frg_credited_ledger_scan.h"

#define CHECK(expr) do { int rc_=(expr); if (rc_) { \
    fprintf(stderr,"%s: %s\n", #expr,mdb_strerror(rc_)); abort(); } } while (0)

static int cmp_height(const MDB_val *a, const MDB_val *b)
{
    uint64_t x = 0, y = 0;
    memcpy(&x,a->mv_data,sizeof(x));
    memcpy(&y,b->mv_data,sizeof(y));
    return x < y ? -1 : x > y;
}
static int cmp_record(const MDB_val *a, const MDB_val *b)
{
    frg_history_saved_t x = {0}, y = {0};
    memcpy(&x,a->mv_data,sizeof(x));
    memcpy(&y,b->mv_data,sizeof(y));
    return x.timestamp < y.timestamp ? -1 : 1;
}
static frg_history_saved_t make_block(uint64_t height, uint32_t status, time_t ts)
{
    frg_history_saved_t b = {0};
    b.height = height;
    memcpy(b.hash, "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789", 64);
    memcpy(b.prev_hash, "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", 64);
    b.difficulty = 500000;
    b.reward = status == FRG_HISTORY_UNLOCKED ? 2384185222ULL : 0;
    b.status = status;
    b.timestamp = ts;
    return b;
}
static void insert(MDB_env *env, MDB_dbi db, frg_history_saved_t *block)
{
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(env,NULL,0,&txn));
    MDB_val key = {sizeof(block->height),&block->height};
    MDB_val value = {sizeof(*block),block};
    CHECK(mdb_put(txn,db,&key,&value,0));
    CHECK(mdb_txn_commit(txn));
}
static void check_selection(MDB_env *env, MDB_dbi db, uint64_t index,
                            bool expected_found, uint64_t expected_total,
                            uint64_t expected_height)
{
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(env,NULL,MDB_RDONLY,&txn));
    frg_history_saved_t record = {0};
    bool found = false;
    uint64_t total = UINT64_MAX;
    CHECK(frg_history_scan_credited(txn,db,index,&record,&found,&total));
    assert(found == expected_found);
    assert(total == expected_total);
    if (found) assert(record.height == expected_height);
    mdb_txn_abort(txn);
}
int main(void)
{
    char dir[] = "/tmp/frg-credited-history-XXXXXX";
    assert(mkdtemp(dir));
    MDB_env *env = NULL;
    MDB_dbi db = 0;
    CHECK(mdb_env_create(&env));
    CHECK(mdb_env_set_maxdbs(env,4));
    CHECK(mdb_env_set_mapsize(env,2*1024*1024));
    CHECK(mdb_env_open(env,dir,0,0600));
    MDB_txn *txn = NULL;
    CHECK(mdb_txn_begin(env,NULL,0,&txn));
    CHECK(mdb_dbi_open(txn,"blocks",MDB_INTEGERKEY|MDB_DUPSORT|MDB_DUPFIXED|MDB_CREATE,&db));
    CHECK(mdb_set_compare(txn,db,cmp_height));
    CHECK(mdb_set_dupsort(txn,db,cmp_record));
    CHECK(mdb_txn_commit(txn));
    check_selection(env,db,0,false,0,0);
    frg_history_saved_t r = make_block(100,FRG_HISTORY_LOCKED,1001);
    insert(env,db,&r);
    r = make_block(100,FRG_HISTORY_UNLOCKED,1002); insert(env,db,&r);
    r = make_block(100,FRG_HISTORY_ORPHANED,1003); insert(env,db,&r);
    r = make_block(101,FRG_HISTORY_UNLOCKED,1004); insert(env,db,&r);
    r = make_block(102,FRG_HISTORY_UNLOCKED,1005); insert(env,db,&r);
    check_selection(env,db,0,true,3,100);
    check_selection(env,db,1,true,3,101);
    check_selection(env,db,2,true,3,102);
    check_selection(env,db,3,false,3,0);

    /* Reopen read transaction: no 'verified' scan state survives restart. */
    mdb_dbi_close(env,db);
    mdb_env_close(env);
    env = NULL;
    CHECK(mdb_env_create(&env));
    CHECK(mdb_env_set_maxdbs(env,4));
    CHECK(mdb_env_open(env,dir,0,0600));
    CHECK(mdb_txn_begin(env,NULL,0,&txn));
    CHECK(mdb_dbi_open(txn,"blocks",0,&db));
    CHECK(mdb_set_compare(txn,db,cmp_height));
    CHECK(mdb_set_dupsort(txn,db,cmp_record));
    CHECK(mdb_txn_commit(txn));
    check_selection(env,db,1,true,3,101);

    /* Bad status is not silently skipped, even at a candidate height. */
    r = make_block(103,9,1006); insert(env,db,&r);
    CHECK(mdb_txn_begin(env,NULL,MDB_RDONLY,&txn));
    frg_history_saved_t selected = {0};
    bool found = false;
    uint64_t total = 0;
    assert(frg_history_scan_credited(txn,db,0,&selected,&found,&total) == EPROTO);
    mdb_txn_abort(txn);
    mdb_dbi_close(env,db);
    mdb_env_close(env);

    char filename[512];
    snprintf(filename,sizeof filename,"%s/data.mdb",dir); CHECK(unlink(filename));
    snprintf(filename,sizeof filename,"%s/lock.mdb",dir); CHECK(unlink(filename));
    CHECK(rmdir(dir));
    puts("PASS: credited LMDB scan covers duplicate heights, noncredited records, restart and corrupt status");
    return 0;
}
