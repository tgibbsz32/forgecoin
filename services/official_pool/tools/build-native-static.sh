#!/usr/bin/env bash
# Build the reviewed native ForgeCoin static archives, not the pool executable.
# Safe for isolated Linux/WSL x86_64 and native Oracle ARM64 staging builders.
# Never starts a daemon, Stratum, wallet, or payout service.
set -Eeuo pipefail

usage() {
  echo "Usage: $0 SOURCE_ROOT BUILD_DIR EXPECTED_SOURCE_SHA" >&2
  echo "The source must be a CLEAN isolated ForgeCoin git checkout." >&2
  exit 64
}
[[ $# -eq 3 ]] || usage
command -v cmake >/dev/null || { echo "cmake not installed" >&2; exit 65; }
command -v git >/dev/null || { echo "git not installed" >&2; exit 65; }
source_root=$(realpath -e "$1")
build_root=$(realpath -m "$2")
expected_sha=$3
[[ "$expected_sha" =~ ^[0-9a-f]{40}$ ]] || { echo "40-character lowercase commit SHA required" >&2; exit 65; }
[[ -f "$source_root/src/cryptonote_config.h" ]] ||
  { echo "not a ForgeCoin consensus source checkout" >&2; exit 65; }
[[ -f "$source_root/services/official_pool/jtgrassie/Makefile" ]] ||
  { echo "reviewed native pool backend missing" >&2; exit 65; }
actual_sha=$(git -C "$source_root" rev-parse HEAD)
[[ "$actual_sha" == "$expected_sha" ]] ||
  { echo "source commit mismatch: actual $actual_sha" >&2; exit 66; }
# Fail instead of compiling unreviewed local consensus changes.
[[ -z "$(git -C "$source_root" status --porcelain --untracked-files=no)" ]] ||
  { echo "source has uncommitted tracked changes; use a clean isolated checkout" >&2; exit 66; }
[[ "$build_root" != "$source_root" && "$build_root" == "$source_root"/* ]] ||
  { echo "build directory must be under the isolated source root" >&2; exit 66; }
case "$(uname -m)" in
  x86_64|aarch64) ;;
  *) echo "unsupported architecture: $(uname -m)" >&2; exit 66 ;;
esac

# This exact WSL builder previously became unresponsive with 8 compilation
# jobs and 1.9 GiB RAM. Default to one job, and reject excessive concurrency
# on small hosts rather than destabilizing the user's computer/Oracle node.
jobs=${FRG_BUILD_JOBS:-1}
[[ "$jobs" =~ ^[1-9][0-9]*$ && "$jobs" -le 8 ]] ||
  { echo "FRG_BUILD_JOBS must be 1 through 8" >&2; exit 66; }
total_kib=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
if (( total_kib < 4 * 1024 * 1024 && jobs > 1 )); then
  echo "under 4 GiB RAM: only FRG_BUILD_JOBS=1 is allowed" >&2
  exit 66
fi
if (( total_kib < 8 * 1024 * 1024 && jobs > 2 )); then
  echo "under 8 GiB RAM: FRG_BUILD_JOBS must be <=2" >&2
  exit 66
fi

# Do not blindly reuse a CMake cache pointing to a different source.
if [[ -f "$build_root/CMakeCache.txt" ]]; then
  original=$(sed -n 's/^CMAKE_HOME_DIRECTORY:INTERNAL=//p' "$build_root/CMakeCache.txt")
  [[ "$original" == "$source_root" ]] ||
    { echo "build cache belongs to another checkout: $original" >&2; exit 66; }
fi

echo "FRG source: $actual_sha"
echo "Builder CPU: $(uname -m), RAM: $((total_kib / 1024)) MiB, parallel jobs: $jobs"
echo "No pool daemon, wallet, payouts, mining ports or Oracle deployment will run."

cmake -S "$source_root" -B "$build_root" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF \
  -DBUILD_GUI_DEPS=OFF -DMANUAL_SUBMODULES=1 -DUSE_CCACHE=OFF

# These 11 build targets correspond to the pool's explicitly pinned archive list.
cmake --build "$build_root" --parallel "$jobs" --target \
  cryptonote_basic cncrypto common ringct_basic device \
  cryptonote_format_utils_basic wallet-crypto epee easylogging version randomx

archives=(
  "src/cryptonote_basic/libcryptonote_basic.a"
  "src/crypto/libcncrypto.a"
  "src/common/libcommon.a"
  "src/ringct/libringct_basic.a"
  "src/device/libdevice.a"
  "src/cryptonote_basic/libcryptonote_format_utils_basic.a"
  "src/crypto/wallet/libwallet-crypto.a"
  "contrib/epee/src/libepee.a"
  "external/easylogging++/libeasylogging.a"
  "src/libversion.a"
  "external/randomx/librandomx.a"
)
for lib in "${archives[@]}"; do
  [[ -s "$build_root/$lib" ]] || {
    echo "required native archive missing or empty: $build_root/$lib" >&2
    exit 67
  }
done
printf 'PASS: %d native ForgeCoin archives exist, architecture=%s\n' "${#archives[@]}" "$(uname -m)"
echo "NOT a pool executable; a separate reviewed link and native miner/daemon test is required."
