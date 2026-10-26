"""Loopback socket integration over real protocol frames; fake daemon and digest."""
import asyncio
import json
import threading
import unittest

from .daemon_job_source import DaemonJobSource
from .native_stratum_research import NativeResearchListener
from .test_daemon_job_source import FakeDaemon, GENESIS, OTHER_TIP


class NativeStratumLoopbackTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.daemon = FakeDaemon()
        self.calls = 0
        def fake_native(seed,blob):
            self.calls += 1
            self.assertEqual(len(seed), 32)
            self.assertEqual(blob[39:43],bytes.fromhex("01020304"))
            return bytes(32)
        self.fake_native = fake_native
        self.listener = NativeResearchListener(self.make_source, fake_native)
        self.port = await self.listener.start()
        self.clients = []

    def make_source(self):
        return DaemonJobSource(
            self.daemon,expected_genesis_hash=GENESIS,expected_nettype="testnet",
            wallet_address="DISPOSABLE_TEST_ADDRESS",
        )

    async def asyncTearDown(self):
        for _, writer in self.clients:
            writer.close()
        await self.listener.close()

    async def client(self):
        pair = await asyncio.open_connection("127.0.0.1",self.port)
        self.clients.append(pair)
        return pair

    async def request(self, pair, request_id, method, params):
        reader,writer = pair
        writer.write((json.dumps({
            "id":request_id,"jsonrpc":"2.0","method":method,"params":params
        })+"\n").encode())
        await writer.drain()
        answer=await asyncio.wait_for(reader.readline(),timeout=8)
        self.assertTrue(answer)
        return json.loads(answer)

    async def login(self,pair):
        reply=await self.request(pair,1,"login",{
            "login":"local-test-no-real-payout","algo":["rx/0"],
        })
        self.assertIsNone(reply["error"])
        self.assertEqual(reply["result"]["status"],"RESEARCH_ONLY_UNCREDITED")
        self.assertFalse(reply["result"]["credited"])
        self.assertEqual(reply["result"]["job"]["algo"],"rx/0")
        return reply["result"]

    def submit_params(self,login):
        return {"id":login["id"],"job_id":login["job"]["job_id"],
                "nonce":"01020304","result":"00"*32}

    async def test_real_socket_login_and_digest_are_uncredited(self):
        pair=await self.client()
        login=await self.login(pair)
        reply=await self.request(pair,2,"submit",self.submit_params(login))
        self.assertIsNone(reply["error"])
        self.assertEqual(reply["result"]["status"],"POW_THRESHOLD_MET_UNCREDITED")
        self.assertFalse(reply["result"]["credited"])
        self.assertFalse(reply["result"]["submitted_block"])
        self.assertEqual(self.calls,1)
        self.assertEqual(self.daemon.calls[0][0],"get_block_header_by_height")
        self.assertIn("get_block_template",[method for method,_ in self.daemon.calls])

    async def test_duplicate_and_cross_worker_submission(self):
        a,b=await self.client(),await self.client()
        al,bl=await self.login(a),await self.login(b)
        self.assertNotEqual(al["job"]["job_id"],bl["job"]["job_id"])
        self.assertNotEqual(al["job"]["blob"],bl["job"]["blob"])
        foreign=self.submit_params(al)
        foreign["id"]=bl["id"]
        reply=await self.request(b,2,"submit",foreign)
        self.assertIn("another session/job",reply["error"]["message"])
        self.assertEqual(self.calls,0)
        reply=await self.request(a,2,"submit",self.submit_params(al))
        self.assertIsNone(reply["error"])
        reply=await self.request(a,3,"submit",self.submit_params(al))
        self.assertIn("verification failed",reply["error"]["message"])
        self.assertEqual(self.calls,1)

    async def test_wrong_digest_and_tip_change_fail_closed(self):
        a=await self.client()
        login=await self.login(a)
        bad=self.submit_params(login)
        bad["result"]="ff"*32
        reply=await self.request(a,2,"submit",bad)
        self.assertIn("digest disagrees",reply["error"]["message"])
        self.daemon.tip=OTHER_TIP
        reply=await self.request(a,3,"submit",self.submit_params(login))
        self.assertIn("tip changed",reply["error"]["message"])
        self.assertEqual(self.calls,1)

    async def test_wrong_network_refuses_login_and_no_share(self):
        self.daemon.nettype="mainnet"
        a=await self.client()
        result=await self.request(a,1,"login",{"login":"worker"})
        self.assertIsNotNone(result["error"])
        self.assertIn("network",result["error"]["message"])
        self.assertEqual(self.calls,0)

    async def test_capacity_on_actual_socket(self):
        self.listener.sessions.limit=1
        a=await self.client()
        await self.login(a)
        b=await self.client()
        reply=json.loads(await asyncio.wait_for(b[0].readline(),timeout=2))
        self.assertIn("capacity",reply["error"]["message"])
        self.assertEqual(self.calls,0)

    async def test_invalid_algorithm_and_mutation_never_accepted(self):
        a=await self.client()
        reply=await self.request(a,1,"login",{"login":"test","algo":["rx/wow"]})
        self.assertIn("rx/0",reply["error"]["message"])
        b=await self.client()
        reply=await self.request(b,1,"send_money",{"amount":5})
        self.assertIn("unsupported method",reply["error"]["message"])
        self.assertEqual(self.calls,0)

    async def test_overlarge_socket_frame_terminates(self):
        a=await self.client()
        a[1].write(b"x"*4097+b"\n")
        await a[1].drain()
        self.assertEqual(await asyncio.wait_for(a[0].readline(),timeout=2),b"")

    async def test_fifo_waits_for_first_worker_then_verifies_second(self):
        a,b=await self.client(),await self.client()
        al,bl=await self.login(a),await self.login(b)
        entered,release=threading.Event(),threading.Event()
        original=self.listener.native_queue.verifier
        order=[]
        def slow(s,blob):
            order.append(blob)
            entered.set()
            if not release.wait(3):
                raise RuntimeError("test barrier timed out")
            return original(s,blob)
        self.listener.native_queue.verifier=slow
        first=asyncio.create_task(self.request(a,2,"submit",self.submit_params(al)))
        second=None
        try:
            self.assertTrue(await asyncio.to_thread(entered.wait,2))
            second=asyncio.create_task(self.request(b,2,"submit",self.submit_params(bl)))
            await asyncio.sleep(0.06)
            self.assertFalse(second.done(), "second share should be queued, not rejected as busy")
            self.assertEqual(self.calls,0)
        finally:
            release.set()
        self.assertIsNone((await first)["error"])
        self.assertIsNone((await second)["error"])
        self.assertEqual(len(order),2)
        self.assertEqual(self.calls,2)
        self.listener.native_queue.verifier=original


if __name__=="__main__":
    unittest.main()
