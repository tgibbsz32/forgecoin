"""Historical anchor audit for the read-only FRG observer.

Anchors are *observations*, not consensus checkpoints or financial finality.
A conflict cannot be automatically 'repaired' by replacing an old anchor.
Only a manual reviewed reset may establish a new historical baseline.
"""
ANCHOR_SPACING = 60
ANCHOR_CONFIRMATIONS = 60
MAX_ANCHORS = 65536
AUDIT_PER_POLL = 8


def valid_hash(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in '0123456789abcdef' for c in value))


def audit_node(snapshot, previous, fetch_by_height):
    """Verify old canonical observations on a rotating schedule and append mature anchors.

    fetch_by_height(height) must retrieve and validate *one* daemon block header and
    return {height: int, hash: str, prev_hash: str, difficulty: int, timestamp: int}.
    Exceptions indicate unverified monitoring and MUST prevent baseline persistence.
    """
    anchors = previous.get('anchors', {})
    cursor = previous.get('audit_cursor', 0)
    if not isinstance(anchors, dict) or len(anchors) > MAX_ANCHORS:
        raise ValueError('invalid or oversized saved historical anchors')
    if not isinstance(cursor, int) or isinstance(cursor, bool) or cursor < 0:
        raise ValueError('invalid saved historical audit cursor')
    for key, value in anchors.items():
        if not isinstance(key, str) or not key.isdecimal() or str(int(key)) != key or not valid_hash(value):
            raise ValueError('invalid saved historical anchor entry')
    tip_height = snapshot['tip']['height']
    keys = sorted(anchors, key=int)
    # Always check the two newest anchors; cycle through older ones without
    # permanently dropping their previous canonical-hash observations.
    recent = keys[-2:]
    older = keys[:-2]
    chosen = list(recent)
    advance = min(max(0, AUDIT_PER_POLL - len(recent)), len(older))
    for i in range(advance):
        chosen.append(older[(cursor+i) % len(older)])
    events = []
    for height_key in chosen:
        height = int(height_key)
        if height > tip_height:
            events.append({'code': 'historical_anchor_ahead_of_tip',
                           'height': height, 'tip_height': tip_height,
                           'severity': 'critical'})
            continue
        observed = fetch_by_height(height)
        if observed['height'] != height or not valid_hash(observed['hash']):
            raise ValueError('historical height/hash did not match RPC request')
        if observed['hash'] != anchors[height_key]:
            events.append({'code': 'historical_anchor_conflict',
                           'height': height, 'expected_hash': anchors[height_key],
                           'observed_hash': observed['hash'], 'severity': 'critical'})
    next_anchors = dict(anchors)
    for key, h in snapshot['headers'].items():
        height = h['height']
        if height > 0 and height % ANCHOR_SPACING == 0 and height + ANCHOR_CONFIRMATIONS <= tip_height:
            previous_hash = next_anchors.get(key)
            if previous_hash is None:
                if len(next_anchors) >= MAX_ANCHORS:
                    raise ValueError('maximum historical anchors reached; manual archive required')
                next_anchors[key] = h['hash']
            elif previous_hash != h['hash']:
                events.append({'code': 'historical_anchor_conflict',
                               'height': height, 'expected_hash': previous_hash,
                               'observed_hash': h['hash'], 'severity': 'critical'})
    return events, {'anchors': next_anchors,
                    'audit_cursor': (cursor + advance) % max(1, len(older))}
