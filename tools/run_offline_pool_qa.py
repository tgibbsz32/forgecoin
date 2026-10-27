#!/usr/bin/env python3
"""Reproducible isolated native daemon + C pool protocol QA, no mining/payouts.

All sockets loopback-only; daemon --offline; disposable QA wallet address;
RPC and Stratum tests only. Processes are always stopped in finally.
"""
import json, os, pathlib, re, signal, socket, subprocess, sys, tempfile, time
import urllib.error, urllib.request

BASE=pathlib.Path("/home/ubuntu/forgecoin-mainnet-20261026")
DAEMON=BASE/"build-release/bin/forged"
POOL=BASE/"services/official_pool/jtgrassie/build/release/forgecoin-pool"
CONFIG=BASE/"qa-pool-20261027/pool-qa.conf"
PROBE=BASE/"tools/probe_pool_stratum_offline.py"
WALLET_RPC=BASE/"build-release/bin/forge-wallet-rpc"
QA_WALLET=BASE/"qa-wallet-20261027/qa-only-wallet"
QA_PASSWORD=BASE/"qa-wallet-20261027/qa-only-password"
EXPECTED="4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"

def fetch(url):
    with urllib.request.urlopen(url,timeout=2) as response:
        return json.load(response)
def rpc(method, params=None):
    data=json.dumps({"jsonrpc":"2.0","id":"qa-only","method":method,"params":params or {}}).encode()
    request=urllib.request.Request("http://127.0.0.1:39481/json_rpc",
         data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(request,timeout=3) as response:
        result=json.load(response)
    return result["result"]
def wallet_rpc(method):
    if method not in ("get_address","get_balance"):
        raise ValueError("Wallet RPC method not allowed in QA")
    request=urllib.request.Request("http://127.0.0.1:39483/json_rpc",
        data=json.dumps({"jsonrpc":"2.0","id":"qa-read-only","method":method}).encode(),
        headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(request,timeout=3) as response:
        result=json.load(response)
    if result.get("error"):
        raise ValueError("QA wallet RPC returned error")
    return result["result"]

def wait_for(check, timeout=15, name="readiness"):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            value=check()
            if value:return value
        except (OSError,ValueError,KeyError,urllib.error.URLError,ConnectionError):
            pass
        time.sleep(.25)
    raise AssertionError(name+" deadline exceeded")
def stop(process):
    if process is None:return
    if process.poll() is None:
        process.terminate()
        try:process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=5)

def real_randomx_share_probe(qa):
    binary=pathlib.Path("/home/ubuntu/pool-preparation/xmrig-v6.26.0/build-synthetic/xmrig-notls")
    donate=pathlib.Path("/home/ubuntu/pool-preparation/xmrig-v6.26.0/src/donate.h")
    assert binary.is_file() and donate.is_file()
    text=donate.read_text()
    assert "kDefaultDonateLevel = 0" in text and "kMinimumDonateLevel = 0" in text, "Donation disablement not verified"
    addr=(BASE/"qa-wallet-20261027/public-qa-only-address.txt").read_text().strip()
    miner=None
    with (qa/"xmrig.log").open("w") as log:
        try:
            miner=subprocess.Popen([str(binary),"-o","127.0.0.1:49442","-u",addr,"-p","qa-only",
                 "-a","rx/0","--donate-level=0","--randomx-mode=light",
                 "--threads=1","--cpu-priority=1","--no-huge-pages","--no-color",
                 "--print-time=5","--log-file="+str(qa/"xmrig-details.log")],
                 stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            got=None
            end=time.monotonic()+45
            while time.monotonic()<end:
                time.sleep(1)
                if miner.poll() is not None:
                    raise AssertionError("XMRig exited before an accepted share; see QA log")
                state=fetch("http://127.0.0.1:49443/stats")
                if state.get("round_hashes",0)>0:
                    got=state
                    break
            if got is None:
                raise AssertionError("No native RandomX shares accepted during bounded QA run")
            assert got.get("pool_fee")==.01
            assert got.get("pool_blocks_found")==0, "Unexpected offline QA block"
            print(json.dumps({"status":"PASS_REAL_XMRIG_TO_NATIVE_POOL_SHARE",
                "verifiedRandomX":True,"acceptedWorkDifficulty":got["round_hashes"],
                "poolFeePercent":1,"productionLaunch":False,
                "network":"offline_loopback_only","realMainnetBlockMined":False},sort_keys=True))
        finally:
            stop(miner)

def main():
    assert all(p.is_file() for p in (DAEMON,POOL,CONFIG,PROBE,WALLET_RPC,QA_WALLET,QA_PASSWORD))
    qa=pathlib.Path(tempfile.mkdtemp(prefix="offline-pool-qa-",dir=BASE/"qa-pool-20261027"))
    db=qa/"blockchain"
    pooldir=qa/"pool-data"
    pooldir.mkdir(mode=0o700)
    conf=qa/"config.conf"
    source=CONFIG.read_text()
    assert "disable-payouts = 1" in source and "disable-hash-check = 0" in source
    assert "pool-listen = 127.0.0.1" in source and "webui-listen = 127.0.0.1" in source
    assert "pool-port = 49442" in source and "webui-port = 49443" in source
    new=re.sub(r"(?m)^data-dir\s*=.*$", "data-dir = "+str(pooldir),source)
    if "--with-miner" in sys.argv:
        # Artificially lower ONLY the disposable QA pool share target, not
        # native consensus difficulty. This makes a real RandomX share fast.
        assert "pool-start-diff = 1000" in new
        new=new.replace("pool-start-diff = 1000","pool-start-diff = 10")
    conf.write_text(new)
    conf.chmod(0o600)
    daemon=None;pool=None;wallet=None
    with (qa/"daemon.log").open("w") as daemon_log, (qa/"pool.log").open("w") as pool_log, (qa/"wallet-rpc.log").open("w") as wallet_log:
        try:
            daemon=subprocess.Popen([str(DAEMON),"--offline","--no-igd","--non-interactive",
              "--data-dir",str(db),"--p2p-bind-ip","127.0.0.1","--p2p-bind-port","39480",
              "--rpc-bind-ip","127.0.0.1","--rpc-bind-port","39481",
              "--zmq-rpc-bind-ip","127.0.0.1","--zmq-rpc-bind-port","39482",
              "--check-updates","disabled","--disable-dns-checkpoints"],
              stdin=subprocess.DEVNULL,stdout=daemon_log,stderr=subprocess.STDOUT,start_new_session=True)
            info=wait_for(lambda:fetch("http://127.0.0.1:39481/get_info"),name="daemon RPC")
            gen=rpc("get_block_header_by_height",{"height":0})["block_header"]
            assert info.get("nettype")=="mainnet" and info.get("height")==1
            assert gen.get("nonce")==20261026 and gen.get("hash")==EXPECTED
            explorer=wait_for(lambda:fetch("http://127.0.0.1:19800/api/overview"),
                              timeout=10,name="existing Oracle block explorer")
            assert explorer.get("height")==1 and explorer.get("tip_height")==0
            assert explorer.get("tip_hash")==EXPECTED and explorer.get("difficulty")=="500000"
            blocks=fetch("http://127.0.0.1:19800/api/blocks")
            assert blocks["blocks"][0]["hash"]==EXPECTED
            first=fetch("http://127.0.0.1:19800/api/block/0")
            assert first["header"]["hash"]==EXPECTED
            print("QA_EXPLORER_OVERVIEW_BLOCK_LIST_AND_GENESIS_DETAIL: PASS")
            wallet=subprocess.Popen([str(WALLET_RPC),"--wallet-file",str(QA_WALLET),
                "--password-file",str(QA_PASSWORD),"--daemon-address","127.0.0.1:39481",
                "--rpc-bind-ip","127.0.0.1","--rpc-bind-port","39483",
                "--disable-rpc-login","--non-interactive","--no-initial-sync","--no-dns"],
                stdin=subprocess.DEVNULL,stdout=wallet_log,stderr=subprocess.STDOUT,
                start_new_session=True)
            qa_wallet=wait_for(lambda:wallet_rpc("get_address"),
                timeout=15,name="disposable QA wallet RPC")
            expected_wallet=(BASE/"qa-wallet-20261027/public-qa-only-address.txt").read_text().strip()
            assert qa_wallet["address"]==expected_wallet, "QA wallet RPC address mismatch"
            zero=wallet_rpc("get_balance")
            assert int(zero["balance"])==0 and int(zero["unlocked_balance"])==0
            print("QA_NATIVE_FRG_WALLET_RPC_GET_ADDRESS_AND_ZERO_BALANCE: PASS")
            pool=subprocess.Popen([str(POOL),"--config-file",str(conf)],
                 stdin=subprocess.DEVNULL,stdout=pool_log,stderr=subprocess.STDOUT,start_new_session=True)
            stats=wait_for(lambda:fetch("http://127.0.0.1:49443/stats"),name="pool stats")
            stats=wait_for(lambda: fetch("http://127.0.0.1:49443/stats") if
                    fetch("http://127.0.0.1:49443/stats").get("network_difficulty")==500000 else None,
                    timeout=15,name="pool next block difficulty")
            assert stats["network_height"]==1
            assert stats["network_difficulty"]==500000
            assert stats["pool_fee"]==.01
            assert stats["pool_blocks_found"]==0
            probe=subprocess.run([sys.executable,str(PROBE)],capture_output=True,text=True,timeout=15)
            print(probe.stdout.strip())
            if probe.returncode!=0:
                raise AssertionError("QA Stratum probe failed (return code {})".format(probe.returncode))
            result=fetch("http://127.0.0.1:49443/stats")
            assert result["pool_blocks_found"]==0
            assert result["round_hashes"]==0
            if "--with-miner" in sys.argv:
                real_randomx_share_probe(qa)
            print(json.dumps({"status":"PASS_DAEMON_POOL_JOB_INVALID_SHARE_QA",
                 "daemonGenesis":gen["hash"],"candidateHeight":stats["network_height"],
                 "miningDifficulty":stats["network_difficulty"],
                 "explorerGenesisVerified":True,
                 "poolFeePercent":stats["pool_fee"]*100,
                 "blocksMined":0,"payoutsEnabled":False,
                 "actualMinerShareTest":"--with-miner" in sys.argv,
                 "allInterfaces":"127.0.0.1",
                 "blockSubmit":"not_attempted","logs":str(qa)},sort_keys=True))
        finally:
            stop(pool)
            stop(wallet)
            stop(daemon)
    # Confirm both daemons terminated, not silently left running.
    assert pool.poll() is not None and wallet.poll() is not None and daemon.poll() is not None
    print("QA processes cleaned up; no production mining endpoints opened")

if __name__=="__main__":
    main()
