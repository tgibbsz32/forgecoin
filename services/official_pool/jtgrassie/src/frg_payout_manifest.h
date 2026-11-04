/* Canonical FRG pool payout MANIFEST commitment (research-only).
 *
 * This module binds the exact ordered recipient list, amounts, unchanging
 * native-chain source-credit identity, pool fee cap and anchor into a SHA-256
 * digest. Batch ID is derived ONLY from chain UUID + canonical source-credit
 * digest so a changed recipient list or fee cannot bypass duplicate-batch
 * protection by generating a different ID.
 *
 * This does NOT authenticate an FRG address checksum, sign a transaction,
 * prove source credit eligibility, reconcile native wallet outputs, debit
 * LMDB, enable pool payouts, or permit payout journal clearing. Issue #210.
 */
#ifndef FRG_PAYOUT_MANIFEST_H
#define FRG_PAYOUT_MANIFEST_H

#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <openssl/evp.h>

#define FRG_PAYOUT_MAX_RECIPIENTS 25
#define FRG_PAYOUT_MAX_ADDRESS_BYTES 127
#define FRG_PAYOUT_MIN_ADDRESS_BYTES 90
#define FRG_PAYOUT_MIN_ANCHOR_HEIGHT UINT64_C(60)

typedef struct frg_payout_recipient
{
    const char *address;
    uint64_t amount_atomic;
} frg_payout_recipient_t;

static inline bool
frg_payout_manifest_nonzero(const uint8_t *p, size_t length)
{
    if (!p) return false;
    uint8_t v = 0;
    for (size_t i = 0; i < length; ++i) v |= p[i];
    return v != 0;
}

static inline bool
frg_payout_manifest_address_ok(const char *address)
{
    if (!address) return false;
    size_t len = 0;
    while (len <= FRG_PAYOUT_MAX_ADDRESS_BYTES && address[len]) {
        const char c = address[len];
        const bool b58 = (c >= '1' && c <= '9') ||
            (c >= 'A' && c <= 'H') || (c >= 'J' && c <= 'N') ||
            (c >= 'P' && c <= 'Z') || (c >= 'a' && c <= 'k') ||
            (c >= 'm' && c <= 'z');
        if (!b58) return false;
        ++len;
    }
    return len >= FRG_PAYOUT_MIN_ADDRESS_BYTES &&
           len <= FRG_PAYOUT_MAX_ADDRESS_BYTES;
}

static inline bool
frg_payout_digest_write(EVP_MD_CTX *ctx, const void *data, size_t length)
{
    return EVP_DigestUpdate(ctx, data, length) == 1;
}

static inline bool
frg_payout_digest_u64(EVP_MD_CTX *ctx, uint64_t number)
{
    uint8_t bytes[8];
    for (int i = 7; i >= 0; --i) {
        bytes[i] = (uint8_t)(number & UINT64_C(255));
        number >>= 8;
    }
    return frg_payout_digest_write(ctx, bytes, sizeof(bytes));
}

/* No nondeterministic sorting: caller MUST pass unique ascending Base58
 * addresses. This avoids silent reordering and duplicated payee outputs.
 * Address checksum/prefix validation and independent output review remain
 * mandatory outside this offline commitment function.
 */
static inline int
frg_payout_manifest_hash(
    const uint8_t chain_uuid[16],
    const uint8_t credited_sources_sha256[32],
    const uint8_t anchor_hash[32], uint64_t anchor_height,
    const frg_payout_recipient_t *recipients, size_t count,
    uint64_t max_fee_atomic, uint8_t out_batch_id[32],
    uint8_t out_manifest_sha256[32], uint64_t *out_total_atomic)
{
    if (!chain_uuid || !credited_sources_sha256 || !anchor_hash ||
        !recipients || !out_batch_id || !out_manifest_sha256 ||
        !out_total_atomic || out_batch_id == out_manifest_sha256 ||
        !frg_payout_manifest_nonzero(chain_uuid, 16) ||
        !frg_payout_manifest_nonzero(credited_sources_sha256, 32) ||
        !frg_payout_manifest_nonzero(anchor_hash, 32) ||
        anchor_height < FRG_PAYOUT_MIN_ANCHOR_HEIGHT ||
        count == 0 || count > FRG_PAYOUT_MAX_RECIPIENTS)
        return EINVAL;

    uint64_t total = 0;
    for (size_t i = 0; i < count; ++i) {
        if (!frg_payout_manifest_address_ok(recipients[i].address) ||
            !recipients[i].amount_atomic ||
            UINT64_MAX - total < recipients[i].amount_atomic)
            return EINVAL;
        if (i > 0 && strcmp(recipients[i - 1].address,
                            recipients[i].address) >= 0)
            return EINVAL;
        total += recipients[i].amount_atomic;
    }
    if (max_fee_atomic > total) return EINVAL;

    static const char id_domain[] = "FRG.PAYOUT.BATCH.V1";
    static const char manifest_domain[] = "FRG.PAYOUT.MANIFEST.V1";
    int rc = EIO;
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    if (!ctx) return ENOMEM;
    unsigned digest_size = 0;
    uint8_t batch[32] = {0}, manifest[32] = {0};

    if (EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1 ||
        !frg_payout_digest_write(ctx, id_domain, sizeof(id_domain) - 1) ||
        !frg_payout_digest_write(ctx, chain_uuid, 16) ||
        !frg_payout_digest_write(ctx, credited_sources_sha256, 32) ||
        EVP_DigestFinal_ex(ctx, batch, &digest_size) != 1 ||
        digest_size != 32) goto done;

    if (EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1 ||
        !frg_payout_digest_write(ctx, manifest_domain, sizeof(manifest_domain) - 1) ||
        !frg_payout_digest_write(ctx, chain_uuid, 16) ||
        !frg_payout_digest_write(ctx, credited_sources_sha256, 32) ||
        !frg_payout_digest_write(ctx, anchor_hash, 32) ||
        !frg_payout_digest_u64(ctx, anchor_height) ||
        !frg_payout_digest_u64(ctx, total) ||
        !frg_payout_digest_u64(ctx, max_fee_atomic) ||
        !frg_payout_digest_u64(ctx, (uint64_t)count)) goto done;

    for (size_t i = 0; i < count; ++i) {
        const size_t address_length = strlen(recipients[i].address);
        uint8_t length = (uint8_t)address_length;
        if (!frg_payout_digest_write(ctx, &length, 1) ||
            !frg_payout_digest_write(ctx, recipients[i].address, address_length) ||
            !frg_payout_digest_u64(ctx, recipients[i].amount_atomic))
            goto done;
    }

    if (EVP_DigestFinal_ex(ctx, manifest, &digest_size) != 1 ||
        digest_size != 32) goto done;
    memcpy(out_batch_id, batch, 32);
    memcpy(out_manifest_sha256, manifest, 32);
    *out_total_atomic = total;
    rc = 0;

done:
    EVP_MD_CTX_free(ctx);
    return rc;
}

#endif
