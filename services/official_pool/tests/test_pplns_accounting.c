/* Standalone C test for actual PPLNS allocation helper.
 * No wallet, daemon, network, LMDB, public Stratum, or payout authorization.
 */
#include <assert.h>
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include "../jtgrassie/src/frg_pplns_accounting.h"
#include "../jtgrassie/src/frg_currency.h"

static uint64_t allocation(uint64_t diff, uint64_t blockdiff, double multiplier,
                           uint64_t reward, uint64_t paid)
{
    uint64_t out = UINT64_MAX;
    assert(frg_pplns_share_atomic(diff, blockdiff, multiplier, reward, paid, &out));
    assert(out <= reward - paid);
    return out;
}

static void precise_rounding_and_fee(void)
{
    const uint64_t reward = UINT64_C(100000000);
    uint64_t credited = 0, miners = 0, operator = 0;
    for (unsigned i = 0; i < 4; ++i)
    {
        const uint64_t amount = allocation(50, 100, 2.0, reward, credited);
        assert(amount == UINT64_C(25000000));
        credited += amount;
        const uint64_t fee = frg_pool_fee_atomic(amount);
        assert(fee == UINT64_C(250000));
        miners += amount - fee;
        operator += fee;
    }
    assert(frg_pplns_fully_accounted(reward, credited));
    assert(miners == UINT64_C(99000000));
    assert(operator == UINT64_C(1000000));
    assert(miners + operator == reward);
    assert(!frg_pplns_fully_accounted(reward, reward - 1));
}

static void caps_and_bounds(void)
{
    const uint64_t reward = UINT64_MAX;
    assert(allocation(UINT64_MAX, 1, 0.5, reward, 0) == reward);
    assert(allocation(UINT64_MAX, UINT64_MAX, 1.0, reward, 0) == reward);
    assert(allocation(UINT64_MAX, UINT64_MAX, 2.0, reward, 0) <= reward / 2);
    assert(allocation(UINT64_MAX, 1, 1.0, reward, reward - 1) == 1);
    assert(allocation(0, 1, 2.0, reward, 0) == 0);
    assert(allocation(1, 1, 2.0, 0, 0) == 0);
    assert(allocation(1, 1, 2.0, 100, 100) == 0);
    assert(!frg_pplns_fully_accounted(0, 0));
    assert(!frg_pplns_fully_accounted(1, 0));
}

static void invalid_inputs_fail_closed(void)
{
    uint64_t out = UINT64_C(7);
    assert(!frg_pplns_share_atomic(1, 0, 2, 100, 0, &out));
    assert(!frg_pplns_share_atomic(1, 10, 0, 100, 0, &out));
    assert(!frg_pplns_share_atomic(1, 10, -1, 100, 0, &out));
    assert(!frg_pplns_share_atomic(1, 10, NAN, 100, 0, &out));
    assert(!frg_pplns_share_atomic(1, 10, INFINITY, 100, 0, &out));
    assert(!frg_pplns_share_atomic(1, 10, -INFINITY, 100, 0, &out));
    assert(!frg_pplns_share_atomic(1, 10, 2.0, 100, 101, &out));
    assert(!frg_pplns_share_atomic(1, 10, 2.0, 100, 0, NULL));
    assert(out == UINT64_C(7)); /* errors never silently mutate destination */
    assert(allocation(1, 1, DBL_MIN, 100, 0) == 100);
}

int main(void)
{
    precise_rounding_and_fee();
    caps_and_bounds();
    invalid_inputs_fail_closed();
    puts("PASS: capped native PPLNS share allocations; 1% ledger conservation; malformed inputs reject");
    return 0;
}
