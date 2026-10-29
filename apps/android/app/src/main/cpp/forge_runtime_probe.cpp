#include <jni.h>
#include <cstdint>
#include <string>

// This is only an ARM64 JNI link/load acceptance probe.
// No FRG spend keys, wallet functions, RandomX or consensus code is linked.
extern "C" JNIEXPORT jstring JNICALL
Java_org_forgecoin_p2ptest_NativeRuntimeProbe_nativeCapabilities(JNIEnv* env, jclass) {
#if defined(__aarch64__)
    const char* architecture = "arm64-v8a";
#else
    const char* architecture = "unsupported-architecture";
#endif
    const std::string result =
        std::string("JNI probe ABI: ") + architecture +
        "\\nNative FRG wallet: NOT LINKED"
        "\\nNative FRG signing: NOT LINKED"
        "\\nNative RandomX miner: NOT LINKED"
        "\\nFRG chain acceptance: NOT VERIFIED";
    return env->NewStringUTF(result.c_str());
}
