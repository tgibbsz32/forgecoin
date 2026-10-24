"""Offline validation of ForgeCoin get_block_template JSON-RPC results.

No daemon connections, RandomX verification, job construction, or shares.
"""
from dataclasses import dataclass

class TemplateError(ValueError):
    pass

def _nonnegative(value, name):
    if type(value) is not int or value < 0:
        raise TemplateError(f"invalid {name}")
    return value

def _hex(value, name, exact_bytes=None):
    if not isinstance(value, str) or not value or len(value) % 2 or len(value)>262144:
        raise TemplateError(f"invalid {name}")
    if any(c not in "0123456789abcdefABCDEF" for c in value):
        raise TemplateError(f"invalid {name}")
    if exact_bytes is not None and len(value)!=exact_bytes*2:
        raise TemplateError(f"invalid {name}")
    return bytes.fromhex(value)

@dataclass(frozen=True)
class Template:
    height: int
    difficulty: int
    expected_reward: int
    seed_hash: bytes
    blocktemplate_blob: bytes
    blockhashing_blob: bytes
    reserved_offset: int
    reserve_size: int

def validate_template(response, reserve_size=8):
    """Trust boundary for already obtained RPC result; not proof of a canonical job."""
    _nonnegative(reserve_size,"reserve_size")
    if reserve_size>255:raise TemplateError("reserve_size too large")
    if not isinstance(response,dict):
        raise TemplateError("template response must be an object")
    if "error" in response:
        raise TemplateError("daemon RPC returned an error")
    result=response.get("result",response)
    if not isinstance(result,dict):
        raise TemplateError("invalid RPC result")
    if result.get("status") != "OK":
        raise TemplateError("daemon template status is not OK")
    if result.get("untrusted") is not False:
        raise TemplateError("trusted local template required")
    height=_nonnegative(result.get("height"),"height")
    difficulty=_nonnegative(result.get("difficulty"),"difficulty")
    if difficulty==0:raise TemplateError("zero difficulty")
    reward=_nonnegative(result.get("expected_reward"),"expected_reward")
    seed=_hex(result.get("seed_hash"),"seed_hash",32)
    blob=_hex(result.get("blocktemplate_blob"),"blocktemplate_blob")
    hashing=_hex(result.get("blockhashing_blob"),"blockhashing_blob")
    offset=_nonnegative(result.get("reserved_offset"),"reserved_offset")
    if offset+reserve_size>len(blob):
        raise TemplateError("reserved region outside block template")
    if len(hashing)<40:
        raise TemplateError("hashing blob is too short")
    return Template(height,difficulty,reward,seed,blob,hashing,offset,reserve_size)
