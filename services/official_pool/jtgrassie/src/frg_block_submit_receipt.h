/* Strict native ForgeCoin daemon submit_block JSON-RPC acknowledgment.
 * A status "OK" alone is not enough if JSON-RPC reported an error.
 * ACK does NOT independently prove canonical block inclusion.
 */
#ifndef FRG_BLOCK_SUBMIT_RECEIPT_H
#define FRG_BLOCK_SUBMIT_RECEIPT_H
#include <json-c/json.h>
#include <string.h>
static inline int frg_block_submission_rpc_accepted(const struct json_object *root)
{
    if (!root || !json_object_is_type(root,json_type_object)) return 0;
    struct json_object *error=NULL,*result=NULL,*status=NULL;
    if (json_object_object_get_ex((struct json_object*)root,"error",&error) &&
        error && !json_object_is_type(error,json_type_null))return 0;
    if (!json_object_object_get_ex((struct json_object*)root,"result",&result) ||
        !json_object_is_type(result,json_type_object))return 0;
    if (!json_object_object_get_ex(result,"status",&status) ||
        !json_object_is_type(status,json_type_string))return 0;
    const char *value=json_object_get_string(status);
    return value && strcmp(value,"OK")==0;
}
#endif
