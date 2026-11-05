#!/bin/bash
# Run inside the connected Windows PC's ForgeCoinBuild WSL distribution.
set -euo pipefail
TASK_ROOT="${FORGE_ANDROID_BUILD_ROOT:-/root/forgecoin-android-20261105}"
SOURCE="${FORGE_ANDROID_SOURCE:-/mnt/d/ForgeCoin-Android-20261105-Build}"
# Resume a partial dependency build without re-extracting source or staging
# dependency outputs in its provenance commit. Use a new build root to change input.
if [ -d "$TASK_ROOT/source/.git" ]; then
    cd "$TASK_ROOT/source/contrib/depends"
    make HOST=aarch64-linux-android NO_QT=1 -j4
    exit
fi
mkdir -p "$TASK_ROOT/source"
cd "$SOURCE"
tar -xf apps/android/build/native-source-input.tar -C "$TASK_ROOT/source"
cd "$TASK_ROOT/source"
# Historical repository blobs include CRLF shell/Make inputs. Normalize the
# isolated Linux build copy only, never the Windows checkout.
python3 - <<'PY'
from pathlib import Path
for p in Path('.').rglob('*'):
    if p.is_file() and '.git' not in p.parts:
        b=p.read_bytes()
        if b'\0' not in b and b'\r\n' in b:
            p.write_bytes(b.replace(b'\r\n', b'\n'))
PY
git init -q
git config user.name 'ForgeCoin Android build'
git config user.email 'build@localhost'
git add .
git commit -qm 'Frozen input 7d7f307 for Android dependency compilation'
# Preserve the repository's pinned sources and checksum verification.
cd contrib/depends
make HOST=aarch64-linux-android NO_QT=1 -j4
