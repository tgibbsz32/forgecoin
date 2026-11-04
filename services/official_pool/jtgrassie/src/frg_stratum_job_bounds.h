#ifndef FRG_STRATUM_JOB_BOUNDS_H
#define FRG_STRATUM_JOB_BOUNDS_H

#include <stdbool.h>
#include <stddef.h>

/*
 * Native pool source safety gate. Never infer a valid canonical block or
 * sufficient proof of work from this byte-span check alone.
 *
 * Cryptonote's nonce occupies four bytes at offset 39. The pool writes
 * extra_nonce + instance_id (8 bytes) into the daemon's reserved region;
 * xmr-node-proxy mode additionally writes two proxy nonces (16 total).
 *
 * Check with subtraction to avoid overflow for an untrusted offset.
 */
#define FRG_STRATUM_NONCE_OFFSET ((size_t)39)
#define FRG_STRATUM_NONCE_SIZE ((size_t)4)
#define FRG_STRATUM_RESERVED_NORMAL ((size_t)8)
#define FRG_STRATUM_RESERVED_PROXY ((size_t)16)

static inline bool frg_stratum_job_bounds_valid(size_t blob_size,
                                                 size_t reserved_offset,
                                                 bool writes_reserved,
                                                 bool proxy)
{
    if (blob_size < FRG_STRATUM_NONCE_OFFSET + FRG_STRATUM_NONCE_SIZE)
        return false;
    if (!writes_reserved)
        return true;
    if (reserved_offset > blob_size)
        return false;
    const size_t required = proxy ? FRG_STRATUM_RESERVED_PROXY :
                                    FRG_STRATUM_RESERVED_NORMAL;
    return blob_size - reserved_offset >= required;
}

#endif /* FRG_STRATUM_JOB_BOUNDS_H */
