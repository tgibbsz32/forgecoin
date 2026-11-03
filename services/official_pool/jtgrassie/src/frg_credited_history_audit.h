/* Read-only historical validation of already-credited pool candidates.
 * Distinguish invalid/unavailable RPC (UNVERIFIED) from a structurally valid,
 * conflicting canonical block (CONFLICT). Neither permits a wallet transfer.
 */
#ifndef FRG_CREDITED_HISTORY_AUDIT_H
#define FRG_CREDITED_HISTORY_AUDIT_H

#include <json-c/json.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include "frg_canonical_headers.h"

enum frg_history_verdict {
    FRG_HISTORY_UNVERIFIED = 0,
    FRG_HISTORY_MATCH = 1,
    FRG_HISTORY_CONFLICT = 2
};

/* Stored LMDB hashes are exactly 64 bytes and may not have a terminator. */
static inline bool frg_fixed_hash64(const char raw[64])
{
    if (!raw) return false;
    for (size_t i = 0; i < 64; ++i) {
        const char c = raw[i];
        if (!((c >= '0' && c <= '9') ||
              (c >= 'a' && c <= 'f') ||
              (c >= 'A' && c <= 'F'))) return false;
    }
    return true;
}

static inline enum frg_history_verdict
frg_history_compare(const struct json_object *header,
                    uint64_t expected_height,
                    const char saved_hash[64],
                    const char saved_parent[64],
                    uint64_t saved_difficulty,
                    uint64_t saved_reward)
{
    if (!header || !frg_fixed_hash64(saved_hash) ||
        !frg_fixed_hash64(saved_parent) || !saved_difficulty || !saved_reward)
        return FRG_HISTORY_UNVERIFIED;

    struct json_object *height = NULL, *difficulty = NULL, *reward = NULL;
    struct json_object *timestamp = NULL, *hash = NULL, *parent = NULL;
    struct json_object *orphan = NULL;
    if (!frg_json_member(header, "height", json_type_int, &height) ||
        !frg_json_member(header, "difficulty", json_type_int, &difficulty) ||
        !frg_json_member(header, "reward", json_type_int, &reward) ||
        !frg_json_member(header, "timestamp", json_type_int, &timestamp) ||
        !frg_json_member(header, "hash", json_type_string, &hash) ||
        !frg_json_member(header, "prev_hash", json_type_string, &parent) ||
        !frg_json_member(header, "orphan_status", json_type_boolean, &orphan))
        return FRG_HISTORY_UNVERIFIED;

    int64_t h = json_object_get_int64(height);
    int64_t diff = json_object_get_int64(difficulty);
    int64_t pay = json_object_get_int64(reward);
    int64_t ts = json_object_get_int64(timestamp);
    const char *chain_hash = json_object_get_string(hash);
    const char *chain_parent = json_object_get_string(parent);
    if (h < 0 || diff <= 0 || pay <= 0 || ts < 0 ||
        !frg_hex_hash64(chain_hash) || !frg_hex_hash64(chain_parent))
        return FRG_HISTORY_UNVERIFIED;
    /* A response for another height is not proof of a reorg at the
     * requested credited height; it is an unverified/misdirected RPC.
     */
    if ((uint64_t)h != expected_height)
        return FRG_HISTORY_UNVERIFIED;
    if (memcmp(chain_hash, saved_hash, 64) != 0 ||
        memcmp(chain_parent, saved_parent, 64) != 0 ||
        json_object_get_boolean(orphan))
        return FRG_HISTORY_CONFLICT;
    /* A hash-identical header with altered reward/difficulty is internally
     * inconsistent RPC evidence, not a cryptographically supported fork.
     * Hold payouts, but do NOT write an irreversible reorg marker.
     */
    if ((uint64_t)diff != saved_difficulty ||
        (uint64_t)pay != saved_reward)
        return FRG_HISTORY_UNVERIFIED;
    return FRG_HISTORY_MATCH;
}

#endif
