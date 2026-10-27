#!/usr/bin/env python3
"""Add a public, GET-only, rate-limited read-only Oracle monitoring route.

Run as root on Oracle, after independently reviewing the target Nginx file.
Only modifies /pool/api/monitor; never changes daemon, miner or payout services.
"""
from pathlib import Path
from shutil import copy2
from datetime import datetime, timezone
import subprocess
import sys

path = Path("/etc/nginx/sites-available/forgecoin-explorer")
original = path.read_text(encoding="utf-8")
anchor = "    location = /pool { return 301 /pool/; }"
location = """
    location = /pool/api/monitor {
        if ($request_method != GET) { return 405; }
        limit_req zone=forge_explorer burst=10 nodelay;
        proxy_pass http://127.0.0.1:19810/api/monitor;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Connection "";
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_connect_timeout 2s;
        proxy_read_timeout 7s;
        add_header Cache-Control "no-store" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Content-Security-Policy "default-src 'none'" always;
    }
"""
if "location = /pool/api/monitor" in original:
    if original.count("location = /pool/api/monitor") != 2:
        raise SystemExit("Unexpected existing monitor route count; refusing edits")
    print("route already installed")
    sys.exit(0)
if original.count(anchor) != 2 or original.count("listen 443 ssl") != 1:
    raise SystemExit("Nginx configuration changed; refusing automatic patch")
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = path.with_name(path.name+".bak."+stamp)
copy2(path, backup)
try:
    path.write_text(original.replace(anchor, location+anchor), encoding="utf-8")
    check = subprocess.run(["/usr/sbin/nginx","-t"],capture_output=True,text=True)
    if check.returncode != 0:
        path.write_text(original,encoding="utf-8")
        raise RuntimeError("nginx -t failed; restored original: "+check.stderr[:900])
    print("installed exact GET monitor route into HTTP and HTTPS; nginx test passed; backup="+str(backup))
except Exception:
    path.write_text(original, encoding="utf-8")
    raise
