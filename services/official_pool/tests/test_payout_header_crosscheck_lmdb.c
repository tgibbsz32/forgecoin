/* Two-observer canonical-header fixture, real disposable LMDB.
 * Neither observer is actually network-authenticated in this offline test.
 * NO daemon, wallet, signing, public Stratum, payout or mainnet activation.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <json-c/json.h>
#include <lmdb.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "../jtgrassie/src/frg_payout_header_crosscheck.h"

static unsigned checks = 0;
#define VERIFY(x) do { ++checks; assert(x); } while (0)
#define OK(x) do { int rc_ = (x); ++checks; if(rc_) { \
  fprintf(stderr,"LMDB code %d line %d\n",rc_,__LINE__);abort(); \
} } while(0)

static int cmp_height(const MDB_val *a, const MDB_val *b)
{
    uint64_t x = 0, y = 0;
    memcpy(&x, a->mv_data, 8);
    memcpy(&y, b->mv_data, 8);
    return (x > y) - (x < y);
}
static int cmp_block(const MDB_val *a, const MDB_val *b)
{
    frg_history_saved_t x = {0}, y = {0};
    memcpy(&x, a->mv_data, sizeof x);
    memcpy(&y, b->mv_data, sizeof y);
    return (x.timestamp > y.timestamp) - (x.timestamp < y.timestamp);
}
static void open_db(const char *dir, MDB_env **env, MDB_dbi *blocks)
{
    OK(mdb_env_create(env));
    OK(mdb_env_set_maxdbs(*env, 4));
    OK(mdb_env_set_mapsize(*env, 2 * 1024 * 1024));
    OK(mdb_env_open(*env, dir, 0, 0600));
    MDB_txn *txn = NULL;
    OK(mdb_txn_begin(*env, NULL, 0, &txn));
    OK(mdb_dbi_open(txn, "blocks",
        MDB_INTEGERKEY | MDB_DUPSORT | MDB_DUPFIXED | MDB_CREATE, blocks));
    OK(mdb_set_compare(txn, *blocks, cmp_height));
    OK(mdb_set_dupsort(txn, *blocks, cmp_block));
    OK(mdb_txn_commit(txn));
}
static frg_history_saved_t block(uint64_t height, uint32_t status,
                                  uint64_t reward, time_t ts)
{
    frg_history_saved_t b = {0};
    b.height = height;
    b.difficulty = 500000;
    b.reward = reward;
    b.status = status;
    b.timestamp = ts;
    memcpy(b.hash,
       "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",64);
    memcpy(b.prev_hash,
       "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",64);
    b.hash[0] = "0123456789abcdef"[height & 15];
    return b;
}
static void insert(MDB_env *env, MDB_dbi db, frg_history_saved_t *b)
{
    MDB_txn *txn = NULL;
    OK(mdb_txn_begin(env, NULL, 0, &txn));
    MDB_val k = {sizeof b->height, &b->height};
    MDB_val v = {sizeof *b, b};
    OK(mdb_put(txn, db, &k, &v, 0));
    OK(mdb_txn_commit(txn));
}
static json_object *header(const frg_history_saved_t *b)
{
    json_object *h = json_object_new_object();
    VERIFY(h != NULL);
    char hex[65], parent[65];
    memcpy(hex, b->hash, 64); hex[64] = 0;
    memcpy(parent, b->prev_hash, 64); parent[64] = 0;
    json_object_object_add(h,"height",json_object_new_int64(b->height));
    json_object_object_add(h,"difficulty",json_object_new_int64(b->difficulty));
    json_object_object_add(h,"reward",json_object_new_int64(b->reward));
    json_object_object_add(h,"timestamp",json_object_new_int64(b->timestamp));
    json_object_object_add(h,"hash",json_object_new_string(hex));
    json_object_object_add(h,"prev_hash",json_object_new_string(parent));
    json_object_object_add(h,"orphan_status",json_object_new_boolean(0));
    return h;
}
static json_object *snapshot(const frg_history_saved_t *tip,
                              const frg_history_saved_t *a,
                              const frg_history_saved_t *b)
{
    json_object *o = json_object_new_object();
    VERIFY(o != NULL);
    json_object_object_add(o, "anchor", header(tip));
    json_object *items = json_object_new_array();
    VERIFY(items != NULL);
    json_object_array_add(items,header(a));
    json_object_array_add(items,header(b));
    json_object_object_add(o, "credits", items);
    return o;
}
static int verify(MDB_env *env, MDB_dbi db, uint64_t tip,
                  const uint8_t expected_tip[32], json_object *a,
                  json_object *b, uint8_t digest[32],
                  uint64_t *count, uint64_t *total)
{
    MDB_txn *txn = NULL;
    int rc = mdb_txn_begin(env, NULL, MDB_RDONLY, &txn);
    if (rc) return rc;
    rc = frg_payout_credited_headers_crosscheck(txn, db,
        FRG_PAYOUT_FROZEN_CHAIN_ID, tip, expected_tip, a, b,
        digest, count, total);
    mdb_txn_abort(txn);
    return rc;
}

int main(void)
{
    char dir[] = "/tmp/frg-two-observer-XXXXXX";
    VERIFY(mkdtemp(dir) != NULL);
    MDB_env *env = NULL;
    MDB_dbi db;
    open_db(dir, &env, &db);
    frg_history_saved_t a = block(100, FRG_HISTORY_UNLOCKED, 100000000, 1010);
    frg_history_saved_t b = block(120, FRG_HISTORY_UNLOCKED, 200000000, 1020);
    frg_history_saved_t locked = block(150, FRG_HISTORY_LOCKED, 0, 1030);
    frg_history_saved_t orphan = block(120, FRG_HISTORY_ORPHANED, 0, 1040);
    insert(env,db,&a);
    insert(env,db,&b);
    insert(env,db,&locked);
    insert(env,db,&orphan);

    frg_history_saved_t tip = block(200, FRG_HISTORY_LOCKED, 0, 2000);
    uint8_t tip_hash[32] = {0};
    VERIFY(frg_source_hash_bytes(tip.hash, tip_hash));
    VERIFY(frg_payout_bytes_nonzero(tip_hash, 32));
    json_object *one = snapshot(&tip, &a, &b);
    json_object *two = snapshot(&tip, &a, &b);
    uint8_t digest[32] = {0};
    uint64_t count = 0, reward = 0;
    OK(verify(env,db,200,tip_hash,one,two,digest,&count,&reward));
    VERIFY(frg_payout_bytes_nonzero(digest,32));
    VERIFY(count == 2 && reward == 300000000);

    /* Every unsuccessful observation must leave outputs unchanged. */
    uint8_t hold[32]; memcpy(hold,digest,32);
    uint64_t prev_count = count, prev_reward = reward;
    VERIFY(verify(env,db,200,tip_hash,one,one,digest,&count,&reward)
           == EINVAL);
    VERIFY(memcmp(hold,digest,32)==0 && count==prev_count &&
           reward==prev_reward);

    json_object *headers = NULL;
    VERIFY(json_object_object_get_ex(two,"credits",&headers));
    json_object *h = json_object_array_get_idx(headers,0);
    json_object_object_add(h,"hash",json_object_new_string(
       "0000000000000000000000000000000000000000000000000000000000000001"));
    VERIFY(verify(env,db,200,tip_hash,one,two,digest,&count,&reward)
           == EAGAIN);
    json_object_put(two);
    two = snapshot(&tip,&a,&b);

    VERIFY(json_object_object_get_ex(two,"credits",&headers));
    h = json_object_array_get_idx(headers,1);
    json_object_object_add(h,"height",json_object_new_int64(119));
    VERIFY(verify(env,db,200,tip_hash,one,two,digest,&count,&reward)
           == EAGAIN);
    json_object_put(two);
    two = snapshot(&tip,&a,&b);

    VERIFY(json_object_object_get_ex(two,"credits",&headers));
    VERIFY(json_object_array_del_idx(headers,1,1)==0);
    VERIFY(verify(env,db,200,tip_hash,one,two,digest,&count,&reward)
           == EAGAIN);
    json_object_put(two);
    two = snapshot(&tip,&a,&b);

    /* Independently claimed common chain anchor must agree in every
     * declared field, not merely the hash/height label. */
    json_object *anchor = NULL;
    VERIFY(json_object_object_get_ex(two,"anchor",&anchor));
    json_object_object_add(anchor,"difficulty",json_object_new_int64(500001));
    VERIFY(verify(env,db,200,tip_hash,one,two,digest,&count,&reward)
           == EAGAIN);
    json_object_put(two);
    two = snapshot(&tip,&a,&b);

    VERIFY(json_object_object_get_ex(two,"anchor",&anchor));
    json_object_object_add(anchor,"orphan_status",json_object_new_boolean(1));
    VERIFY(verify(env,db,200,tip_hash,one,two,digest,&count,&reward)
           == EAGAIN);
    json_object_put(two);
    two = snapshot(&tip,&a,&b);

    uint8_t wrong_tip[32]; memcpy(wrong_tip,tip_hash,32);wrong_tip[0]^=1;
    VERIFY(verify(env,db,200,wrong_tip,one,two,digest,&count,&reward)
           == EAGAIN);
    VERIFY(verify(env,db,199,tip_hash,one,two,digest,&count,&reward)
           == EAGAIN);
    VERIFY(verify(env,db,179,tip_hash,one,two,digest,&count,&reward)
           == EAGAIN); /* b at 120 needs 60 confirmations. */
    VERIFY(verify(env,db,200,tip_hash,one,NULL,digest,&count,&reward)
           == EINVAL);
    VERIFY(memcmp(hold,digest,32)==0 && count==prev_count &&
           reward==prev_reward);

    json_object *empty = json_object_new_object();
    json_object_object_add(empty,"anchor",header(&tip));
    VERIFY(verify(env,db,200,tip_hash,one,empty,digest,&count,&reward)
           == EAGAIN);
    json_object_put(empty);

    /* Abandoned credit can never be rescued by two synthetic witnesses:
     * the authoritative local source scan still holds the pipeline.
     */
    frg_history_saved_t bad = block(99,9,0,999);
    insert(env,db,&bad);
    VERIFY(verify(env,db,200,tip_hash,one,two,digest,&count,&reward)
           == EPROTO);
    VERIFY(memcmp(hold,digest,32)==0 && count==prev_count &&
           reward==prev_reward);

    json_object_put(one);
    json_object_put(two);
    mdb_dbi_close(env,db);
    mdb_env_close(env);
    char file[512];
    snprintf(file,sizeof file,"%s/data.mdb",dir);OK(unlink(file));
    snprintf(file,sizeof file,"%s/lock.mdb",dir);OK(unlink(file));
    OK(rmdir(dir));
    printf("PASS: %u native dual-observer header/credited-LMDB "
           "crosscheck assertions; no RPC, wallet or payout\n",checks);
    return 0;
}
