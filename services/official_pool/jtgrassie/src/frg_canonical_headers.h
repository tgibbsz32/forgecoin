/* Strict validation of a daemon's exact canonical-header range response.
 * Never pass partial, stale, malformed, re-ordered or disconnected ranges
 * to the reward-crediting / orphan reconciliation callback.
 * This helper does not prove daemon honesty or authorize wallet payouts.
 */
#ifndef FRG_CANONICAL_HEADERS_H
#define FRG_CANONICAL_HEADERS_H

#include <json-c/json.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#define FRG_CANONICAL_HEADERS_MAX 10

static inline bool frg_hex_hash64(const char *s)
{
    if (!s || strlen(s) != 64) return false;
    for (size_t i = 0; i < 64; ++i)
        if (!((s[i] >= '0' && s[i] <= '9') ||
              (s[i] >= 'a' && s[i] <= 'f') ||
              (s[i] >= 'A' && s[i] <= 'F'))) return false;
    return true;
}

static inline bool
frg_json_member(const struct json_object *obj, const char *key,
                enum json_type kind, struct json_object **out)
{
    struct json_object *value = NULL;
    if (!obj || !json_object_is_type(obj, json_type_object) ||
        !json_object_object_get_ex((struct json_object *)obj, key, &value) ||
        !value || !json_object_is_type(value, kind))
        return false;
    *out = value;
    return true;
}

static inline bool
frg_canonical_headers_valid(const struct json_object *headers,
                            uint64_t requested_start, uint64_t requested_end)
{
    if (!headers || !json_object_is_type(headers, json_type_array) ||
        requested_start > requested_end)
        return false;
    const uint64_t gap = requested_end - requested_start;
    if (gap >= FRG_CANONICAL_HEADERS_MAX ||
        json_object_array_length((struct json_object *)headers) != (size_t)(gap + 1))
        return false;

    const char *prior_hash = NULL;
    for (size_t i = 0; i <= (size_t)gap; ++i)
    {
        struct json_object *item = json_object_array_get_idx(
            (struct json_object *)headers, i);
        struct json_object *height = NULL, *difficulty = NULL;
        struct json_object *timestamp = NULL, *reward = NULL;
        struct json_object *hash_obj = NULL, *parent_obj = NULL, *orphan = NULL;
        if (!frg_json_member(item, "height", json_type_int, &height) ||
            !frg_json_member(item, "difficulty", json_type_int, &difficulty) ||
            !frg_json_member(item, "timestamp", json_type_int, &timestamp) ||
            !frg_json_member(item, "reward", json_type_int, &reward) ||
            !frg_json_member(item, "hash", json_type_string, &hash_obj) ||
            !frg_json_member(item, "prev_hash", json_type_string, &parent_obj) ||
            !frg_json_member(item, "orphan_status", json_type_boolean, &orphan))
            return false;
        const int64_t h = json_object_get_int64(height);
        if (h < 0 || (uint64_t)h != requested_start + (uint64_t)i ||
            json_object_get_int64(difficulty) <= 0 ||
            json_object_get_int64(timestamp) < 0 ||
            json_object_get_int64(reward) < 0)
            return false;
        const char *hash = json_object_get_string(hash_obj);
        const char *parent = json_object_get_string(parent_obj);
        if (!frg_hex_hash64(hash) || !frg_hex_hash64(parent) ||
            (prior_hash && strcmp(parent, prior_hash)))
            return false;
        prior_hash = hash;
    }
    return true;
}

#endif
