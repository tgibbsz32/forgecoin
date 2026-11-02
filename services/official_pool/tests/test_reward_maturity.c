/* Pure C verification of the SAME native pool reward/maturity helpers.
 * No daemon, wallet, network listener, real funds, or live LMDB required.
 */
#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include "../jtgrassie/src/frg_reward_maturity.h"
#include "../jtgrassie/src/frg_currency.h"

static void test_maturity(void)
{
    assert(FRG_MINED_REWARD_UNLOCK_WINDOW == UINT64_C(60));
    assert(!frg_reward_mature(0, 0));
    assert(!frg_reward_mature(0, 59));
    assert(frg_reward_mature(0, 60));
    assert(frg_reward_mature(0, 61));
    assert(!frg_reward_mature(1, 60));
    assert(frg_reward_mature(1, 61));
    assert(!frg_reward_mature(1000, 999));
    assert(!frg_reward_mature(1000, 1059));
    assert(frg_reward_mature(1000, 1060));
    assert(!frg_reward_mature(UINT64_MAX, 0));
    assert(!frg_reward_mature(UINT64_MAX, UINT64_MAX));
    assert(!frg_reward_mature(UINT64_MAX - 59, UINT64_MAX));
    assert(frg_reward_mature(UINT64_MAX - 60, UINT64_MAX));
    assert(frg_reward_mature(UINT64_MAX - 61, UINT64_MAX));
}

static void test_header_window(void)
{
    uint64_t start = 789, end = 987;
    assert(!frg_mature_header_window(59, 10, &start, &end));
    assert(start == 789 && end == 987);
    assert(!frg_mature_header_window(60, 10, &start, &end));
    assert(!frg_mature_header_window(68, 10, &start, &end));
    assert(frg_mature_header_window(69, 10, &start, &end));
    assert(start == 0 && end == 9);
    assert(frg_mature_header_window(70, 10, &start, &end));
    assert(start == 1 && end == 10);
    assert(frg_mature_header_window(60, 1, &start, &end));
    assert(start == 0 && end == 0);
    assert(!frg_mature_header_window(500, 0, &start, &end));
    assert(!frg_mature_header_window(500, UINT64_MAX, &start, &end));
    assert(!frg_mature_header_window(500, 10, NULL, &end));
    assert(!frg_mature_header_window(500, 10, &start, NULL));
    assert(frg_mature_header_window(UINT64_MAX, 10, &start, &end));
    assert(end == UINT64_MAX - 60);
    assert(start == UINT64_MAX - 69);
}

static void test_fee_and_balance_invariants(void)
{
    const uint64_t amounts[] = {
        0, 1, 99, 100, 199, 100000000, 2384185222, UINT64_MAX
    };
    for (size_t i = 0; i < sizeof amounts / sizeof *amounts; ++i)
    {
        const uint64_t fee = frg_pool_fee_atomic(amounts[i]);
        const uint64_t miner = amounts[i] - fee;
        assert(fee == amounts[i] / UINT64_C(100));
        assert(fee <= amounts[i]);
        assert(miner + fee == amounts[i]);
    }
    assert(frg_pool_fee_atomic(UINT64_C(100000000)) == UINT64_C(1000000));
    assert(frg_pool_fee_atomic(UINT64_C(2384185222)) == UINT64_C(23841852));
}

int main(void)
{
    test_maturity();
    test_header_window();
    test_fee_and_balance_invariants();
    puts("PASS: 60-height pool maturity boundaries, bounded canonical headers and exact integer 1% fee");
    return 0;
}
