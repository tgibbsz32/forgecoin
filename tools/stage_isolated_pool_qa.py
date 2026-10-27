#!/usr/bin/env python3
"""Stage an isolated localhost-only native pool QA configuration.

Uses a disposable QA receiving address, NEVER the operator's real reward wallet.
Never changes launch config, releases, services, payout flags or public firewall.
"""
import pathlib
root=pathlib.Path("/home/ubuntu/forgecoin-mainnet-20261026")
source=root/"services/official_pool/jtgrassie/pool.conf"
qa=root/"qa-pool-20261027"
qa.mkdir(mode=0o700,exist_ok=True)
wallet=(root/"qa-wallet-20261027/public-qa-only-address.txt").read_text().strip()
assert len(wallet)==97 and wallet.startswith("YnJ")
assert wallet!="YnJPKnrv2fk6MdHkvvAxDbe1L3Dv7WgtrjPBHnP3NokU1Zri6a8da9SfoDiF9SpQxP4Xn18BT2bBNLnVtCPqXTvr1UTsca4Z4"
src=source.read_text()
changes={
"pool-wallet":wallet,
"wallet-rpc-port":"39483",
"pool-port":"49442",
"webui-port":"49443",
"data-dir":str(qa/"database"),
"disable-payouts":"1",
"disable-hash-check":"0",
"pool-listen":"127.0.0.1",
"webui-listen":"127.0.0.1",
"rpc-port":"39481",
}
values={}
lines=[]
for line in src.splitlines():
    if line.strip() and not line.lstrip().startswith("#") and "=" in line:
        key,_=line.split("=",1)
        key=key.strip()
        if key in changes:
            assert key not in values
            values[key]=True
            line=key+" = "+changes[key]
    lines.append(line)
assert set(values)==set(changes)
conf=qa/"pool-qa.conf"
assert not conf.exists(), "Refusing to overwrite existing test pool configuration"
conf.write_text("\n".join(lines)+"\n")
conf.chmod(0o600)
print("Staged isolated loopback native C pool QA config; no real keys")
print("QA Stratum port: 49442; stats: 49443; daemon: 39481; wallet RPC placeholder: 39483")
print("QA reward destination differs from dedicated 1% operator fee destination")
print("Payouts disabled, native RandomX hash checks enabled")
