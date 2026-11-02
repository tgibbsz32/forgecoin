/* Native json-c daemon submit_block acknowledgement regression fixture. */
#include <assert.h>
#include <json-c/json.h>
#include <stdio.h>
#include "../jtgrassie/src/frg_block_submit_receipt.h"

static void probe(const char *json, int expected)
{
    json_object *root=json_tokener_parse(json);
    int result=frg_block_submission_rpc_accepted(root);
    if (root) json_object_put(root);
    if(result!=expected){
        fprintf(stderr,"RPC submitted candidate validation mismatch for fixture\n");
        assert(result==expected);
    }
}
int main(void)
{
    probe("{\"jsonrpc\":\"2.0\",\"id\":\"0\",\"result\":{\"status\":\"OK\"}}",1);
    probe("{\"result\":{\"status\":\"OK\"},\"error\":null}",1);
    probe("{\"result\":{\"status\":\"ERROR\"}}",0);
    probe("{\"error\":{\"code\":-7,\"message\":\"invalid block\"},\"result\":{\"status\":\"OK\"}}",0);
    probe("{\"error\":\"rejected\",\"result\":{\"status\":\"OK\"}}",0);
    probe("{\"error\":false,\"result\":{\"status\":\"OK\"}}",0);
    probe("{\"result\":{\"status\":null}}",0);
    probe("{\"result\":{\"status\":true}}",0);
    probe("{\"result\":{\"status\":1}}",0);
    probe("{\"result\":{\"status\":\"ok\"}}",0);
    probe("{\"result\":{\"status\":\"OK \",\"untrusted\":\"ignored\"}}",0);
    probe("{\"result\":{}}",0);
    probe("{\"result\":[]}",0);
    probe("{\"status\":\"OK\"}",0);
    probe("{\"result\":null}",0);
    probe("null",0);
    probe("{broken",0);
    assert(frg_block_submission_rpc_accepted(NULL)==0);
    puts("PASS: native FRG JSON-RPC block acceptance requires error-free OK response; rejects 17 malformed/failure fixtures");
    return 0;
}
