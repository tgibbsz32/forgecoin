/* Strict native FRG transfer_split receipt verification.
 * Fails closed on wallet RPC errors and missing/invalid transaction IDs.
 * This is necessary but NOT sufficient evidence of on-chain confirmation.
 */
#ifndef FRG_TRANSFER_RECEIPT_H
#define FRG_TRANSFER_RECEIPT_H
#include <json-c/json.h>
#include <stddef.h>

static inline int frg_receipt_valid_txid(const char *hash) {
    if (!hash) return 0;
    for (size_t i=0; i<64; ++i) {
        unsigned char c=(unsigned char)hash[i];
        if (!c || !((c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F')))
            return 0;
    }
    return hash[64]=='\0';
}
static inline int frg_transfer_receipt_valid(const struct json_object *root) {
    if (!root || !json_object_is_type(root,json_type_object)) return 0;
    struct json_object *error=NULL;
    if (json_object_object_get_ex((struct json_object *)root,"error",&error) &&
        error && !json_object_is_type(error,json_type_null)) return 0;
    struct json_object *result=NULL,*hashes=NULL;
    if (!json_object_object_get_ex((struct json_object *)root,"result",&result) ||
        !json_object_is_type(result,json_type_object) ||
        !json_object_object_get_ex(result,"tx_hash_list",&hashes) ||
        !json_object_is_type(hashes,json_type_array)) return 0;
    size_t count=json_object_array_length(hashes);
    if (count==0 || count>128) return 0;
    for(size_t i=0;i<count;++i) {
        struct json_object *entry=json_object_array_get_idx(hashes,i);
        if (!entry || !json_object_is_type(entry,json_type_string) ||
            !frg_receipt_valid_txid(json_object_get_string(entry))) return 0;
    }
    return 1;
}
#endif
