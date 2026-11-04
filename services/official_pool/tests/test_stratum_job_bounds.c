#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#include "../jtgrassie/src/frg_stratum_job_bounds.h"

static unsigned checks;
static void check(bool passed)
{
    checks++;
    assert(passed);
}

int main(void)
{
    /* Nonce: four bytes at offset 39, including last byte 42. */
    check(!frg_stratum_job_bounds_valid(0, 0, false, false));
    check(!frg_stratum_job_bounds_valid(39, 0, false, false));
    check(!frg_stratum_job_bounds_valid(42, 0, false, false));
    check(frg_stratum_job_bounds_valid(43, 0, false, false));
    check(frg_stratum_job_bounds_valid(43, SIZE_MAX, false, false));

    /* Normal pool needs exactly 8 reserved bytes without overflow. */
    check(!frg_stratum_job_bounds_valid(43, 36, true, false));
    check(frg_stratum_job_bounds_valid(43, 35, true, false));
    check(frg_stratum_job_bounds_valid(100, 92, true, false));
    check(!frg_stratum_job_bounds_valid(100, 93, true, false));
    check(!frg_stratum_job_bounds_valid(100, 101, true, false));
    check(!frg_stratum_job_bounds_valid(100, SIZE_MAX, true, false));

    /* Proxy supplies pool_nonce and worker_nonce, requiring 16 bytes. */
    check(frg_stratum_job_bounds_valid(100, 84, true, true));
    check(!frg_stratum_job_bounds_valid(100, 85, true, true));
    check(!frg_stratum_job_bounds_valid(43, 35, true, true));
    check(frg_stratum_job_bounds_valid(43, 27, true, true));

    /* Prefer valid realistic template lengths; reject rollover offsets. */
    check(frg_stratum_job_bounds_valid(4096, 140, true, true));
    check(frg_stratum_job_bounds_valid(SIZE_MAX, SIZE_MAX - 8, true, false));
    check(!frg_stratum_job_bounds_valid(SIZE_MAX, SIZE_MAX - 7, true, false));
    check(frg_stratum_job_bounds_valid(SIZE_MAX, SIZE_MAX - 16, true, true));
    check(!frg_stratum_job_bounds_valid(SIZE_MAX, SIZE_MAX - 15, true, true));

    printf("PASS: %u native Stratum job and nonce bounds assertions\n", checks);
    return 0;
}
