#include <jni.h>
#include <randomx.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <memory>
#include <mutex>
#include <vector>

// Isolated RandomX hash primitive, not a miner. No network, nonce search or block submission.
// Cache initialization is expensive. Serialize per-call light VMs to bound peak memory pressure.
namespace {
std::mutex mutex;
struct CacheDeleter { void operator()(randomx_cache* p) const { if(p) randomx_release_cache(p); } };
struct VMDeleter { void operator()(randomx_vm* p) const { if(p) randomx_destroy_vm(p); } };
}
extern "C" JNIEXPORT jbyteArray JNICALL
Java_org_forgecoin_p2ptest_NativeRandomX_hashLight(JNIEnv* env, jclass,
                                                    jbyteArray keyArray, jbyteArray inputArray) {
    if (!keyArray || !inputArray) return nullptr;
    jsize keyLen=env->GetArrayLength(keyArray), inputLen=env->GetArrayLength(inputArray);
    if (keyLen < 1 || keyLen > 128 || inputLen < 1 || inputLen > 256) return nullptr;
    std::vector<uint8_t> key(static_cast<size_t>(keyLen)), input(static_cast<size_t>(inputLen));
    env->GetByteArrayRegion(keyArray,0,keyLen,reinterpret_cast<jbyte*>(key.data()));
    env->GetByteArrayRegion(inputArray,0,inputLen,reinterpret_cast<jbyte*>(input.data()));
    if (env->ExceptionCheck()) return nullptr;
    std::lock_guard<std::mutex> lock(mutex);
    std::unique_ptr<randomx_cache,CacheDeleter> cache(randomx_alloc_cache(RANDOMX_FLAG_DEFAULT));
    if (!cache) return nullptr;
    randomx_init_cache(cache.get(),key.data(),key.size());
    std::unique_ptr<randomx_vm,VMDeleter> vm(randomx_create_vm(RANDOMX_FLAG_DEFAULT,cache.get(),nullptr));
    if (!vm) return nullptr;
    std::array<uint8_t,RANDOMX_HASH_SIZE> digest{};
    randomx_calculate_hash(vm.get(),input.data(),input.size(),digest.data());
    jbyteArray output=env->NewByteArray(static_cast<jsize>(digest.size()));
    if (output) env->SetByteArrayRegion(output,0,static_cast<jsize>(digest.size()),
                                        reinterpret_cast<const jbyte*>(digest.data()));
    std::fill(key.begin(),key.end(),0);
    std::fill(input.begin(),input.end(),0);
    return output;
}
