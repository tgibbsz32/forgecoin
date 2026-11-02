"""Deterministic offline PPLNS snapshot calculation; NO live share credit or payouts.

The caller must supply chronological, independently validated and deduplicated
shares up to (and not after) the candidate's discovery cutoff. No chain RPC,
share authentication, maturity verification, or payment authorization exists.
"""
from dataclasses import dataclass
from .model import Allocation, allocate_reward

MAX_SQLITE_INT = (1 << 63) - 1
MAX_RESEARCH_SHARES = 100_000


@dataclass(frozen=True)
class VerifiedShare:
    sequence: int
    share_id: str
    miner: str
    difficulty: int


@dataclass(frozen=True)
class WindowSnapshot:
    target_work: int
    observed_work: int
    miner_work: dict[str, int]
    first_sequence: int | None
    last_sequence: int | None
    partial_first_share: bool


@dataclass(frozen=True)
class PPLNSAllocation:
    window: WindowSnapshot
    reward: Allocation


def snapshot(shares: list[VerifiedShare] | tuple[VerifiedShare, ...],
             network_difficulty: int, *, multiplier: int = 2) -> WindowSnapshot:
    """Select the last multiplier * network_difficulty units of verified work.

    If history is shorter than the target, use the available work only. A
    partially crossing oldest share contributes exactly the remaining work.
    Strict input order is required: sorting corrupted history would conceal
    a bookkeeping error.
    """
    if (type(network_difficulty) is not int or network_difficulty < 1
            or network_difficulty > MAX_SQLITE_INT
            or type(multiplier) is not int or not 1 <= multiplier <= 16
            or network_difficulty > MAX_SQLITE_INT // multiplier):
        raise ValueError("invalid PPLNS work target")
    if (not isinstance(shares, (list, tuple)) or
            not 1 <= len(shares) <= MAX_RESEARCH_SHARES):
        raise ValueError("nonempty bounded verified-share history required")
    seen = set()
    previous = -1
    for share in shares:
        if not isinstance(share, VerifiedShare):
            raise ValueError("invalid verified share")
        if (type(share.sequence) is not int or not 0 <= share.sequence <= MAX_SQLITE_INT
                or share.sequence <= previous):
            raise ValueError("shares must be in strictly increasing sequence")
        if (not isinstance(share.share_id, str)
                or not 1 <= len(share.share_id) <= 128
                or any(ord(c) < 33 or ord(c) > 126 for c in share.share_id)
                or share.share_id in seen):
            raise ValueError("invalid or repeated share identity")
        if (not isinstance(share.miner, str) or not 1 <= len(share.miner) <= 256
                or any(ord(c) < 33 or ord(c) > 126 for c in share.miner)):
            raise ValueError("invalid miner identity")
        if (type(share.difficulty) is not int
                or not 1 <= share.difficulty <= MAX_SQLITE_INT):
            raise ValueError("invalid verified share difficulty")
        previous = share.sequence
        seen.add(share.share_id)

    target = network_difficulty * multiplier
    remaining = target
    weights: dict[str, int] = {}
    first = None
    partial = False
    for share in reversed(shares):
        if remaining == 0:
            break
        work = min(remaining, share.difficulty)
        weights[share.miner] = weights.get(share.miner, 0) + work
        first = share.sequence
        partial = work < share.difficulty
        remaining -= work
    return WindowSnapshot(target, target - remaining,
                          dict(sorted(weights.items())), first,
                          shares[-1].sequence, partial)


def allocate_pplns(reward_atomic: int,
                   shares: list[VerifiedShare] | tuple[VerifiedShare, ...],
                   network_difficulty: int, *, multiplier: int = 2
                   ) -> PPLNSAllocation:
    """Research-only 1% fee and exact integer distribution over a PPLNS window."""
    if (type(reward_atomic) is not int
            or not 0 <= reward_atomic <= MAX_SQLITE_INT):
        raise ValueError("invalid atomic-unit reward")
    window = snapshot(shares, network_difficulty, multiplier=multiplier)
    result = allocate_reward(reward_atomic, window.miner_work)
    if result.fee_atomic + sum(result.miner_atomic.values()) != reward_atomic:
        raise AssertionError("atomic-unit conservation failed")
    return PPLNSAllocation(window, result)
