"""Exercise the template capture tool against a disposable local HTTP fixture."""
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from services.pool_research.capture_template import capture, local_opener

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.headers.get("X-Redirect-Test"):
            self.send_response(302)
            self.send_header("Location", "http://example.invalid/json_rpc")
            self.end_headers()
            return
        if self.path!="/json_rpc":
            self.send_error(404);return
        count=int(self.headers.get("Content-Length","0"))
        body=json.loads(self.rfile.read(count))
        if body.get("method")!="get_block_template" or body["params"].get("reserve_size")!=8:
            self.send_error(400);return
        reply={"jsonrpc":"2.0","id":body["id"],"result":{
            "height":17,"difficulty":500000,"expected_reward":2384185222,
            "seed_hash":"a1"*32,"blocktemplate_blob":"01"*128,
            "blockhashing_blob":"02"*80,"reserved_offset":40}}
        data=json.dumps(reply).encode()
        self.send_response(200);self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(data)));self.end_headers()
        self.wfile.write(data)
    def log_message(self,*args):pass

class CaptureTests(unittest.TestCase):
    def test_environment_proxy_is_ignored(self):
        with patch.dict("os.environ", {"http_proxy": "http://127.0.0.1:1", "no_proxy": ""}):
            self.test_local_fixture()

    def test_redirect_rejected(self):
        from urllib.request import Request
        request = Request(f"http://127.0.0.1:{self.server.server_port}/json_rpc",
                          b"{}", {"X-Redirect-Test": "yes"})
        with self.assertRaisesRegex(ValueError, "redirects are forbidden"):
            local_opener().open(request, timeout=3)

    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(3)
    def test_local_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"sanitized.json"
            result=capture(f"http://127.0.0.1:{self.server.server_port}/json_rpc","DISPOSABLE_TEST_ADDRESS",path)
            self.assertEqual(result["height"],17)
            output=path.read_text()
            self.assertNotIn("DISPOSABLE_TEST_ADDRESS",output)
            self.assertNotIn("blocktemplate_blob",output)
    def test_reject_external_urls(self):
        with tempfile.TemporaryDirectory() as d:
            for url in ("https://127.0.0.1:39481/json_rpc","http://example.com/json_rpc",
                        "http://127.0.0.1:39481/admin","http://user:pass@127.0.0.1/json_rpc"):
                with self.subTest(url=url),self.assertRaises(ValueError):
                    capture(url,"TEST",Path(d)/"out.json")
if __name__=="__main__":unittest.main()
