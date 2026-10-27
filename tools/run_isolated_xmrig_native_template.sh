#!/bin/bash
# Explicitly disposable, unprivileged client: no daemon or public network.
set -euo pipefail
if [ "$#" -ne 2 ]; then echo "usage: runner PRIVATE_CAPTURE PRIVATE_CANDIDATE" >&2; exit 2; fi
CAPTURE="$1"
OUTPUT="$2"
case "$CAPTURE" in /mnt/c/Users/*/AppData/Local/ForgeCoin/IsolatedTemplateCaptures/*/native-template.json) ;; *) echo "refusing non-private template" >&2; exit 2;; esac
case "$OUTPUT" in /mnt/c/Users/*/AppData/Local/ForgeCoin/IsolatedTemplateCaptures/*/xmrig-miner-candidate.json) ;; *) echo "refusing non-private output" >&2; exit 2;; esac
[ ! -e "$OUTPUT" ] || { echo "candidate already exists" >&2; exit 2; }
REPO="$(cd "$(dirname "$0")/.." && pwd -P)"
XMRIG=/tmp/forgecoin-xmrig-run/xmrig-notls
WORKER=/tmp/forgecoin-xmrig-run/randomx_worker
echo '391f766cadc49f4cb349e680b363994147af54651235fb51d5b1219f33fbd24e  /tmp/forgecoin-xmrig-run/xmrig-notls' | sha256sum --check --status
echo '5be16e696e17f6214c07243522672d905945ec01990b5baa0b29e0e8a363a77b  /tmp/forgecoin-xmrig-run/randomx_worker' | sha256sum --check --status
cd "$REPO"
unshare --net -- /bin/bash -c 'ip link set lo up && exec setpriv --reuid 65534 --regid 65534 --clear-groups --no-new-privs env PYTHONPATH="$1" python3 -m services.pool_research.tests.run_xmrig_native_template --capture "$2" --output "$3" --xmrig /tmp/forgecoin-xmrig-run/xmrig-notls --worker /tmp/forgecoin-xmrig-run/randomx_worker --xmrig-sha256 391f766cadc49f4cb349e680b363994147af54651235fb51d5b1219f33fbd24e --worker-sha256 5be16e696e17f6214c07243522672d905945ec01990b5baa0b29e0e8a363a77b' isolated "$REPO" "$CAPTURE" "$OUTPUT"
