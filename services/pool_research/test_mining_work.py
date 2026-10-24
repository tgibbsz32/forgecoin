from dataclasses import replace
import unittest
from services.pool_research.mining_work import decode_header, prepare_work, read_varint
from services.pool_research.template_adapter import Template


def fixture():
    header = bytes([16, 16, 128, 1]) + b"p" * 32 + b"\0" * 4
    return Template(1, 500000, 1, b"s" * 32, header + b"b" * 100,
                    header + b"r" * 32 + b"\x01", 100, 8)


class MiningWorkTests(unittest.TestCase):
    def test_header_and_nonce_byte_order(self):
        work = prepare_work(fixture())
        self.assertEqual(work.header.timestamp, 128)
        self.assertEqual(work.header.nonce_offset, 36)
        self.assertEqual(work.transaction_count, 1)
        hashing, block = work.with_nonce(0x12345678)
        self.assertEqual(hashing[36:40], b"\x78\x56\x34\x12")
        self.assertEqual(decode_header(block).nonce, 0x12345678)
        for new, old in ((hashing, work.hashing_blob), (block, work.block_blob)):
            self.assertEqual(new[:36] + new[40:], old[:36] + old[40:])
        self.assertEqual(work.header.nonce, 0)

    def test_nonce_limits(self):
        work = prepare_work(fixture())
        for nonce in (0, 2**32 - 1):
            self.assertEqual(decode_header(work.with_nonce(nonce)[0]).nonce, nonce)
        for nonce in (-1, 2**32, True, 1.5):
            with self.subTest(nonce=nonce), self.assertRaises(ValueError):
                work.with_nonce(nonce)

    def test_malformed_varints_and_headers(self):
        for value in (b"", b"\x80", b"\x80\0", b"\xff" * 9 + b"\x02"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                read_varint(value, 0)
        with self.assertRaises(ValueError):
            decode_header(b"\x80\x02\x01\x01" + b"\0" * 36)
        with self.assertRaises(ValueError):
            decode_header(b"\x01\x01\x01")

    def test_inconsistent_or_malformed_work(self):
        template = fixture()
        malformed = [replace(template, blocktemplate_blob=b"\x11" + template.blocktemplate_blob[1:]),
                     replace(template, reserved_offset=1),
                     replace(template, blockhashing_blob=template.blockhashing_blob[:-1]),
                     replace(template, blockhashing_blob=template.blockhashing_blob[:-1] + b"\0"),
                     replace(template, blockhashing_blob=template.blockhashing_blob + b"\0")]
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(ValueError):
                prepare_work(value)
