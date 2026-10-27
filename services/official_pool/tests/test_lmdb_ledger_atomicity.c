/* Oracle ARM64 LMDB crash/credit semantics fixture for ForgeCoin pool.
 * Real liblmdb and the same checked FRG atomic helper as native C pool.
 * It models nested balance credits + outer block status commit, but DOES NOT
 * run pool.c's internal process_blocks or issue any wallet/daemon RPC.
 */
#define _XOPEN_SOURCE 700
#include <assert.h>
#include <inttypes.h>
#include <lmdb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "../jtgrassie/src/frg_currency.h"

static MDB_env *env;
static MDB_dbi balances;
static MDB_dbi blocks;
static const char *miner = "disposable-qa-miner";
static const char *height = "block-1";

static int put_u64(MDB_txn *txn,MDB_dbi db,const char *name,uint64_t amount)
{
    MDB_val k={strlen(name), (void*)name};
    MDB_val v={sizeof(amount),&amount};
    return mdb_put(txn,db,&k,&v,0);
}
static uint64_t get_u64(MDB_txn *txn,MDB_dbi db,const char *name)
{
    MDB_val k={strlen(name),(void*)name};
    MDB_val v;
    assert(mdb_get(txn,db,&k,&v)==MDB_SUCCESS);
    assert(v.mv_size==sizeof(uint64_t));
    uint64_t number;
    memcpy(&number,v.mv_data,sizeof(number));
    return number;
}
static void check(uint64_t amount,uint64_t state)
{
    MDB_txn *tx=NULL;
    assert(mdb_txn_begin(env,NULL,MDB_RDONLY,&tx)==0);
    assert(get_u64(tx,balances,miner)==amount);
    assert(get_u64(tx,blocks,height)==state);
    mdb_txn_abort(tx);
}
static int credit_nested(MDB_txn *parent,uint64_t amount)
{
    MDB_txn *child=NULL;
    int rc=mdb_txn_begin(env,parent,0,&child);
    if (rc)return rc;
    uint64_t old=get_u64(child,balances,miner);
    uint64_t after=0;
    if (frg_checked_balance_add(old,amount,&after)!=0)
    {
        mdb_txn_abort(child);
        return MDB_BAD_VALSIZE;
    }
    rc=put_u64(child,balances,miner,after);
    if(rc){mdb_txn_abort(child);return rc;}
    return mdb_txn_commit(child);
}
static void reset(uint64_t amount,uint64_t state)
{
    MDB_txn *tx=NULL;
    assert(mdb_txn_begin(env,NULL,0,&tx)==0);
    assert(put_u64(tx,balances,miner,amount)==0);
    assert(put_u64(tx,blocks,height,state)==0);
    assert(mdb_txn_commit(tx)==0);
}
static void once(uint64_t amount)
{
    MDB_txn *tx=NULL;
    assert(mdb_txn_begin(env,NULL,0,&tx)==0);
    uint64_t state=get_u64(tx,blocks,height);
    if (!state)
    {
        int rc=credit_nested(tx,amount);
        if(rc){mdb_txn_abort(tx);return;}
        assert(put_u64(tx,blocks,height,1)==0);
    }
    assert(mdb_txn_commit(tx)==0);
}
int main(void)
{
    char directory[]="/tmp/forgecoin-ledger-fixture-XXXXXX";
    assert(mkdtemp(directory)!=NULL);
    assert(mdb_env_create(&env)==0);
    assert(mdb_env_set_maxdbs(env,5)==0);
    assert(mdb_env_set_mapsize(env,16u*1024u*1024u)==0);
    assert(mdb_env_open(env,directory,0,0600)==0);
    MDB_txn *tx=NULL;
    assert(mdb_txn_begin(env,NULL,0,&tx)==0);
    assert(mdb_dbi_open(tx,"miner_balance",MDB_CREATE,&balances)==0);
    assert(mdb_dbi_open(tx,"mature_blocks",MDB_CREATE,&blocks)==0);
    assert(put_u64(tx,balances,miner,0)==0);
    assert(put_u64(tx,blocks,height,0)==0);
    assert(mdb_txn_commit(tx)==0);

    /* Child LMDB commit is still part of outer parent. An outer failure
       rolls BOTH balance and block status back without partial credit. */
    assert(mdb_txn_begin(env,NULL,0,&tx)==0);
    assert(credit_nested(tx,99)==0);
    assert(put_u64(tx,blocks,height,1)==0);
    mdb_txn_abort(tx);
    check(0,0);

    /* Successful payout allocation is atomic with mature block status. */
    once(100);
    check(100,1);

    /* Idempotent status guard prevents double local allocation. */
    once(100);
    check(100,1);

    /* Overflow may NEVER wrap or flip a block to credited. */
    reset(UINT64_MAX-1,0);
    assert(mdb_txn_begin(env,NULL,0,&tx)==0);
    assert(credit_nested(tx,2)==MDB_BAD_VALSIZE);
    mdb_txn_abort(tx);
    check(UINT64_MAX-1,0);

    /* Nested credit can fit exactly at maximum, then remains idempotent. */
    once(1);
    check(UINT64_MAX,1);
    once(1);
    check(UINT64_MAX,1);

    mdb_dbi_close(env,balances);
    mdb_dbi_close(env,blocks);
    mdb_env_close(env);
    char dbfile[512],lockfile[512];
    snprintf(dbfile,sizeof(dbfile),"%s/data.mdb",directory);
    snprintf(lockfile,sizeof(lockfile),"%s/lock.mdb",directory);
    unlink(dbfile);unlink(lockfile);rmdir(directory);
    puts("PASS: LMDB nested-credit abort, atomic maturity status, local idempotency and uint64 overflow protection");
    return 0;
}
