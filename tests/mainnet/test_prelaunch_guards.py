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
    def test_genesis_output_rejected_in_cached_and_direct_ring_scan(self):
        s = source("src/cryptonote_core/blockchain.cpp")
        scan = s[s.index("bool Blockchain::scan_outputkeys_for_indexes"):s.index("bool Blockchain::have_tx_keyimg_as_spent")] if (
            "bool Blockchain::have_tx_keyimg_as_spent" in s[s.index("bool Blockchain::scan_outputkeys_for_indexes"):]
        ) else s[s.index("bool Blockchain::scan_outputkeys_for_indexes"):]
        member_loop = scan[scan.index("for (const uint64_t& i : absolute_offsets)"):]
        cached = "output_index = outputs.at(count);"
        direct = "output_index = m_db->get_output_key(tx_in_to_key.amount, i);"
        guard = "forgecoin_prelaunch::output_allowed(m_nettype == MAINNET, output_index.height)"
        visitor = "vis.handle_output(output_index.unlock_time, output_index.pubkey, output_index.commitment)"
        self.assertIn("outputs = its->second", scan)
        self.assertIn("m_db->get_output_key(epee::span<const uint64_t>", scan)
        self.assertIn(cached, member_loop)
        self.assertIn(direct, member_loop)
        self.assertLess(member_loop.index(cached), member_loop.index(guard))
        self.assertLess(member_loop.index(direct), member_loop.index(guard))
        self.assertLess(member_loop.index(guard), member_loop.index(visitor))
        tx_checker = s[s.index("bool Blockchain::check_tx_input("):]
        self.assertIn("scan_outputkeys_for_indexes(tx_version, txin, vi, tx_prefix_hash", tx_checker)

    def test_genesis_rpc_output_height_matches_serialized_actual_public_key(self):
        script = source("tools/smoke_frozen_prelaunch_daemon.py")
        self.assertIn("extract_genesis_pubkey(manifest)", script)
        self.assertIn('call_rpc(rpc_port, "get_outs", {', script)
        self.assertIn('"amount": manifest["currency"]["genesis_output_atomic"]', script)
        self.assertIn('"index": 0', script)
        self.assertIn('type(indexed_height) is not int or indexed_height != 0', script)
        self.assertIn('indexed_key.lower() != expected_key', script)
        self.assertIn("actual daemon LMDB genesis output key matches", script)

    def test_fixed_difficulty_override_is_rejected_on_mainnet(self):
        core = source("src/cryptonote_core/cryptonote_core.cpp")
        init = core[core.index("const difficulty_type fixed_difficulty = command_line::get_arg(vm, arg_fixed_difficulty);"):]
        self.assertIn("m_nettype == MAINNET && fixed_difficulty != 0", init)
        self.assertIn("Mainnet consensus forbids --fixed-difficulty", init)
        self.assertLess(init.index("if (m_nettype == MAINNET && fixed_difficulty != 0)"),
                        init.index("m_blockchain_storage.init(db.release()"))

    def test_native_miner_and_template_paths_are_locked(self):
        s = source("src/cryptonote_basic/miner.cpp")
        start = s[s.index("bool miner::start("):]
        self.assertLess(start.index("forgecoin_prelaunch::mining_allowed"), start.index("m_block_reward ="))
        self.assertIn("m_prelaunch_nettype = nettype", s)
        self.assertEqual(source("src/cryptonote_core/cryptonote_core.cpp").count("forgecoin_prelaunch::mining_allowed(get_nettype() == MAINNET)"), 3)
