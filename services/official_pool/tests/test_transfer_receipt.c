/* Wallet RPC fixture-based acceptance tests: no spending keys, chain or network. */
#include <assert.h>
#include <json-c/json.h>
#include <stdio.h>
#include "../jtgrassie/src/frg_transfer_receipt.h"

static int check(const char *text) {
    struct json_object *root=json_tokener_parse(text);
    int ok=frg_transfer_receipt_valid(root);
    if(root) json_object_put(root);
    return ok;
}
int main(void) {
    const char *tx="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    char input[4096];
    snprintf(input,sizeof(input),"{\"result\":{\"tx_hash_list\":[\"%s\"]}}",tx);
    assert(check(input)==1);
    snprintf(input,sizeof(input),"{\"result\":{\"tx_hash_list\":[\"%s\",\"%s\"]}}",tx,tx);
    assert(check(input)==1);
    assert(check("{\"error\":{\"code\":-1,\"message\":\"rejected\"},\"result\":{\"tx_hash_list\":[\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\"]}}")==0);
    assert(check("{\"result\":{}}")==0);
    assert(check("{\"result\":{\"tx_hash_list\":[]}}")==0);
    assert(check("{\"result\":{\"tx_hash_list\":[\"123\"]}}")==0);
    assert(check("{\"result\":{\"tx_hash_list\":[123]}}")==0);
    assert(check("{\"result\":{\"tx_hash_list\":null}}")==0);
    assert(check("{\"result\":{\"tx_hash_list\":[\"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz\"]}}")==0);
    assert(check("garbage")==0);
    assert(check("null")==0);
    assert(check("{}")==0);
    puts("PASS: native wallet transfer receipt fixtures reject errors and malformed confirmations");
    return 0;
}
