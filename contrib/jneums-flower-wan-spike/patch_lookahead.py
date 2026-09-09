"""Patch flwr's supercore/grpc.py: raise HTTP/2 per-stream lookahead to 16 MB.

Applies to both the client channel (create_channel) and the server options
(generic_create_grpc_server) — the latter is what governs the node->SuperLink
push leg, so the patch must be applied (and the daemon restarted) on BOTH the
SuperNode and SuperLink hosts, in the environment their daemons actually run.

Run it with the same interpreter that runs the daemon:

    /path/to/venv/bin/python patch_lookahead.py

Verification: the patch appends an import-time log line, so any process
running the patched module prints "wan-spike lookahead patch active" at
startup. If a daemon's log doesn't show it, that daemon is NOT patched.

Idempotent: skips if already patched.
"""

import sys
from pathlib import Path

from flwr.supercore import grpc as _mod

PATH = Path(_mod.__file__)
LOOKAHEAD = '        ("grpc.http2.lookahead_bytes", 16 * 1024 * 1024),\n'
BANNER = (
    "\nfrom logging import INFO as _WAN_SPIKE_INFO\n"
    'log(_WAN_SPIKE_INFO, "wan-spike lookahead patch active: '
    '16 MB HTTP/2 windows (client channels + servers)")\n'
)

src = PATH.read_text(encoding="utf-8")
if "lookahead_bytes" in src:
    print(f"already patched: {PATH}")
    sys.exit(0)

# 1. Client channel options in create_channel
old_client = """    channel_options = [
        ("grpc.max_send_message_length", max_message_length),
        ("grpc.max_receive_message_length", max_message_length),
    ]
"""
new_client = """    channel_options = [
        ("grpc.max_send_message_length", max_message_length),
        ("grpc.max_receive_message_length", max_message_length),
        ("grpc.http2.lookahead_bytes", 16 * 1024 * 1024),
    ]
"""
if src.count(old_client) != 1:
    raise RuntimeError("client options block not found")
src = src.replace(old_client, new_client)

# 2. Server options in generic_create_grpc_server
old_server = '        ("grpc.keepalive_permit_without_calls", 0),\n    ]\n'
new_server = '        ("grpc.keepalive_permit_without_calls", 0),\n' + LOOKAHEAD + "    ]\n"
if src.count(old_server) != 1:
    raise RuntimeError("server options block not found")
src = src.replace(old_server, new_server)

# 3. Import-time banner so patched daemons are verifiable from their logs
src += BANNER

PATH.write_text(src, encoding="utf-8")
print(f"patched OK: {PATH}")
print("restart the daemon and confirm its log shows " "'wan-spike lookahead patch active'")
