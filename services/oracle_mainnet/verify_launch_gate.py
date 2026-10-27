#!/usr/bin/env python3
"""Oracle ForgeCoin launch preflight. Read-only; cannot start mining.

Rejects legacy binary, wrong genesis, wrong fee wallet, or unauthorized launch.
Start-mode needs BOTH an approved frozen release manifest and an operator
authorization marker bound to its SHA256. Source repo remains release_locked.
"""
import argparse
import hashlib
import json
import pathlib
import sys

EXPECTED_GENESIS = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"
EXPECTED_DAEMON_SHA256 = "3dd3d0c10f41ef2f887314221e0b9adec9571b98a83c9783a78a6290156506bd"
EXPECTED_FEE_ADDRESS = "YnJPKnrv2fk6MdHkvvAxDbe1L3Dv7WgtrjPBHnP3NokU1Zri6a8da9SfoDiF9SpQxP4Xn18BT2bBNLnVtCPqXTvr1UTsca4Z4"
MANIFEST = pathlib.Path("/home/ubuntu/forgecoin-mainnet-20261026/config/mainnet.identity.json")
DAEMON = pathlib.Path("/home/ubuntu/forgecoin-mainnet-20261026/build-release/bin/forged")
MARKER = pathlib.Path("/etc/forgecoin/approved-mainnet-launch.json")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path,"rb") as fh:
        while True:
            blob=fh.read(1024*1024)
            if not blob:break
            h.update(blob)
    return h.hexdigest()

def verify(manifest_bytes, daemon_digest, marker=None, require_authorized=False):
    identity=json.loads(manifest_bytes)
    errors=[]
    if identity.get("chain")!="forgecoin-mainnet":
        errors.append("wrong_chain")
    if identity.get("genesis_nonce")!=20261026 or identity.get("genesis_hash")!=EXPECTED_GENESIS:
        errors.append("wrong_genesis")
    if identity.get("network_uuid")!="bd936359-09e4-4fdb-8ec0-12fa9d6ef090":
        errors.append("wrong_network_uuid")
    ports=identity.get("ports")
    if not isinstance(ports,dict) or (ports.get("p2p"),ports.get("daemon_rpc"),ports.get("zmq_rpc"))!=(39480,39481,39482):
        errors.append("wrong_network_ports")
    mining=identity.get("mining")
    if not isinstance(mining,dict) or any([
        mining.get("algorithm")!="RandomX",
        mining.get("target_seconds")!=120,
        mining.get("starting_difficulty")!=500000,
        mining.get("difficulty_floor")!=400000,
        mining.get("lwma_activation_height")!=16]):
        errors.append("wrong_consensus_policy")
    currency=identity.get("currency")
    if not isinstance(currency,dict) or (
        currency.get("ticker")!="FRG" or
        currency.get("decimals")!=8 or
        currency.get("money_supply_constant_frg")!=50000000 or
        currency.get("genesis_output_atomic")!=1192092895):
        errors.append("currency_terms_changed")
    pool=identity.get("pool")
    if not isinstance(pool,dict) or (
        pool.get("operator_fee_fraction")!="0.01" or
        pool.get("operator_fee_address")!=EXPECTED_FEE_ADDRESS):
        errors.append("fee_routing_changed")
    if daemon_digest != EXPECTED_DAEMON_SHA256:
        errors.append("binary_sha256_mismatch")
    release=identity.get("release_authorized") is True and identity.get("stage")=="released"
    manifest_digest=hashlib.sha256(manifest_bytes).hexdigest()
    marker_ok=(isinstance(marker,dict) and marker.get("manifest_sha256")==manifest_digest and
              marker.get("genesis_hash")==EXPECTED_GENESIS and
              marker.get("daemon_sha256")==EXPECTED_DAEMON_SHA256 and
              marker.get("operator_approval")=="explicit")
    if require_authorized:
        if not release:errors.append("release_manifest_not_authorized")
        if not marker_ok:errors.append("operator_approval_missing_or_invalid")
    return {
      "binaryPinned":daemon_digest==EXPECTED_DAEMON_SHA256,
      "genesisMatches":identity.get("genesis_hash")==EXPECTED_GENESIS,
      "configuredPoolFeePercent":"1",
      "releaseManifestAuthorized":release,
      "operatorMarkerValid":bool(marker_ok),
      "canStart":not errors and require_authorized,
      "reasons":errors,
      "manifestSha256":manifest_digest,
      "daemonSha256":daemon_digest
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--require-authorized",action="store_true",help="fail unless release manifest AND matching explicit marker")
    parser.add_argument("--manifest",type=pathlib.Path,default=MANIFEST)
    parser.add_argument("--daemon",type=pathlib.Path,default=DAEMON)
    parser.add_argument("--operator-marker",type=pathlib.Path,default=MARKER)
    args=parser.parse_args()
    try:
        manifest_data=args.manifest.read_bytes()
        digest=sha256_file(args.daemon)
        marker=json.loads(args.operator_marker.read_text(encoding="utf-8")) if args.operator_marker.is_file() else None
        result=verify(manifest_data,digest,marker,args.require_authorized)
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FORGECOIN_LAUNCH_GATE_REJECTED: "+type(exc).__name__,file=sys.stderr)
        return 8
    print(json.dumps(result,sort_keys=True,indent=2))
    if result["reasons"]:
        print("FORGECOIN_LAUNCH_GATE_REJECTED",file=sys.stderr)
        return 9
    print("FORGECOIN_PREFLIGHT_PASS_NO_PRODUCTION_START" if not args.require_authorized else "FORGECOIN_PRODUCTION_RELEASE_GATE_PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
