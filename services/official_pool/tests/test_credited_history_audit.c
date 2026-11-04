/* Native real json-c historical callback validation; no daemon or wallet. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <json-c/json.h>
#include "../jtgrassie/src/frg_credited_history_audit.h"

static const char HASH[] =
    "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
static const char PARENT[] =
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

static struct json_object *base_header(void)
{
    struct json_object *r = json_object_new_object();
    assert(r);
    json_object_object_add(r, "height", json_object_new_int64(160));
    json_object_object_add(r, "difficulty", json_object_new_int64(500000));
    json_object_object_add(r, "reward", json_object_new_int64(2384185222LL));
    json_object_object_add(r, "timestamp", json_object_new_int64(1800000000));
    json_object_object_add(r, "hash", json_object_new_string(HASH));
    json_object_object_add(r, "prev_hash", json_object_new_string(PARENT));
    json_object_object_add(r, "orphan_status", json_object_new_boolean(0));
    return r;
}
static enum frg_history_verdict verdict(struct json_object *r)
{
    return frg_history_compare(r, 160, HASH, PARENT, 500000, 2384185222ULL);
}
int main(void)
{
    struct json_object *r = base_header();
    assert(verdict(r) == FRG_HISTORY_MATCH);
    json_object_object_add(r, "hash", json_object_new_string(PARENT));
    assert(verdict(r) == FRG_HISTORY_CONFLICT);
    json_object_put(r);

    r = base_header();
    json_object_object_add(r, "prev_hash", json_object_new_string(HASH));
    assert(verdict(r) == FRG_HISTORY_CONFLICT);
    json_object_put(r);

    r = base_header();
    json_object_object_add(r, "orphan_status", json_object_new_boolean(1));
    assert(verdict(r) == FRG_HISTORY_CONFLICT);
    json_object_put(r);

    r = base_header();
    json_object_object_add(r, "difficulty", json_object_new_int64(700000));
    assert(verdict(r) == FRG_HISTORY_UNVERIFIED);
    json_object_put(r);

    r = base_header();
    json_object_object_add(r, "reward", json_object_new_int64(2384185221LL));
    assert(verdict(r) == FRG_HISTORY_UNVERIFIED);
    json_object_put(r);

    r = base_header();
    json_object_object_del(r, "prev_hash");
    assert(verdict(r) == FRG_HISTORY_UNVERIFIED);
    json_object_put(r);

    r = base_header();
    json_object_object_add(r, "hash", json_object_new_string("malformed"));
    assert(verdict(r) == FRG_HISTORY_UNVERIFIED);
    json_object_put(r);

    r = base_header();
    json_object_object_add(r, "height", json_object_new_int64(161));
    assert(verdict(r) == FRG_HISTORY_UNVERIFIED);
    json_object_put(r);

    r = base_header();
    json_object_object_add(r, "timestamp", json_object_new_int64(-1));
    assert(verdict(r) == FRG_HISTORY_UNVERIFIED);
    json_object_put(r);

    r = base_header();
    json_object_object_add(r, "orphan_status", json_object_new_string("false"));
    assert(verdict(r) == FRG_HISTORY_UNVERIFIED);
    json_object_put(r);

    assert(verdict(NULL) == FRG_HISTORY_UNVERIFIED);
    assert(frg_history_compare(base_header(), 160, HASH, PARENT, 0, 2384185222ULL)
           == FRG_HISTORY_UNVERIFIED);
    assert(!frg_history_payout_allowed(false, false, false));
    assert(!frg_history_payout_allowed(false, true, true));
    assert(!frg_history_payout_allowed(true, true, false));
    assert(frg_history_payout_allowed(false, true, false));
    puts("PASS: native credited-history checks distinguish verified match, conflict, malformed/unverified");
    return 0;
}
