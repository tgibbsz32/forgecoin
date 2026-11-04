#!/usr/bin/env python3
"""No-secret localhost HTTP trace proxy for disposable native wallet QA.

Never logs payload, credentials, authorization proof, challenge nonce,
keys, addresses, wallet paths or request content. Prints only auth-header
presence, previous-challenge nonce match and HTTP status.
NOT production code or a general HTTP proxy.
"""
import argparse
import re
import socket
import socketserver
import sys
import threading

last_nonce = None
lock = threading.Lock()
number = 0


def header_value(headers, field):
    found = re.search(rb"(?im)^" + field.encode("ascii") + rb":\s*([^\r\n]+)", headers)
    return found.group(1).decode("ascii", "replace") if found else ""


def digest_nonce(header):
    found = re.search(r'nonce="([^"]{1,200})"', header)
    return found.group(1) if found else None


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        global last_nonce, number
        self.request.settimeout(7)
        try:
            packet = bytearray()
            while b"\r\n\r\n" not in packet and len(packet) < 65536:
                part = self.request.recv(4096)
                if not part:
                    return
                packet += part
            if b"\r\n\r\n" not in packet:
                return
            header, tail = bytes(packet).split(b"\r\n\r\n", 1)
            size = header_value(header, "Content-Length")
            length = int(size) if size.isdigit() else 0
            if length < 0 or length > 524288:
                return
            while len(tail) < length:
                tail += self.request.recv(min(4096, length - len(tail)))
            packet = header + b"\r\n\r\n" + tail
            auth = header_value(header, "Authorization")
            given_nonce = digest_nonce(auth)
            with lock:
                number += 1
                sequence = number
                matches = bool(given_nonce and given_nonce == last_nonce)
            print("QA_PROXY_REQUEST=%d AUTH=%s NONCE_MATCH_PREVIOUS=%s" % (
                sequence, bool(auth), matches), flush=True)
            with socket.create_connection(("127.0.0.1", self.server.wallet_port), 6) as remote:
                remote.settimeout(6)
                remote.sendall(packet)
                response = bytearray()
                try:
                    while len(response) < 1024 * 1024:
                        chunk = remote.recv(16384)
                        if not chunk:
                            break
                        response += chunk
                except socket.timeout:
                    pass
            if response:
                response_header = bytes(response).split(b"\r\n\r\n", 1)[0]
                status_line = response_header.split(b"\r\n", 1)[0]
                code = status_line.split()[1].decode("ascii", "ignore") if len(status_line.split()) > 1 else "unknown"
                header_lines = response_header.split(b"\r\n")
                challenges = [part.decode("ascii", "replace") for part in header_lines
                              if part.lower().startswith(b"www-authenticate:")]
                nonce = digest_nonce(challenges[0]) if challenges else None
                with lock:
                    if nonce:
                        last_nonce = nonce
                print("QA_PROXY_RESPONSE=%d STATUS=%s CHALLENGES=%d" % (
                    sequence, code, len(challenges)), flush=True)
                self.request.sendall(response)
        except (OSError, ValueError):
            print("QA_PROXY_TRANSPORT_FAILURE", flush=True)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen-port", type=int, required=True)
    parser.add_argument("--wallet-port", type=int, required=True)
    args = parser.parse_args()
    if not 1024 <= args.listen_port <= 65535 or not 1024 <= args.wallet_port <= 65535:
        raise SystemExit("Invalid private QA port")
    with Server(("127.0.0.1", args.listen_port), Handler) as server:
        server.wallet_port = args.wallet_port
        print("QA_PROXY_READY", flush=True)
        server.serve_forever(poll_interval=0.2)


if __name__ == "__main__":
    main()
