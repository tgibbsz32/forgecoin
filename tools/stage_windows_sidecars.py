"""Stage only the reviewed system-DLL-only MinGW artifacts; never execute them.

The Tauri suffix selects the host package, not the sidecar compiler ABI.
Changing an artifact requires a new dependency audit and digest review here.
"""
import argparse
import hashlib
import json
from pathlib import Path

TARGET = "x86_64-pc-windows-msvc"
SOURCE_COMMIT = "0f3a9a2820a6285838fb45227a34c65957615e38"
# MinGW64 Release, ARCH_ID=x86_64. Both PE import tables were inspected with
# objdump -p: ADVAPI32, CRYPT32, IPHLPAPI, KERNEL32, msvcrt, MSWSOCK,
# SHELL32, USER32, WS2_32. No external runtime DLLs were imported.
REVIEWED = {
    "forged": "600a76d02fbf9f46825ca989daf1c74187aa3bf524d651c35cfe6fbbc1fd2836",
    "forge-wallet-rpc": "34a3f72add57fb96beb3a822d28c910e1e6eadb2f6acfdee01a1a901de7b12e0",
}


def validate_network_identity(manifest):
    """The dependency audit must approve the same bytes as the network manifest."""
    identity = json.loads(Path(manifest).read_text(encoding="utf-8"))
    expected = identity.get("windows_prelaunch_binaries_sha256", {})
    if identity.get("release_authorized") is not False:
        raise ValueError("Expected a locked prelaunch identity; release packaging needs separate review")
    if not identity.get("genesis_hash") or identity.get("stage") != "genesis-frozen":
        raise ValueError("Missing frozen genesis identity")
    for name, digest in REVIEWED.items():
        if expected.get(f"{name}.exe") != digest:
            raise ValueError(
                f"Stale sidecar audit for {name}: reviewed bytes do not match the network manifest; "
                "review matching binaries and DLL dependencies before updating the audit"
            )


def validated(directory, suffixed=False):
    payloads = {}
    for name, digest in REVIEWED.items():
        filename = f"{name}-{TARGET}.exe" if suffixed else f"{name}.exe"
        payload = (Path(directory) / filename).read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError(f"Unreviewed sidecar: {filename}; audit provenance and DLL imports first")
        payloads[name] = payload
    return payloads


def stage(source, destination):
    # Validate the complete set before writing any artifact. Copy exactly the
    # bytes hashed, so source replacement cannot substitute unreviewed bytes.
    payloads = validated(source)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (destination / f"{name}-{TARGET}.exe").write_bytes(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate_network_identity(Path(__file__).resolve().parents[1] / "config/mainnet.identity.json")
        if args.source:
            stage(args.source, args.destination)
        else:
            validated(args.destination, suffixed=True)
    except (OSError, ValueError) as error:
        parser.exit(1, f"BLOCKED: {error}\n")
    print(f"Reviewed MinGW sidecars for Tauri {TARGET}; source {SOURCE_COMMIT}")
    print("Packaging prerequisite only; clean-machine runtime and mining acceptance outstanding")


if __name__ == "__main__":
    main()
