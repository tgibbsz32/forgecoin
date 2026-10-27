import unittest

if __package__:
    from .model import CapacityExceeded, WorkerRegistry, allocate_reward
else:
    # Preserve direct script execution for the original offline research test.
    from model import CapacityExceeded, WorkerRegistry, allocate_reward


class PoolResearchTests(unittest.TestCase):
    def test_exactly_one_hundred_workers(self):
        registry = WorkerRegistry()
        for n in range(100):
            self.assertTrue(registry.connect(f"connection-{n}"))
        with self.assertRaises(CapacityExceeded):
            registry.connect("connection-100")
        self.assertFalse(registry.connect("connection-99"))
        registry.disconnect("connection-0")
        self.assertTrue(registry.connect("connection-100"))

    def test_fee_and_two_miners(self):
        allocation = allocate_reward(100_000_000_000, {"miner-a": 3, "miner-b": 1})
        self.assertEqual(allocation.fee_atomic, 1_000_000_000)
        self.assertEqual(allocation.miner_atomic["miner-a"], 74_250_000_000)
        self.assertEqual(allocation.miner_atomic["miner-b"], 24_750_000_000)

    def test_dust_and_remainder(self):
        a = allocate_reward(7, {"b": 1, "a": 1, "c": 1})
        self.assertEqual(sum(a.miner_atomic.values()) + a.fee_atomic, 7)
        self.assertEqual(a.miner_atomic, {"b": 2, "a": 3, "c": 2})

    def test_invalid_inputs(self):
        for reward, weights in [(-1, {"a": 1}), (1, {}), (1, {"a": 0}),
                                (1, {"a": -1}), (1.2, {"a": 1})]:
            with self.assertRaises(ValueError):
                allocate_reward(reward, weights)
        with self.assertRaises(ValueError):
            WorkerRegistry(101)


if __name__ == "__main__":
    unittest.main()
