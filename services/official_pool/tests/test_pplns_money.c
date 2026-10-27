#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include "../jtgrassie/src/frg_pplns_money.h"
#include "../jtgrassie/src/frg_currency.h"

int main(void) {
    assert(frg_pplns_share_reward_atomic(0,100,100)==0);
    assert(frg_pplns_share_reward_atomic(100,0,100)==0);
    assert(frg_pplns_share_reward_atomic(100,100,0)==0);
    assert(frg_pplns_share_reward_atomic(100,100,100000000)==50000000);
    assert(frg_pplns_share_reward_atomic(200,100,100000000)==100000000);
    assert(frg_pplns_share_reward_atomic(300,100,100000000)==100000000);
    assert(frg_pplns_share_reward_atomic(1,3,100)==16);
    assert(frg_pplns_share_reward_atomic(1,3,UINT64_MAX)==UINT64_MAX/6);
    assert(frg_pplns_share_reward_atomic(UINT64_MAX,UINT64_MAX,UINT64_MAX)==UINT64_MAX/2);
    assert(frg_pplns_share_reward_atomic(UINT64_MAX,1,UINT64_MAX)==UINT64_MAX);
    uint64_t reward=UINT64_C(2384185222);
    uint64_t allocated=0;
    for (unsigned i=0;i<201;i++) {
        uint64_t piece=frg_pplns_share_reward_atomic(10000,1000000,reward);
        if(piece>reward-allocated)piece=reward-allocated;
        allocated+=piece;
    }
    assert(allocated==reward);
    uint64_t fee=frg_pool_fee_atomic(allocated);
    assert(fee==reward/100);
    assert(allocated-fee+fee==reward);
    puts("PASS: atomic PPLNS value bounds, rounding, cap, full conservation and exact fee");
    return 0;
}
