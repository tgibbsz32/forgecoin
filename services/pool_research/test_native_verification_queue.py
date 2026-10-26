"""Bounded FIFO, cancellation and overload checks; no native miner required."""
import asyncio
import threading
import unittest

from .native_verification_queue import FairNativeVerificationQueue, VerificationQueueError
from .pow_boundary import VerificationResult


class FakeSource:
    def __init__(self, callback):
        self.callback = callback

    def inspect(self, worker, job_id, nonce, digest, verifier):
        self.callback(worker)
        return VerificationResult("POW_THRESHOLD_MET_UNCREDITED", "a" * 64)


class QueueTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.queue = FairNativeVerificationQueue(lambda seed, blob: bytes(32), max_pending=2)
        self.queue.start()

    async def asyncTearDown(self):
        await self.queue.close()

    async def test_fifo_three_sessions(self):
        entered, release = threading.Event(), threading.Event()
        processed = []
        def fn(worker):
            processed.append(worker)
            if worker == "a":
                entered.set()
                if not release.wait(3):
                    raise RuntimeError("barrier timed out")
        source = FakeSource(fn)
        async def verify(worker):
            return await self.queue.verify(source, worker, "job", "01020304", "ff" * 32)
        first = asyncio.create_task(verify("a"))
        second = third = None
        try:
            self.assertTrue(await asyncio.to_thread(entered.wait, 2))
            second = asyncio.create_task(verify("b"))
            await asyncio.sleep(.02)
            third = asyncio.create_task(verify("c"))
            await asyncio.sleep(.04)
            self.assertEqual(processed, ["a"])
            self.assertEqual(self.queue.queue.qsize(), 2)
        finally:
            release.set()
        results = await asyncio.gather(first, second, third)
        self.assertEqual(processed, ["a", "b", "c"])
        self.assertTrue(all(x.status == "POW_THRESHOLD_MET_UNCREDITED" for x in results))
        self.assertEqual(self.queue.inflight, 0)

    async def test_overflow_is_fast_and_does_not_run(self):
        first_entered, release = threading.Event(), threading.Event()
        called = []
        def fn(worker):
            called.append(worker)
            if worker == "a":
                first_entered.set()
                if not release.wait(3):
                    raise RuntimeError("barrier timed out")
        source = FakeSource(fn)
        def create(worker):
            return asyncio.create_task(self.queue.verify(
                source, worker, "job", "01020304", "ff" * 32
            ))
        first = create("a")
        second = None
        try:
            self.assertTrue(await asyncio.to_thread(first_entered.wait, 2))
            second = create("b")
            await asyncio.sleep(.03)
            third = create("c")
            await asyncio.sleep(.03)
            with self.assertRaisesRegex(VerificationQueueError, "queue full"):
                await self.queue.verify(source, "d", "job", "01020304", "ff" * 32)
            self.assertEqual(called, ["a"])
        finally:
            release.set()
        await asyncio.gather(first, second, third)
        self.assertNotIn("d", called)

    async def test_cancel_pending_never_invokes_native(self):
        first_entered, release = threading.Event(), threading.Event()
        called = []
        def fn(worker):
            called.append(worker)
            if worker == "a":
                first_entered.set()
                if not release.wait(3):
                    raise RuntimeError("barrier timed out")
        source = FakeSource(fn)
        first = asyncio.create_task(self.queue.verify(source, "a", "job", "01", "ff"))
        second = None
        try:
            self.assertTrue(await asyncio.to_thread(first_entered.wait, 2))
            second = asyncio.create_task(self.queue.verify(source, "b", "job", "01", "ff"))
            await asyncio.sleep(.02)
            second.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await second
        finally:
            release.set()
        await first
        await self.queue.queue.join()
        self.assertEqual(called, ["a"])

    async def test_closed_queue_rejects(self):
        await self.queue.close()
        with self.assertRaisesRegex(VerificationQueueError, "not available"):
            await self.queue.verify(FakeSource(lambda _: None), "a", "job", "00", "ff")


if __name__ == "__main__":
    unittest.main()
