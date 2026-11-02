"""Loopback-only Stratum-shaped socket for daemon-issued native RandomX jobs.

Research fixture only: one non-refreshable daemon job per connection, no mining
payout address verification, share credits, chain submission, ledger, or TLS.
Bounded capacity/frames/requests. Never bind a public interface. Real production
mining pool operation is intentionally unavailable.
"""
from __future__ import annotations

import asyncio
import json
import secrets
from typing import Callable

from .daemon_job_source import DaemonJobError, DaemonJobSource
from .native_verification_queue import FairNativeVerificationQueue, VerificationQueueError
from .stratum_protocol import MAX_FRAME_BYTES, ProtocolError, SessionTable


class NativeResearchListener:
    def __init__(self, source_factory: Callable[[], DaemonJobSource],
                 verifier: Callable, *, capacity: int = 4, difficulty: int = 1,
                 idle_timeout: int = 10, request_limit: int = 32):
        if not callable(source_factory) or not callable(verifier):
            raise ValueError("explicit daemon source factory and trusted native verifier required")
        if type(capacity) is not int or not 1 <= capacity <= 8:
            raise ValueError("research listener capacity must be 1..8")
        if type(difficulty) is not int or not 1 <= difficulty <= 0xffffffff:
            raise ValueError("invalid worker share difficulty")
        if type(idle_timeout) is not int or not 1 <= idle_timeout <= 30:
            raise ValueError("invalid idle timeout")
        if type(request_limit) is not int or not 1 <= request_limit <= 64:
            raise ValueError("invalid request limit")
        self.source_factory = source_factory
        self.verifier = verifier
        self.sessions = SessionTable(capacity)
        self.difficulty = difficulty
        self.idle_timeout = idle_timeout
        self.request_limit = request_limit
        self.server = None
        self.writers = set()
        self.tasks = set()
        self.native_queue = FairNativeVerificationQueue(
            verifier, max_pending=capacity, wait_timeout=25
        )

    async def start(self) -> int:
        if self.server is not None:
            raise ValueError("already listening")
        self.server = await asyncio.start_server(
            self.handle, host="127.0.0.1", port=0, limit=MAX_FRAME_BYTES
        )
        self.native_queue.start()
        return self.server.sockets[0].getsockname()[1]

    async def close(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        for writer in tuple(self.writers):
            writer.close()
        if self.tasks:
            await asyncio.gather(*tuple(self.tasks), return_exceptions=True)
        await self.native_queue.close()

    async def send(self, writer, request_id, *, result=None, error=None) -> None:
        response = {"id": request_id, "jsonrpc": "2.0", "result": result, "error": error}
        writer.write((json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8"))
        await asyncio.wait_for(writer.drain(), timeout=3)

    async def handle(self, reader, writer) -> None:
        task = asyncio.current_task()
        self.tasks.add(task)
        self.writers.add(writer)
        connection = secrets.token_hex(16)
        try:
            try:
                self.sessions.open(connection)
            except ProtocolError:
                await self.send(writer, None, error={"code": -1, "message": "capacity reached"})
                return
            source = None
            current_job = None
            for _ in range(self.request_limit):
                raw = await asyncio.wait_for(reader.readline(), timeout=self.idle_timeout)
                if not raw:
                    return
                if len(raw) > MAX_FRAME_BYTES or not raw.endswith(b"\n"):
                    raise ProtocolError("invalid frame length")
                req_id = None
                try:
                    request = self.sessions.inspect(connection, raw)
                    req_id = request["id"]
                    params = request["params"]
                    method = request["method"]
                    if method == "login":
                        if "algo" in params and "rx/0" not in params["algo"]:
                            await self.send(
                                writer, req_id,
                                error={"code": -1, "message": "miner must support rx/0"}
                            )
                            return
                        source = self.source_factory()
                        if not isinstance(source, DaemonJobSource):
                            raise DaemonJobError("invalid native job source")
                        # RPC is blocking. No chain I/O happens on the event loop.
                        current_job = await asyncio.to_thread(
                            source.issue, connection, self.difficulty
                        )
                        await self.send(writer, req_id, result={
                            "id": connection, "status": "RESEARCH_ONLY_UNCREDITED",
                            "credited": False, "job": current_job.xmrig_job(),
                        })
                    elif method == "keepalived":
                        await self.send(writer, req_id, result={"status": "KEEPALIVED"})
                    elif method == "submit":
                        if (source is None or current_job is None
                                or params["id"] != connection
                                or params["job_id"] != current_job.job_id):
                            raise ProtocolError("share belongs to another session/job")
                        # FIFO serializes access to a persistent native RandomX
                        # worker without dropping a second miner's share merely
                        # because another socket is already hashing. Each socket
                        # awaits its share; it cannot fill the bounded queue.
                        result = await self.native_queue.verify(
                            source, connection, current_job.job_id,
                            params["nonce"], params["result"]
                        )
                        if result.status != "POW_THRESHOLD_MET_UNCREDITED":
                            raise ProtocolError("unrecognized native research result")
                        await self.send(writer, req_id, result={
                            "status": "POW_THRESHOLD_MET_UNCREDITED",
                            "credited": False, "submitted_block": False,
                        })
                except (ProtocolError, DaemonJobError, VerificationQueueError) as exc:
                    await self.send(writer, req_id,
                                    error={"code": -1, "message": str(exc)})
        except (OSError, ValueError, asyncio.TimeoutError):
            # Length abuse, idle clients or unparseable transport close the socket.
            pass
        finally:
            self.sessions.close(connection)
            self.writers.discard(writer)
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), timeout=3)
            except (OSError, asyncio.TimeoutError):
                pass
            self.tasks.discard(task)
