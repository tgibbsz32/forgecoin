#!/bin/sh
set -eu
# Disabled for the frozen 20261026 FRG mainnet: the historical installer would
# replace Oracle's working HTTPS + /pool nginx configuration with HTTP-only nginx
# and conflate a live-node smoke with prelaunch acceptance.
printf '%s\n' 'Legacy explorer installer DISABLED. Preserve the current Oracle HTTPS routing and frozen FRG daemon.' 'Use README.md and the reviewed, hash-pinned Oracle prelaunch deployment runbook; do not activate mining.' >&2
exit 2
