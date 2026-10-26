/* Standalone native FRG decimal conversion regression test.
 * No daemon, wallet, pool, network, LMDB or external dependencies.
 */
#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../jtgrassie/src/frg_currency.h"

struct accepted {
    const char *input;
    uint64_t expected;
};

int main(void)
{
    const struct accepted examples[] = {
        {"0", UINT64_C(0)},
        {"0.0", UINT64_C(0)},
        {"0.00000000", UINT64_C(0)},
        {"0.00000001", UINT64_C(1)},
        {"0.1", UINT64_C(10000000)},
        {"0.33", UINT64_C(33000000)},
        {"1", UINT64_C(100000000)},
        {"1.23456789", UINT64_C(123456789)},
        {"50", UINT64_C(5000000000)},
        {"50000000", UINT64_C(5000000000000000)},
        {"184467440737.09551615", UINT64_MAX},
        {"001.00000001", UINT64_C(100000001)},
    };
    const char *rejected[] = {
        "", "1.", ".1", "-1", "+1", " 1", "1 ", "1e2", "NaN",
        "Infinity", "0.000000001", "1.000000000", "1.2.3",
        "184467440737.09551616", "184467440738",
        "999999999999999999999999999999", "1x", "1/0",
    };
    for (size_t i = 0; i < sizeof(examples) / sizeof(examples[0]); ++i)
    {
        uint64_t got = UINT64_C(9999);
        int rc = frg_parse_amount_atomic(examples[i].input, &got);
        if (rc != 0 || got != examples[i].expected)
        {
            fprintf(stderr, "FRG valid parse failed: %s rc=%d value=%" PRIu64 "\n",
                    examples[i].input, rc, got);
            return 1;
        }
    }
    for (size_t i = 0; i < sizeof(rejected) / sizeof(rejected[0]); ++i)
    {
        uint64_t got = UINT64_C(12345);
        if (frg_parse_amount_atomic(rejected[i], &got) != -1 ||
            got != UINT64_C(12345))
        {
            fprintf(stderr, "FRG invalid amount accepted: %s\n", rejected[i]);
            return 1;
        }
    }
    assert(frg_parse_amount_atomic(NULL, NULL) == -1);
    assert(frg_parse_amount_atomic("1", NULL) == -1);
    assert(FRG_ATOMIC_UNITS == UINT64_C(100000000));
    assert(frg_atomic_to_coin(UINT64_C(33000000)) == 0.33);
    assert(frg_atomic_to_coin(UINT64_C(100000000)) == 1.0);
    assert(frg_pool_fee_atomic(UINT64_C(0)) == 0);
    assert(frg_pool_fee_atomic(UINT64_C(99)) == 0);
    assert(frg_pool_fee_atomic(UINT64_C(100)) == 1);
    assert(frg_pool_fee_atomic(UINT64_C(199)) == 1);
    assert(frg_pool_fee_atomic(UINT64_C(100000000)) == UINT64_C(1000000));
    assert(frg_pool_fee_atomic(UINT64_MAX) == UINT64_MAX / 100);
    puts("PASS: FRG exact 8-decimal parser, overflow and integer 1% fee (40 checks)");
    return 0;
}
