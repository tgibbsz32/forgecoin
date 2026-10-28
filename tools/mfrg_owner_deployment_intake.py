#!/usr/bin/env python3
"""Validate public owner-supplied mFRG mainnet identifiers and evidence references.

This is syntax and completeness validation only. It does NOT authenticate
ownership, query Solana, or authorize any financial operation.
"""
import argparse
import json
import sys
from urllib.parse import urlsplit

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
DEVNET_MINT = "9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw"

class IntakeError(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise IntakeError(message)

def decode_base58(value, expected_len):
    require(isinstance(value, str) and 32 <= len(value) <= 88, "public identifier length invalid")
    number = 0
    for char in value:
        require(char in ALPHABET, "public identifier contains non-base58 character")
        number = number * 58 + ALPHABET.index(char)
    data = (number.to_bytes((number.bit_length() + 7)//8, "big") if number else b"")
    data = b"\x00" * (len(value)-len(value.lstrip("1"))) + data
    require(len(data) == expected_len, "public identifier decoded length invalid")
    return data

def public_https(url):
    require(isinstance(url, str), "evidence URL must be text")
    parsed = urlsplit(url)
    require(parsed.scheme == "https" and bool(parsed.hostname), "public HTTPS evidence URL required")
    require(parsed.username is None and parsed.password is None and parsed.port in (None,443), "credentials or custom port prohibited")
    host = parsed.hostname
    require(host not in ("localhost",) and not host.endswith((".local",".internal")),"private host prohibited")
    require(not parsed.fragment, "URL fragments prohibited")
    # No downloads or requests: DNS resolution, actual routability, and independence remain unverified.
    return parsed.netloc.lower()

def validate(record):
    require(isinstance(record,dict) and set(record)=={
        "version","network","mint","initialization_signature","owner_statement_url",
        "initialization_history_url","independent_source_urls"}, "exact intake schema required")
    require(type(record["version"]) is int and record["version"]==1,"version invalid")
    require(record["network"]=="solana-mainnet-beta","only Solana mainnet-beta accepted")
    decode_base58(record["mint"],32)
    require(record["mint"]!=DEVNET_MINT,"historical devnet test mint forbidden")
    decode_base58(record["initialization_signature"],64)
    public_https(record["owner_statement_url"])
    public_https(record["initialization_history_url"])
    sources=record["independent_source_urls"]
    require(isinstance(sources,list) and len(sources)>=2,"two independent corroboration candidates required")
    hosts=[public_https(u) for u in sources]
    require(len(set(hosts))==len(hosts),"duplicate source origins")
    return {
       "status":"PUBLIC_IDENTIFIERS_AND_REFERENCES_FORMAT_VALID_ONLY",
       "reported_mint":record["mint"],
       "reported_initialization_signature":record["initialization_signature"],
       "source_candidates":len(sources),
       "owner_authorization_authenticated":False,
       "source_administration_independence_verified":False,
       "solana_mainnet_genesis_verified":False,
       "onchain_mint_or_holder_data_verified":False,
       "minting_authorized":False,"sales_authorized":False,
       "treasury_release_authorized":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("intake_json")
    a=p.parse_args()
    try:
        with open(a.intake_json,encoding="utf8") as f:record=json.load(f)
        print(json.dumps(validate(record),indent=2,sort_keys=True))
    except (OSError,ValueError,TypeError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
