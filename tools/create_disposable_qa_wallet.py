#!/usr/bin/env python3
"""Generate and identify an isolated disposable Oracle QA wallet.

Does not print mnemonic, private keys, passwords, full CLI output, or balances.
NEVER use the QA wallet as the real mining-pool reward wallet.
"""
import os
import pathlib
import re
import secrets
import subprocess
import sys

walletcli="/home/ubuntu/forgecoin-mainnet-20261026/build-release/bin/forge-wallet-cli"
dir=pathlib.Path("/home/ubuntu/forgecoin-mainnet-20261026/qa-wallet-20261027")
dir.mkdir(mode=0o700,exist_ok=True)
os.chmod(dir,0o700)
w=dir/"qa-only-wallet"
passwd=dir/"qa-only-password"
if w.exists() or pathlib.Path(str(w)+".keys").exists():
    print("Wallet exists; refusing replacement")
    sys.exit(1)
passwd.write_text(secrets.token_urlsafe(40)+"\n",encoding="utf-8")
os.chmod(passwd,0o600)
cmd=[walletcli,"--offline","--no-dns","--generate-new-wallet",str(w),
     "--password-file",str(passwd),"--mnemonic-language","English","--command","address"]
try:
    proc=subprocess.run(cmd,input="\n",text=True,stdout=subprocess.PIPE,
         stderr=subprocess.PIPE,timeout=40)
except subprocess.TimeoutExpired:
    print("QA wallet CLI timed out without exposing secrets")
    sys.exit(2)
out=proc.stdout
matches=re.findall(r"(?<![1-9A-HJ-NP-Za-km-z])[1-9A-HJ-NP-Za-km-z]{90,110}(?![1-9A-HJ-NP-Za-km-z])",out)
if proc.returncode or not pathlib.Path(str(w)+".keys").exists() or not matches:
    print("QA wallet creation did not pass checks: return-code=",proc.returncode,
          ", keyfile_exists=",pathlib.Path(str(w)+".keys").exists(),",address_found=",bool(matches))
    sys.exit(3)
addr=matches[-1]
if len(addr)<95 or len(addr)>100:
    print("QA address length mismatch; refusing to stage")
    sys.exit(4)
(dir/"public-qa-only-address.txt").write_text(addr+"\n",encoding="ascii")
os.chmod(dir/"public-qa-only-address.txt",0o600)
print("QA wallet generated without displaying credentials")
print("QA public address:",addr)
print("QA wallet files remain 0700/0600 in isolated directory; never use for production")
