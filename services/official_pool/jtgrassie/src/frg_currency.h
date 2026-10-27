/* Native FRG atomic amount helpers for jtgrassie pool adaptation.
 *
 * ForgeCoin consensus: COIN=100000000 (8 decimal places).
 * Parse decimal strings exactly; no floating point rounding for payout
 * thresholds and no overflow, signs, exponents, NaN, or >8 decimals.
 *
 * Research-only patch. Enabling real payouts requires release-gate reviews.
 */
#ifndef FRG_CURRENCY_H
#define FRG_CURRENCY_H

#include <stdint.h>
#include <stddef.h>

#define FRG_ATOMIC_UNITS UINT64_C(100000000)
#define FRG_COIN_DECIMALS 8

static inline int
frg_parse_amount_atomic(const char *amount, uint64_t *out)
{
    uint64_t integral = 0;
    uint64_t fractional = 0;
    unsigned decimals = 0;
    const unsigned char *p = (const unsigned char *)amount;

    if (amount == NULL || out == NULL || *p < '0' || *p > '9')
        return -1;
    while (*p >= '0' && *p <= '9')
    {
        unsigned digit = (unsigned)(*p++ - '0');
        if (integral > (UINT64_MAX - digit) / 10)
            return -1;
        integral = integral * 10 + digit;
    }
    if (*p == '.')
    {
        ++p;
        if (*p < '0' || *p > '9')
            return -1;
        while (*p >= '0' && *p <= '9')
        {
            if (decimals >= FRG_COIN_DECIMALS)
                return -1;
            fractional = fractional * 10 + (unsigned)(*p++ - '0');
            ++decimals;
        }
    }
    if (*p != '\0' || integral > UINT64_MAX / FRG_ATOMIC_UNITS)
        return -1;
    while (decimals++ < FRG_COIN_DECIMALS)
        fractional *= 10;
    uint64_t whole = integral * FRG_ATOMIC_UNITS;
    if (fractional > UINT64_MAX - whole)
        return -1;
    *out = whole + fractional;
    return 0;
}

/* Checked integer accounting: a failed credit must not wrap a live miner's
 * uint64 atomic balance. On overflow, out is left unchanged. */
static inline int
frg_checked_balance_add(uint64_t current, uint64_t credit, uint64_t *out)
{
    if (out == NULL || credit > UINT64_MAX - current)
        return -1;
    *out = current + credit;
    return 0;
}

/* Research policy: exactly 1% of each eligible allocated amount, rounded
 * down in atomic units. Avoid floating-point balance/fee drift entirely.
 * Reconciliation across share allocations and orphaned blocks remains a
 * separate launch gate, NOT proven by this helper.
 */
static inline uint64_t
frg_pool_fee_atomic(uint64_t amount)
{
    return amount / UINT64_C(100);
}

static inline double
frg_atomic_to_coin(uint64_t amount)
{
    return (double)amount / (double)FRG_ATOMIC_UNITS;
}

#endif
