import unittest
from pathlib import Path
R = Path(__file__).resolve().parents[2]
def source(p): return (R / p).read_text(encoding="utf-8")
class PrelaunchWiring(unittest.TestCase):
    def test_main_and_alternative_paths_reject_before_processing(self):
        s = source("src/cryptonote_core/blockchain.cpp")
        main = s[s.index("bool Blockchain::handle_block_to_main_chain(const block& bl, const crypto::hash& id,"):]
        self.assertLess(main.index("forgecoin_prelaunch::block_allowed"), main.index("m_db->add_block"))
        alt = s[s.index("bool Blockchain::handle_alternative_block("):]
        self.assertLess(alt.index("forgecoin_prelaunch::block_allowed"), alt.index("is_alternative_block_allowed"))
        self.assertIn("refusing a mainnet database containing blocks beyond genesis", s)
    def test_output_exclusion_precedes_signature_visitor(self):
        s = source("src/cryptonote_core/blockchain.cpp")
        scan = s[s.index("bool Blockchain::scan_outputkeys_for_indexes"):]
        self.assertLess(scan.index("forgecoin_prelaunch::output_allowed"), scan.index("vis.handle_output"))
        self.assertIn("output_index.height", scan)
    def test_native_miner_and_template_paths_are_locked(self):
        s = source("src/cryptonote_basic/miner.cpp")
        start = s[s.index("bool miner::start("):]
        self.assertLess(start.index("forgecoin_prelaunch::mining_allowed"), start.index("m_block_reward ="))
        self.assertIn("m_prelaunch_nettype = nettype", s)
        self.assertEqual(source("src/cryptonote_core/cryptonote_core.cpp").count("forgecoin_prelaunch::mining_allowed(get_nettype() == MAINNET)"), 3)
