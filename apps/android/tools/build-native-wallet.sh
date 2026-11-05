#!/bin/bash
set -euo pipefail
TASK_ROOT="${FORGE_ANDROID_BUILD_ROOT:-/root/forgecoin-android-20261105}"
SOURCE="${FORGE_ANDROID_SOURCE:-/mnt/d/ForgeCoin-Android-20261105-Build}"
# depends must already have succeeded. Keep its verified cache and never
# overwrite it while a dependency build is running.
cd "$TASK_ROOT/source"
mkdir -p apps/android/native-wallet apps/android/app/src/main/cpp
cp "$SOURCE/apps/android/native-wallet/CMakeLists.txt" apps/android/native-wallet/
cp "$SOURCE/apps/android/app/src/main/cpp/wallet_bridge.cpp" apps/android/app/src/main/cpp/
PREFIX="$TASK_ROOT/source/contrib/depends/aarch64-linux-android"
export PATH="$PREFIX/native/bin:$PATH"
cmake -S apps/android/native-wallet -B "$TASK_ROOT/wallet-build" \
    -DCMAKE_TOOLCHAIN_FILE="$PREFIX/share/toolchain.cmake" \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DANDROID_STL=c++_static \
    -DCMAKE_SHARED_LINKER_FLAGS="-static-libstdc++ -Wl,-z,max-page-size=16384" \
    -DBOOST_IGNORE_SYSTEM_PATHS=ON -DUSE_CCACHE=OFF \
    -DMANUAL_SUBMODULES=ON -DPYTHON_EXECUTABLE=/usr/bin/python3
cmake --build "$TASK_ROOT/wallet-build" --target forge_wallet -j2
# Only stage after a successful linker result.
mkdir -p "$SOURCE/apps/android/app/src/debug/jniLibs/arm64-v8a"
cp "$TASK_ROOT/wallet-build/libforge_wallet.so" "$SOURCE/apps/android/app/src/debug/jniLibs/arm64-v8a/"
sha256sum "$SOURCE/apps/android/app/src/debug/jniLibs/arm64-v8a/libforge_wallet.so"
