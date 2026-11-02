/* Strict native JSON-C canonical range acceptance regression.
 * No daemon, remote RPC, ledger, payouts or network access.
 */
#include <assert.h>
#include <json-c/json.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../jtgrassie/src/frg_canonical_headers.h"

static void hash_for(int i, char result[65])
{
    memset(result, 'a', 64);
    result[63] = "0123456789abcdef"[i & 15];
    result[64] = 0;
}

static json_object * make_headers(uint64_t first, size_t count)
{
    json_object *headers = json_object_new_array();
    assert(headers);
    for (size_t i = 0; i < count; ++i)
    {
        char hash[65], prev[65];
        hash_for((int)i, hash);
        hash_for((int)i - 1, prev);
        json_object *item = json_object_new_object();
        json_object_object_add(item, "height", json_object_new_int64((int64_t)(first+i)));
        json_object_object_add(item, "difficulty", json_object_new_int64(500000));
        json_object_object_add(item, "timestamp", json_object_new_int64(1720000000+(int64_t)i));
        json_object_object_add(item, "reward", json_object_new_int64(20000000));
        json_object_object_add(item, "hash", json_object_new_string(hash));
        json_object_object_add(item, "prev_hash", json_object_new_string(prev));
        json_object_object_add(item, "orphan_status", json_object_new_boolean(0));
        json_object_array_add(headers, item);
    }
    return headers;
}

static void test_range_length_and_position(void)
{
    json_object *valid = make_headers(100, 10);
    assert(frg_canonical_headers_valid(valid, 100, 109));
    assert(!frg_canonical_headers_valid(valid, 99, 108));
    assert(!frg_canonical_headers_valid(valid, 100, 110));
    assert(!frg_canonical_headers_valid(valid, 100, 108));
    assert(!frg_canonical_headers_valid(valid, 109, 100));
    assert(!frg_canonical_headers_valid(valid, UINT64_MAX-9, UINT64_MAX));
    assert(!frg_canonical_headers_valid(NULL, 100, 109));
    json_object_put(valid);

    json_object *short_range = make_headers(100, 9);
    assert(!frg_canonical_headers_valid(short_range, 100, 109));
    json_object_put(short_range);

    json_object *oversized = make_headers(100, 11);
    assert(!frg_canonical_headers_valid(oversized, 100, 109));
    json_object_put(oversized);

    json_object *single = make_headers(100, 1);
    assert(frg_canonical_headers_valid(single, 100, 100));
    json_object_put(single);
}

static void test_chain_and_fields(void)
{
    json_object *valid = make_headers(100, 10);
    json_object *item = json_object_array_get_idx(valid, 4);
    json_object_object_add(item, "prev_hash", json_object_new_string("deadbeef"));
    assert(!frg_canonical_headers_valid(valid, 100, 109));
    json_object_put(valid);

    valid = make_headers(100, 10);
    item = json_object_array_get_idx(valid, 5);
    json_object_object_add(item, "height", json_object_new_int64(104));
    assert(!frg_canonical_headers_valid(valid, 100, 109));
    json_object_put(valid);

    valid = make_headers(100, 10);
    item = json_object_array_get_idx(valid, 1);
    json_object_object_del(item, "orphan_status");
    assert(!frg_canonical_headers_valid(valid, 100, 109));
    json_object_put(valid);

    valid = make_headers(100, 10);
    item = json_object_array_get_idx(valid, 1);
    json_object_object_add(item, "orphan_status", json_object_new_int(0));
    assert(!frg_canonical_headers_valid(valid, 100, 109));
    json_object_put(valid);

    valid = make_headers(100, 10);
    item = json_object_array_get_idx(valid, 2);
    json_object_object_add(item, "difficulty", json_object_new_int64(0));
    assert(!frg_canonical_headers_valid(valid, 100, 109));
    json_object_put(valid);

    valid = make_headers(100, 10);
    item = json_object_array_get_idx(valid, 2);
    json_object_object_add(item, "reward", json_object_new_int64(-1));
    assert(!frg_canonical_headers_valid(valid, 100, 109));
    json_object_put(valid);

    valid = make_headers(100, 10);
    item = json_object_array_get_idx(valid, 2);
    json_object_object_add(item, "timestamp", json_object_new_string("wrong"));
    assert(!frg_canonical_headers_valid(valid, 100, 109));
    json_object_put(valid);

    valid = make_headers(100, 10);
    item = json_object_array_get_idx(valid, 2);
    json_object_object_add(item, "hash", json_object_new_string("not-hex"));
    assert(!frg_canonical_headers_valid(valid, 100, 109));
    json_object_put(valid);
}

int main(void)
{
    test_range_length_and_position();
    test_chain_and_fields();
    puts("PASS: daemon canonical range exact size, anchored heights, hash linkage, typed headers");
    return 0;
}
