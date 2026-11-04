"""Offline deterministic regression tests; never touch a live daemon."""
import unittest
import forgecoin_chain_risk as m


def header(height, branch='a', timestamp=1_000_000):
    hx = lambda x: format(x, '064x')
    prefix = 0 if branch == 'a' else 10000
    return {'height': height, 'hash': hx(height+1+prefix),
            'prev_hash': hx(height+prefix) if height else '0'*64,
            'timestamp': timestamp, 'difficulty': 500000}


def snap(start, end, branch='a'):
    hs = {str(h): header(h, branch) for h in range(start, end+1)}
    return {'tip': hs[str(end)], 'headers': hs}


class ChainRiskTests(unittest.TestCase):
    def test_normal(self):
        prev = {'a': snap(1, 5), 'b': snap(1, 5)}
        current = {'a': snap(3, 6), 'b': snap(3, 6)}
        events, _ = m.assess(current, prev, now=1_000_100)
        self.assertEqual(events, [])

    def test_detect_deep_observed_reorg(self):
        old = {'a': snap(1, 8)}
        changed = snap(1, 8)
        # New branch has a common ancestor at 4 and consistent continuation at 5..8.
        for h in range(5, 9):
            changed['headers'][str(h)] = header(h, 'b')
        changed['tip'] = changed['headers']['8']
        events, _ = m.assess({'a': changed}, old, now=1_000_100)
        self.assertEqual(events[0]['code'], 'observed_reorg')
        self.assertEqual(events[0]['minimum_depth'], 4)
        self.assertEqual(events[0]['severity'], 'critical')

    def test_two_node_conflict(self):
        events, _ = m.assess({'a': snap(3, 6), 'b': snap(3, 6, 'b')}, now=1_000_100)
        self.assertIn('node_divergence', [x['code'] for x in events])

    def test_height_rollback_stale(self):
        events, _ = m.assess({'a': snap(1, 3)}, {'a': snap(1, 5)}, now=1_002_000)
        self.assertIn('height_rollback', [x['code'] for x in events])
        self.assertIn('stale_tip', [x['code'] for x in events])

    def test_no_overlap(self):
        events, _ = m.assess({'a': snap(1, 3), 'b': snap(6, 8)}, now=1_000_100)
        self.assertIn('no_overlap', [x['code'] for x in events])

    def test_history_gap_not_marked_safe(self):
        events, _ = m.assess({'a': snap(100, 107)}, {'a': snap(1, 8)}, now=1_000_100)
        self.assertIn('history_gap', [x['code'] for x in events])

    def test_endpoint_validation(self):
        self.assertEqual(m.validate_url('http://localhost:39481/json_rpc'), 'http://localhost:39481/json_rpc')
        for url in ('http://evil.example:39481/json_rpc', 'http://alice:pw@127.0.0.1:39481/json_rpc',
                    'http://127.0.0.1:39481/json_rpc?x=1'):
            with self.assertRaises(ValueError):
                m.validate_url(url)

    def test_parse_header_validation(self):
        h = header(5)
        self.assertEqual(m.parse_header(h)['difficulty'], 500000)
        for bad in ({**h, 'difficulty': -1}, {**h, 'hash': 'not a hash'},
                    {**h, 'height': True}, {**h, 'timestamp': None}):
            with self.assertRaises(ValueError):
                m.parse_header(bad)

    def test_wide_difficulty_is_hex_even_when_digits_only(self):
        h = header(5)
        self.assertEqual(m.parse_header({**h, 'wide_difficulty': '7a120'})['difficulty'], 500000)
        self.assertEqual(m.parse_header({**h, 'wide_difficulty': '0x7a120'})['difficulty'], 500000)
        # Digit-only string is still base-16, never decimal.
        self.assertEqual(m.parse_header({**h, 'wide_difficulty': '500000',
                                         'difficulty': 0x500000})['difficulty'], 0x500000)

    def test_wide_difficulty_large_and_consistent_with_header_parts(self):
        h = header(5)
        large = (3 << 64) + 500000
        wide = {**h, 'wide_difficulty': format(large, 'x'),
                'difficulty_top64': 3}
        self.assertEqual(m.parse_header(wide)['difficulty'], large)
        for bad in ({**wide, 'difficulty_top64': 2},
                    {**wide, 'difficulty': 500001},
                    {**wide, 'wide_difficulty': 'XYZ'},
                    {**wide, 'wide_difficulty': ''},
                    {**wide, 'wide_difficulty': 'f' * 65},
                    {**wide, 'wide_difficulty': 500000},
                    {**wide, 'difficulty_top64': True}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                m.parse_header(bad)

    def test_wide_difficulty_missing_rejects_string_or_boolean_fallback(self):
        h = header(5)
        for value in ('500000', True, 0, -1, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.parse_header({**h, 'difficulty': value})

    def test_reject_wrong_genesis(self):
        from unittest.mock import patch
        bad_genesis = header(0)
        with patch.object(m, 'rpc', return_value={'block_header': bad_genesis}):
            with self.assertRaisesRegex(ValueError, 'frozen ForgeCoin genesis'):
                m.take_snapshot('http://localhost:39481/json_rpc')

    def test_peer_count_and_sync_warning(self):
        node = snap(1, 5)
        node['outbound_peers'] = 1
        node['synchronized'] = False
        events, _ = m.assess({'node-a': node}, now=1_000_100)
        self.assertIn('low_outbound_peer_count', [e['code'] for e in events])
        self.assertIn('node_not_synchronized', [e['code'] for e in events])

    def test_rpc_peer_count_fails_closed(self):
        from unittest.mock import patch
        def fake_rpc(url, method, params=None, timeout=5):
            if method == 'get_block_header_by_height':
                genesis = header(0)
                genesis['hash'] = m.FROZEN_GENESIS_HASH
                return {'block_header': genesis}
            if method == 'get_info':
                return {'outgoing_connections_count': -1, 'synchronized': True}
            raise AssertionError(method)
        with patch.object(m, 'rpc', side_effect=fake_rpc):
            with self.assertRaisesRegex(ValueError, 'outgoing peer count'):
                m.take_snapshot('http://localhost:39481/json_rpc')

    def test_severe_difficulty_jump_alert_only(self):
        before = snap(1, 5)
        after = snap(2, 6)
        after['tip'] = {**after['tip'], 'difficulty': 2500000}
        events, _ = m.assess({'a': after}, {'a': before}, now=1_000_100)
        self.assertIn('difficulty_jump', [event['code'] for event in events])

    def test_history_audit_error_keeps_baseline_unmodified(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        import json
        with TemporaryDirectory() as d:
            state = Path(d) / 'state.json'
            original = {'version': 1, 'nodes': {
                'http://localhost:39481/json_rpc': {'anchors': {'60': header(60)['hash']}},
                'http://localhost:39581/json_rpc': {'anchors': {'60': header(60)['hash']}}
            }}
            state.write_text(json.dumps(original))
            with patch.object(m, 'take_snapshot', return_value=snap(500, 563)):
                with patch.object(m, 'rpc', side_effect=ValueError('historical RPC unreachable')):
                    code = m.main(['--node', 'http://localhost:39481',
                                   '--node', 'http://localhost:39581',
                                   '--state', str(state)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(state.read_text()), original)

    def test_failed_rpc_not_persisted(self):
        from unittest.mock import patch
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as d:
            state = Path(d) / 'state.json'
            with patch.object(m, 'take_snapshot', side_effect=OSError('offline')):
                out = m.main(['--node', 'http://localhost:39481', '--node', 'http://localhost:39581',
                              '--state', str(state)])
            self.assertEqual(out, 2)
            self.assertFalse(state.exists())


if __name__ == '__main__':
    unittest.main()
