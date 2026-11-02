"""Bounded FIFO native RandomX verification for the LOCAL research listener.

Strictly in-memory, one verifier subprocess shared by the socket listener.
Never credits shares, submits blocks, calls a wallet or creates a payout.
Each socket handler awaits its submitted work before accepting another frame,
giving at most one outstanding share per connected worker/session.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable

from .daemon_job_source import DaemonJobSource


class VerificationQueueError(ValueError):
    pass


@dataclass(frozen=True)
class _Pending:
    source: DaemonJobSource
    worker: str
    job_id: str
    nonce: str
    digest: str
    result: asyncio.Future


class FairNativeVerificationQueue:
    """FIFO, at most one native verification running; max pending work is bounded."""

    def __init__(self, verifier: Callable, *, max_pending: int = 8,
                 wait_timeout: float = 25):
        if not callable(verifier):
            raise ValueError("trusted native RandomX verifier required")
        if type(max_pending) is not int or not 1 <= max_pending <= 8:
            raise ValueError("research queue size must be 1..8")
        if type(wait_timeout) not in (int, float) or not 1 <= wait_timeout <= 60:
            raise ValueError("research queue timeout must be 1..60 seconds")
        self.verifier = verifier
        self.queue: asyncio.Queue[_Pending] = asyncio.Queue(maxsize=max_pending)
        self.wait_timeout = wait_timeout
        self.task: asyncio.Task | None = None
        self.closed = False
        self.inflight = 0

    def start(self):
        if self.task is not None or self.closed:
            raise ValueError("queue already started or closed")
        self.task = asyncio.create_task(self._run(), name="forgecoin-native-randomx-fifo")

    async def _run(self):
        try:
            while True:
                item = await self.queue.get()
                try:
                    if item.result.cancelled():
                        continue
                    self.inflight += 1
                    try:
                        result = await asyncio.to_thread(
                            item.source.inspect, item.worker, item.job_id,
                            item.nonce, item.digest, self.verifier,
                        )
                    except Exception as exc:
                        if not item.result.done():
                            item.result.set_exception(exc)
                    else:
                        if not item.result.done():
                            item.result.set_result(result)
                    finally:
                        self.inflight -= 1
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            raise

    async def verify(self, source: DaemonJobSource, worker: str, job_id: str,
                     nonce: str, digest: str):
        if self.closed or self.task is None or self.task.done():
            raise VerificationQueueError("native verifier queue not available")
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        item = _Pending(source, worker, job_id, nonce, digest, future)
        try:
            self.queue.put_nowait(item)
        except asyncio.QueueFull as exc:
            future.cancel()
            raise VerificationQueueError("native verification queue full; retry") from exc
        try:
            return await asyncio.wait_for(future, timeout=self.wait_timeout)
        except asyncio.TimeoutError as exc:
            raise VerificationQueueError("native verifier deadline exceeded") from exc
        finally:
            # Cancellation during a blocked/native call must never yield a
            # reported success after the socket has abandoned the request.
            if not future.done():
                future.cancel()

    async def close(self):
        if self.closed:
            return
        self.closed = True
        # Outstanding caller tasks are already stopped by the listener.
        while not self.queue.empty():
            item = self.queue.get_nowait()
            if not item.result.done():
                item.result.cancel()
            self.queue.task_done()
        if self.task is not None:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
            self.task = None
