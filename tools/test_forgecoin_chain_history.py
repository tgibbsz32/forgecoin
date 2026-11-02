"""Deterministic tests for non-consensus historical-observation safety."""
import unittest

from forgecoin_chain_history import audit_node, MAX_ANCHORS
from test_forgecoin_chain_risk import header, snap


class HistoricalObservationTests(unittest.TestCase):
    def test_new_mature_anchor_and_followup_poll(self):
        first = snap(57, 120)
        events, state = audit_node(first, {}, lambda n: header(n))
        self.assertFalse(events)
        self.assertEqual(state['anchors'], {'60': header(60)['hash']})
        events, again = audit_node(snap(100, 160), state, lambda n: header(n))
        self.assertEqual(events, [])
        self.assertEqual(again['anchors']['60'], header(60)['hash'])

    def test_detect_old_history_reorg_outside_recent_window(self):
        previous = {'anchors': {'60': header(60)['hash']}}
        changed = header(60, 'b')
        events, state = audit_node(snap(500, 563), previous, lambda n: changed)
        self.assertEqual(events[0]['code'], 'historical_anchor_conflict')
        self.assertEqual(events[0]['severity'], 'critical')
        self.assertEqual(state['anchors']['60'], header(60)['hash'])

    def test_ahead_of_tip_is_critical(self):
        previous = {'anchors': {'600': header(600)['hash']}}
        events, _ = audit_node(snap(10, 50), previous, lambda n: header(n))
        self.assertEqual(events[0]['code'], 'historical_anchor_ahead_of_tip')

    def test_detect_changed_stored_recent_observation(self):
        current = snap(57, 120)
        previous = {'anchors': {'60': header(60, 'b')['hash']}}
        events, state = audit_node(current, previous, lambda n: header(n))
        self.assertGreaterEqual(len(events), 1)
        self.assertTrue(all(x['code'] == 'historical_anchor_conflict' for x in events))
        self.assertEqual(state['anchors']['60'], header(60, 'b')['hash'])

    def test_rpc_history_fail_closed(self):
        previous = {'anchors': {'60': header(60)['hash']}}
        with self.assertRaises(ValueError):
            audit_node(snap(500, 563), previous, lambda n: (_ for _ in ()).throw(ValueError('RPC failed')))

    def test_mismatched_header_height_fails_closed(self):
        previous = {'anchors': {'60': header(60)['hash']}}
        with self.assertRaises(ValueError):
            audit_node(snap(500, 563), previous, lambda n: header(n+1))

    def test_saved_anchor_corruption(self):
        for bad in ({'06': header(6)['hash']}, {'6': '0' * 63},
                    {'-1': header(1)['hash']}, {'1.0': header(1)['hash']}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                audit_node(snap(1, 10), {'anchors': bad}, lambda n: header(n))

    def test_saved_cursor_corruption(self):
        with self.assertRaises(ValueError):
            audit_node(snap(1, 10), {'audit_cursor': True}, lambda n: header(n))

    def test_anchor_capacity_fail_closed(self):
        anchors = {str(i): header(i)['hash'] for i in range(MAX_ANCHORS+1)}
        with self.assertRaises(ValueError):
            audit_node(snap(1, 10), {'anchors': anchors}, lambda n: header(n))

    def test_rotation_keeps_old_observations(self):
        anchors = {str(i*60): header(i*60)['hash'] for i in range(1, 15)}
        first, state = audit_node(snap(1000, 1063), {'anchors': anchors},
                                  lambda n: header(n))
        self.assertEqual(first, [])
        self.assertEqual(state['anchors'], anchors)
        self.assertGreater(state['audit_cursor'], 0)


if __name__ == '__main__':
    unittest.main()
