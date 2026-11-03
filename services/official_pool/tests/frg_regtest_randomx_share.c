/* One genuine RandomX result for a disposable ForgeCoin FAKECHAIN Stratum job.
 *
 * NO sockets, no private keys, no daemon, no wallet, no payouts, no persistent
 * files. Input must be a public 32-byte seed and a pool-issued hashing blob.
 * The Python integration runner alone restricts the destination to localhost
 * and the daemon identity to --regtest / FAKECHAIN.
 *
 * Usage: frg-regtest-share PUBLIC_SEED_HASH_HEX STRATUM_HASHING_BLOB_HEX
 * Output: <8 hex bytes nonce><space><64 hex bytes native RandomX hash>
 */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "randomx.h"

#define MAX_BLOB 4096
#define NONCE_OFFSET 39

static int from_hex(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
static int decode_hex(const char *hex, unsigned char *out, size_t capacity,
                      size_t *len_out)
{
    size_t length = strlen(hex);
    if ((length & 1) || length / 2 > capacity || !length) return -1;
    for (size_t i = 0; i < length / 2; ++i)
    {
        int upper = from_hex(hex[2 * i]);
        int lower = from_hex(hex[2 * i + 1]);
        if (upper < 0 || lower < 0) return -1;
        out[i] = (unsigned char)((upper << 4) | lower);
    }
    *len_out = length / 2;
    return 0;
}
int main(int argc, char **argv)
{
    if (argc != 3) { fputs("two public hex arguments required\n", stderr); return 2; }
    unsigned char seed[32], blob[MAX_BLOB], hash[RANDOMX_HASH_SIZE];
    size_t seed_len = 0, blob_len = 0;
    if (decode_hex(argv[1], seed, sizeof(seed), &seed_len) ||
        decode_hex(argv[2], blob, sizeof(blob), &blob_len) ||
        seed_len != sizeof(seed) || blob_len <= NONCE_OFFSET + 4 ||
        blob_len < 60)
    {
        fputs("invalid public RandomX seed or hashing blob\n", stderr);
        return 2;
    }
    /* Deterministic candidate, difficulty-one FAKECHAIN only.
     * Encode little endian bytes directly in the native hashing blob.
     */
    uint32_t candidate = 1;
    for (size_t i = 0; i < 4; ++i)
        blob[NONCE_OFFSET + i] = (unsigned char)((candidate >> (i * 8)) & 255u);

    randomx_cache *cache = randomx_alloc_cache(RANDOMX_FLAG_DEFAULT);
    if (!cache) { fputs("RandomX cache allocation failed\n", stderr); return 3; }
    randomx_init_cache(cache, seed, sizeof(seed));
    randomx_vm *vm = randomx_create_vm(RANDOMX_FLAG_DEFAULT, cache, NULL);
    if (!vm)
    {
        fputs("RandomX VM allocation failed\n", stderr);
        randomx_release_cache(cache);
        return 3;
    }
    randomx_calculate_hash(vm, blob, blob_len, hash);
    for (size_t i = 0; i < 4; ++i)
        printf("%02x", blob[NONCE_OFFSET + i]);
    putchar(' ');
    for (size_t i = 0; i < sizeof(hash); ++i)
        printf("%02x", hash[i]);
    putchar('\n');

    randomx_destroy_vm(vm);
    randomx_release_cache(cache);
    return 0;
}
