// Android adapter for the CURRENT repository's wallet_api. No alternate key derivation.
#include <jni.h>
#include "wallet/api/wallet2_api.h"
#include <map>
#include <mutex>
#include <stdexcept>
#include <string>
#include <cstring>
#include <sys/stat.h>
#include <unistd.h>

namespace {
std::mutex guard;
std::map<jlong, Monero::Wallet*> wallets;
std::map<jlong, int> syncedPorts;
std::map<jlong, Monero::PendingTransaction*> prepared;
void discardPrepared(jlong id, Monero::Wallet* wallet) {
    auto it=prepared.find(id);
    if(it!=prepared.end()) {
        wallet->disposeTransaction(it->second);
        prepared.erase(it);
    }
}
jlong nextId = 1;
struct Secret {
    std::string bytes;
    Secret(JNIEnv* e, jbyteArray a) {
        if (!a || e->GetArrayLength(a) < 12 || e->GetArrayLength(a) > 1024)
            throw std::invalid_argument("Wallet password must contain 12-1024 UTF-8 bytes");
        bytes.resize(e->GetArrayLength(a));
        e->GetByteArrayRegion(a, 0, bytes.size(), reinterpret_cast<jbyte*>(&bytes[0]));
        if (e->ExceptionCheck()) throw std::runtime_error("Unable to read password");
    }
    ~Secret() { volatile char* p = bytes.empty() ? nullptr : &bytes[0];
        for (size_t i=0; i<bytes.size(); ++i) p[i]=0; }
};
std::string text(JNIEnv* e, jstring s) {
    if (!s) throw std::invalid_argument("Missing argument");
    const char* p=e->GetStringUTFChars(s,nullptr);
    if (!p) throw std::runtime_error("Unable to read text");
    std::string value(p); e->ReleaseStringUTFChars(s,p); return value;
}
void fail(JNIEnv* e, const char* message) {
    if (!e->ExceptionCheck()) e->ThrowNew(e->FindClass("java/lang/IllegalStateException"),message);
}
Monero::WalletManager* manager() { return Monero::WalletManagerFactory::getWalletManager(); }
Monero::Wallet* get(jlong id) {
    auto it=wallets.find(id);
    if(it==wallets.end()) throw std::invalid_argument("Wallet session closed");
    return it->second;
}
void check(Monero::Wallet* w) {
    if(!w || w->status()!=Monero::Wallet::Status_Ok)
        throw std::runtime_error("Native wallet operation failed");
}
void unusedPath(const std::string& path) {
    struct stat st{};
    // The Java controller supplies an app-private absolute path. Refuse ANY
    // existing wallet/cache/key file, including a partial prior creation.
    if(path.empty() || path[0]!='/' || path.find("/../")!=std::string::npos)
        throw std::invalid_argument("Absolute private wallet path required");
    for(const auto& suffix: {"", ".keys", ".address.txt"})
        if(lstat((path+suffix).c_str(),&st)==0)
            throw std::invalid_argument("Wallet already exists; restore to a new path");
}
jlong retain(Monero::Wallet* w) {
    try { check(w); if(!w->store("")) throw std::runtime_error("Wallet storage failed"); }
    catch(...) { if(w) manager()->closeWallet(w,false); throw; }
    jlong id=nextId++; wallets.emplace(id,w); return id;
}
}

// One global lock protects wallet_api lifetime and all access; no Java handle
// is ever a raw pointer. Failures never return placeholder addresses/balances.
extern "C" JNIEXPORT jlong JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_create(JNIEnv* e,jclass,jstring path,jbyteArray password) {
    std::lock_guard<std::mutex> lock(guard);
    try {
        auto p=text(e,path); unusedPath(p); Secret pw(e,password);
        auto* w=manager()->createWallet(p,pw.bytes,"English",Monero::MAINNET);
        // An offline-created wallet has no trusted creation height.
        if(w && w->status()==Monero::Wallet::Status_Ok)w->setRefreshFromBlockHeight(0);
        return retain(w);
    } catch(...) { fail(e,"Native FRG wallet creation failed; check private storage/password"); return 0; }
}
extern "C" JNIEXPORT jlong JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_restore(JNIEnv* e,jclass,jstring path,jbyteArray password,jstring seed,jlong height) {
    std::lock_guard<std::mutex> lock(guard);
    try {
        if(height<0) throw std::invalid_argument("Invalid restore height");
        auto p=text(e,path); unusedPath(p); Secret pw(e,password);
        auto phrase=text(e,seed);
        Monero::Wallet* w=nullptr;
        try { w=manager()->recoveryWallet(p,pw.bytes,phrase,Monero::MAINNET,static_cast<uint64_t>(height)); }
        catch(...) { volatile char* q=phrase.empty()?nullptr:&phrase[0]; for(size_t i=0;i<phrase.size();++i)q[i]=0; throw; }
        volatile char* q=phrase.empty()?nullptr:&phrase[0]; for(size_t i=0;i<phrase.size();++i)q[i]=0;
        return retain(w);
    } catch(...) { fail(e,"Native FRG restoration failed; verify seed/checksum and destination"); return 0; }
}
extern "C" JNIEXPORT jlong JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_open(JNIEnv* e,jclass,jstring path,jbyteArray password) {
    std::lock_guard<std::mutex> lock(guard);
    try {
        Secret pw(e,password);
        auto* w=manager()->openWallet(text(e,path),pw.bytes,Monero::MAINNET);
        try { check(w); } catch(...) { if(w)manager()->closeWallet(w,false); throw; }
        jlong id=nextId++; wallets.emplace(id,w); return id;
    } catch(...) { fail(e,"Native FRG unlock failed; wallet was not opened"); return 0; }
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_address(JNIEnv* e,jclass,jlong id) {
    std::lock_guard<std::mutex> lock(guard);
    try { auto s=get(id)->address(); return e->NewStringUTF(s.c_str()); }
    catch(...) { fail(e,"No open native wallet"); return nullptr; }
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_seed(JNIEnv* e,jclass,jlong id) {
    std::lock_guard<std::mutex> lock(guard);
    try {
        auto s=get(id)->seed(); auto out=e->NewStringUTF(s.c_str());
        volatile char* p=s.empty()?nullptr:&s[0]; for(size_t i=0;i<s.size();++i)p[i]=0;
        return out;
    } catch(...) { fail(e,"Native recovery phrase unavailable"); return nullptr; }
}
extern "C" JNIEXPORT void JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_close(JNIEnv* e,jclass,jlong id) {
    std::lock_guard<std::mutex> lock(guard);
    try {
        auto* w=get(id);
        // Store explicitly before close, retaining the handle on storage failure.
        if(!w->store("")) throw std::runtime_error("Unable to save wallet");
        discardPrepared(id,w);
        syncedPorts.erase(id);
        wallets.erase(id);
        if(!manager()->closeWallet(w,false)) throw std::runtime_error("Unable to close wallet");
    } catch(...) { fail(e,"Native FRG wallet close failed"); }
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_snapshot(JNIEnv* e,jclass,jlong id) {
    std::lock_guard<std::mutex> lock(guard);
    try {
        auto* w=get(id);
        auto s=std::to_string(w->balance())+":"+std::to_string(w->unlockedBalance())+":"+std::to_string(w->blockChainHeight());
        return e->NewStringUTF(s.c_str());
    } catch(...) { fail(e,"Native wallet balance unavailable"); return nullptr; }
}
// This library is staged only in the debug variant. The Java boundary
// checks the disposable node's nettype and genesis before entering JNI.
extern "C" JNIEXPORT jstring JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_refreshLocal(JNIEnv* e,jclass,jlong id,jint port) {
    std::lock_guard<std::mutex> lock(guard);
    try {
        if(port<1024 || port>65535) throw std::invalid_argument("Invalid isolated node port");
        auto* w=get(id);
        discardPrepared(id,w);
        syncedPorts.erase(id);
        if(!w->init("127.0.0.1:"+std::to_string(port)) || !w->refresh())
            throw std::runtime_error("Native wallet refresh failed");
        check(w);
        syncedPorts.emplace(id,port);
        auto s=std::to_string(w->balance())+":"+std::to_string(w->unlockedBalance())+":"+std::to_string(w->blockChainHeight());
        return e->NewStringUTF(s.c_str());
    } catch(...) { fail(e,"Unable to synchronize the native wallet with the isolated node"); return nullptr; }
}
// No release variant includes this library. Prepare and commit are separate,
// and the debug caller revalidates the disposable node before each step.
extern "C" JNIEXPORT jstring JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_prepareLocal(JNIEnv* e,jclass,jlong id,jint port,jstring recipient,jlong amount) {
    std::lock_guard<std::mutex> lock(guard);
    try {
        auto* w=get(id);
        discardPrepared(id,w);
        auto node=syncedPorts.find(id);
        auto address=text(e,recipient);
        if(node==syncedPorts.end() || node->second!=port || amount<=0 ||
            !Monero::Wallet::addressValid(address,Monero::MAINNET) ||
            static_cast<uint64_t>(amount)>w->unlockedBalance())
            throw std::invalid_argument("Fresh scan, valid address and unlocked FRG required");
        auto* tx=w->createTransaction(address,"",Monero::optional<uint64_t>(static_cast<uint64_t>(amount)),0);
        if(!tx)throw std::runtime_error("Native wallet returned no transaction");
        try {
            if(tx->status()!=Monero::PendingTransaction::Status_Ok ||
                tx->txCount()!=1 || tx->amount()!=static_cast<uint64_t>(amount))
                throw std::runtime_error("Native wallet could not prepare an exact single transaction");
            auto quote=std::to_string(tx->amount())+":"+std::to_string(tx->fee());
            auto out=e->NewStringUTF(quote.c_str());
            if(!out)throw std::runtime_error("Unable to return transaction quote");
            prepared.emplace(id,tx);
            return out;
        } catch(...) { w->disposeTransaction(tx);throw; }
    } catch(...) { fail(e,"Unable to prepare native FRG transaction on the isolated chain");return nullptr; }
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_commitLocal(JNIEnv* e,jclass,jlong id,jint port) {
    std::lock_guard<std::mutex> lock(guard);
    try {
        auto* w=get(id);
        auto node=syncedPorts.find(id);
        auto pending=prepared.find(id);
        if(node==syncedPorts.end() || node->second!=port || pending==prepared.end())
            throw std::invalid_argument("Confirmed transaction and matching isolated node required");
        try {
            auto hashes=pending->second->txid();
            if(hashes.size()!=1 || hashes[0].size()!=64)
                throw std::runtime_error("Expected a single native transaction hash");
            // Allocate the receipt before broadcast so Java allocation failure
            // cannot be confused with a failed submission.
            auto receipt=e->NewStringUTF(hashes[0].c_str());
            if(!receipt || !pending->second->commit())throw std::runtime_error("Native broadcast failed");
            discardPrepared(id,w);
            return receipt;
        } catch(...) { discardPrepared(id,w);throw; }
    } catch(...) { fail(e,"No isolated transaction acknowledgment; synchronize before retrying");return nullptr; }
}
extern "C" JNIEXPORT void JNICALL
Java_org_forgecoin_p2ptest_NativeFrgWallet_cancelLocal(JNIEnv* e,jclass,jlong id) {
    std::lock_guard<std::mutex> lock(guard);
    try { discardPrepared(id,get(id)); }
    catch(...) { fail(e,"Wallet session closed"); }
}
