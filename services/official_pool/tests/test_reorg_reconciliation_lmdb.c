/* Disposable real-LMDB 60-block reward, orphan and deep-reorg fixture.
 * Exercises the same frg_reconcile_block() decision called by pool.c.
 * Does NOT start daemon, Stratum, wallet, or initiate any payout.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <inttypes.h>
#include <lmdb.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "../jtgrassie/src/frg_reconcile_policy.h"
#include "../jtgrassie/src/frg_currency.h"

#define CHECK(x) do { int rc_=(x); if(rc_) { \
    fprintf(stderr,"LMDB %s: %s\n",#x,mdb_strerror(rc_)); abort();} } while(0)
typedef struct fixture_block {
    uint64_t height;
    uint32_t status;
} fixture_block;

static MDB_val key_of(const char *s) { MDB_val v={strlen(s),(void*)s}; return v; }
static void put_value(MDB_txn *txn,MDB_dbi db,const char *k,
                      const void *bytes,size_t len)
{
    MDB_val key=key_of(k),val={len,(void*)bytes};
    CHECK(mdb_put(txn,db,&key,&val,0));
}
static bool read_block(MDB_txn *txn,MDB_dbi blocks,const char *name,
                       fixture_block *out)
{
    MDB_val k=key_of(name),v;
    int rc=mdb_get(txn,blocks,&k,&v);
    if(rc==MDB_NOTFOUND) return false;
    CHECK(rc);
    assert(v.mv_size==sizeof(*out));
    memcpy(out,v.mv_data,sizeof(*out));
    return true;
}
static uint64_t balance(MDB_txn *txn,MDB_dbi db,const char *name)
{
    MDB_val k=key_of(name),v;
    int rc=mdb_get(txn,db,&k,&v);
    if(rc==MDB_NOTFOUND) return 0;
    CHECK(rc);
    assert(v.mv_size==sizeof(uint64_t));
    uint64_t value;
    memcpy(&value,v.mv_data,sizeof(value));
    return value;
}
static enum frg_reconcile_action
reconcile(MDB_env *env,MDB_dbi blocks,MDB_dbi balances,
          const char *name,uint64_t tip,uint64_t observed,
          bool same_hash,bool same_parent,bool daemon_orphan)
{
    MDB_txn *txn=NULL;
    CHECK(mdb_txn_begin(env,NULL,0,&txn));
    fixture_block saved;
    assert(read_block(txn,blocks,name,&saved));
    const enum frg_reconcile_action action=frg_reconcile_block(
        saved.status,saved.height,observed,tip,
        same_hash,same_parent,daemon_orphan);
    if(action==FRG_RECONCILE_MARK_ORPHAN) {
        saved.status=FRG_SAVED_ORPHANED;
        put_value(txn,blocks,name,&saved,sizeof(saved));
        CHECK(mdb_txn_commit(txn));
        return action;
    }
    if(action==FRG_RECONCILE_CREDIT) {
        const uint64_t reward=UINT64_C(100000000);
        const uint64_t fee=frg_pool_fee_atomic(reward);
        assert(fee==UINT64_C(1000000));
        MDB_txn *child=NULL;
        CHECK(mdb_txn_begin(env,txn,0,&child));
        const uint64_t miner=reward-fee;
        /* two distinct test candidates have distinct miner accounting keys */
        const char *miner_key=strcmp(name,"candidate_A")==0?"miner_A":"miner_B";
        const uint64_t old_miner=balance(child,balances,miner_key);
        const uint64_t old_fee=balance(child,balances,"fee");
        assert(old_miner<=UINT64_MAX-miner && old_fee<=UINT64_MAX-fee);
        const uint64_t updated_miner=old_miner+miner,updated_fee=old_fee+fee;
        put_value(child,balances,miner_key,&updated_miner,sizeof(updated_miner));
        put_value(child,balances,"fee",&updated_fee,sizeof(updated_fee));
        CHECK(mdb_txn_commit(child));
        saved.status=FRG_SAVED_UNLOCKED;
        put_value(txn,blocks,name,&saved,sizeof(saved));
        CHECK(mdb_txn_commit(txn));
        return action;
    }
    /* A reorg after credit must never commit a second or compensating credit.
     * DEFER, duplicate, and invalid cases are also side-effect free.
     */
    mdb_txn_abort(txn);
    return action;
}
static void check(MDB_env *env,MDB_dbi blocks,MDB_dbi balances,
                  const char *name,uint32_t status,
                  uint64_t miner,uint64_t fee)
{
    MDB_txn *read=NULL;
    CHECK(mdb_txn_begin(env,NULL,MDB_RDONLY,&read));
    fixture_block block;
    assert(read_block(read,blocks,name,&block));
    assert(block.status==status);
    assert(balance(read,balances,
                   strcmp(name,"candidate_A")==0?"miner_A":"miner_B")==miner);
    assert(balance(read,balances,"fee")==fee);
    mdb_txn_abort(read);
}
int main(void)
{
    char dir[]="/tmp/frg-61-block-reorg-XXXXXX";
    assert(mkdtemp(dir)!=NULL);
    MDB_env *env=NULL;
    CHECK(mdb_env_create(&env));
    CHECK(mdb_env_set_maxdbs(env,4));
    CHECK(mdb_env_set_mapsize(env,4*1024*1024));
    CHECK(mdb_env_open(env,dir,0,0600));
    MDB_txn *txn=NULL;
    MDB_dbi blocks=0,balances=0;
    CHECK(mdb_txn_begin(env,NULL,0,&txn));
    CHECK(mdb_dbi_open(txn,"blocks",MDB_CREATE,&blocks));
    CHECK(mdb_dbi_open(txn,"balances",MDB_CREATE,&balances));
    const fixture_block b={11,FRG_SAVED_LOCKED};
    put_value(txn,blocks,"candidate_A",&b,sizeof(b));
    put_value(txn,blocks,"candidate_B",&b,sizeof(b));
    CHECK(mdb_txn_commit(txn));
    /* Tip 70 means only 59 further heights after block 11. No credit. */
    assert(reconcile(env,blocks,balances,"candidate_A",70,11,true,true,false)
           == FRG_RECONCILE_DEFER);
    check(env,blocks,balances,"candidate_A",FRG_SAVED_LOCKED,0,0);
    assert(reconcile(env,blocks,balances,"candidate_A",71,11,true,true,false)
           == FRG_RECONCILE_CREDIT);
    check(env,blocks,balances,"candidate_A",FRG_SAVED_UNLOCKED,
          UINT64_C(99000000),UINT64_C(1000000));
    /* A second callback for the same canonical block cannot double-credit. */
    assert(reconcile(env,blocks,balances,"candidate_A",72,11,true,true,false)
           == FRG_RECONCILE_ALREADY_CREDITED);
    check(env,blocks,balances,"candidate_A",FRG_SAVED_UNLOCKED,
          UINT64_C(99000000),UINT64_C(1000000));
    /* 90-block-deep mismatch, parent mismatch and daemon orphan flag all
     * fail closed for an already credited block. No balances are debited.
     */
    for(int variant=0;variant<3;++variant) {
        assert(reconcile(env,blocks,balances,"candidate_A",101,11,
               variant!=0,variant!=1,variant==2)
               == FRG_RECONCILE_ABORT_DEEP_REORG);
        check(env,blocks,balances,"candidate_A",FRG_SAVED_UNLOCKED,
              UINT64_C(99000000),UINT64_C(1000000));
    }
    assert(reconcile(env,blocks,balances,"candidate_A",101,12,true,true,false)
           == FRG_RECONCILE_ABORT_INVALID);
    assert(reconcile(env,blocks,balances,"candidate_B",70,11,false,true,false)
           == FRG_RECONCILE_DEFER);
    check(env,blocks,balances,"candidate_B",FRG_SAVED_LOCKED,0,
          UINT64_C(1000000));
    /* A candidate orphaned at its first mature eligibility never credits. */
    assert(reconcile(env,blocks,balances,"candidate_B",71,11,false,true,false)
           == FRG_RECONCILE_MARK_ORPHAN);
    check(env,blocks,balances,"candidate_B",FRG_SAVED_ORPHANED,0,
          UINT64_C(1000000));
    assert(reconcile(env,blocks,balances,"candidate_B",72,11,true,true,false)
           == FRG_RECONCILE_ALREADY_ORPHANED);
    check(env,blocks,balances,"candidate_B",FRG_SAVED_ORPHANED,0,
          UINT64_C(1000000));
    mdb_env_close(env);
    char path[512];
    snprintf(path,sizeof(path),"%s/data.mdb",dir); CHECK(unlink(path));
    snprintf(path,sizeof(path),"%s/lock.mdb",dir); CHECK(unlink(path));
    CHECK(rmdir(dir));
    puts("PASS: native LMDB tip 70 defers; tip 71 credits once; orphan never credits; 90-block deep-reorg alert freezes balances");
    return 0;
}
