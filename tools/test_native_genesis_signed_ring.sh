#!/usr/bin/env bash
# Build signed-ring crypto regression exclusively against the native archives
# produced by the reviewed ForgeCoin consensus build at this exact revision.
# No daemon is launched, wallet key loaded, mining performed, or funds touched.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 ABSOLUTE_NATIVE_BUILD_ROOT" >&2
  exit 2
fi
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build="$(realpath "$1")"
cd "$root"
archives=(
  "$build/src/crypto/libcncrypto.a"
  "$build/src/common/libcommon.a"
  "$build/contrib/epee/src/libepee.a"
  "$build/external/easylogging++/libeasylogging.a"
)
for archive in "${archives[@]}"; do
  if [[ ! -s "$archive" ]]; then
    echo "Cannot validate signed genesis ring without same-build native archive: $archive" >&2
    exit 2
  fi
done
tmp="$(mktemp -d -t frg-genesis-signed-ring-XXXXXXXX)"
trap 'rm -rf "$tmp"' EXIT
g++ -std=c++17 -O2 -Wall -Wextra -Werror -pedantic \
  -Isrc -Icontrib/epee/include -Iexternal -Iexternal/easylogging++ \
  tests/mainnet/genesis_signed_ring_policy.cpp \
  "${archives[@]}" -o "$tmp/genesis-signed-ring" \
  -lsodium -pthread -ldl -lboost_thread -lboost_system -lssl -lcrypto
pubkey="$(python3 tools/extract_frozen_genesis_output_key.py)"
if [[ ! "$pubkey" =~ ^[0-9a-f]{64}$ ]]; then
  echo "Frozen genesis public output key extractor returned malformed hex" >&2
  exit 2
fi
"$tmp/genesis-signed-ring" "$pubkey"
