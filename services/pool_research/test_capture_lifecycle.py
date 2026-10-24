"""Failure injection tests: never launch binaries or connect to a daemon."""
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from services.pool_research.integration_capture import run


class CaptureLifecycleTests(unittest.TestCase):
    def exercise(self, *, summary=None, capture_error=None, shutdown_error=None,
                 info=None, invalid_daemon=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            daemon, wallet = root / "forged.exe", root / "forge-wallet-cli.exe"
            if not invalid_daemon:
                daemon.touch()
            wallet.touch()
            output = root / "evidence.json"
            # Failure must not overwrite an earlier successful artifact.
            output.write_text("prior evidence")
            generated_roots = []

            def create_wallet(command, **kwargs):
                path = Path(command[command.index("--generate-new-wallet") + 1])
                generated_roots.append(path.parent)
                Path(str(path) + ".address.txt").write_text("DISPOSABLE_TEST_ADDRESS")
                return Mock(returncode=0)

            process = Mock(returncode=None, stdin=io.BytesIO())
            process.poll.return_value = None

            def communicate(*args, **kwargs):
                if shutdown_error:
                    raise shutdown_error
                process.returncode = 0

            def kill():
                process.returncode = -9

            process.communicate.side_effect = communicate
            process.kill.side_effect = kill
            info = info or {"offline": True, "height": 1,
                            "incoming_connections_count": 0, "outgoing_connections_count": 0}
            summary = summary or {"height": 1, "seed_hash": "ab" * 32}
            with patch("services.pool_research.integration_capture.socket.socket"), \
                 patch("services.pool_research.integration_capture.subprocess.run", side_effect=create_wallet) as create, \
                 patch("services.pool_research.integration_capture.subprocess.Popen", return_value=process) as launch, \
                 patch("services.pool_research.integration_capture.rpc", side_effect=[info, {"block_header": {"hash": "ab" * 32}}]), \
                 patch("services.pool_research.integration_capture.capture", return_value=summary, side_effect=capture_error):
                with self.assertRaises((RuntimeError, ValueError)):
                    run(daemon, wallet, output)
            self.assertEqual(output.read_text(), "prior evidence")
            for generated in generated_roots:
                self.assertFalse(generated.exists(), "wallet and database must be removed")
            if invalid_daemon:
                create.assert_not_called()
                launch.assert_not_called()
            else:
                process.communicate.assert_called_once_with(b"exit\n", timeout=20)
                self.assertTrue(process.stdin.closed)
                if shutdown_error:
                    process.kill.assert_called_once()
                    process.wait.assert_called_once_with(timeout=10)

    def test_invalid_daemon_fails_before_wallet_creation(self):
        self.exercise(invalid_daemon=True)

    def test_capture_rejection_cleans_up(self):
        self.exercise(capture_error=ValueError("invalid template"))

    def test_peer_connection_rejected_and_cleaned_up(self):
        self.exercise(info={"offline": True, "height": 1,
                            "incoming_connections_count": 1, "outgoing_connections_count": 0})

    def test_wrong_height_or_seed_not_published(self):
        for summary in ({"height": 2, "seed_hash": "ab" * 32},
                        {"height": 1, "seed_hash": "cd" * 32}):
            with self.subTest(summary=summary):
                self.exercise(summary=summary)

    def test_shutdown_timeout_kills_process_and_rejects_evidence(self):
        self.exercise(shutdown_error=subprocess.TimeoutExpired("forged", 20))

    def test_broken_stdin_kills_process_and_rejects_evidence(self):
        self.exercise(shutdown_error=BrokenPipeError())
