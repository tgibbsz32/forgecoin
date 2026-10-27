#!/usr/bin/env python3
"""Careful additive deployment to existing Oracle 57-stat pool preview.

This deliberately retains existing pool.html, pool-observer.html, static
metrics logic, images and future account-service integration.
"""
from pathlib import Path
import os
import shutil
import tempfile
from datetime import datetime, timezone

ROOT=Path("/opt/forgecoin-pool/releases/preparation-20261027-v1/pool")
BACKUPS=Path("/home/ubuntu/forgecoin-pool-site-backups")
HOME=ROOT/"index.html"
JS=ROOT/"network-monitor.js"
STAGED=Path("/home/ubuntu/forgecoin-network-monitor-20261027.js")
assert ROOT.is_dir() and HOME.is_file() and STAGED.is_file()
assert "127.0.0.1" not in STAGED.read_text()
original=HOME.read_text(encoding="utf-8")
if "network-monitor.js" in original:
    print("Oracle pool network telemetry is already wired; no changes")
    raise SystemExit(0)
if original.count("</body>") != 1 or original.count('data-poolmetric="networkHeight"') != 1:
    raise SystemExit("Unknown pool website version: refusing deployment")
if "57" not in (Path("/opt/forgecoin-pool/releases/preparation-20261027-v1/manifest.json").read_text()):
    raise SystemExit("Pool manifest changed, refusing replacement")
stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
BACKUPS.mkdir(mode=0o700,parents=True,exist_ok=True)
backup=BACKUPS/("index.html."+stamp)
shutil.copy2(HOME,backup)
shutil.copy2(STAGED,JS)
os.chmod(JS,0o644)
new=original.replace("</body>",'<script src="network-monitor.js" defer></script></body>')
new=new.replace("1% planned</strong>","1% configured</strong>")
with tempfile.NamedTemporaryFile(mode="w",dir=ROOT,delete=False,encoding="utf-8") as tmp:
    tmp.write(new)
    name=tmp.name
os.chmod(name,0o644)
os.replace(name,HOME)
print("Updated existing 57-metric page additively; original backup:",backup)
