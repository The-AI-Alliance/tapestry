"""Minimal gRPC throughput bench for HTTP/2 flow-control experiments.

Isolates the two transfer directions Flower uses:
  push = big unary request  (client -> server data; the node->SuperLink leg)
  pull = big unary response (server -> client data; the SuperLink->node leg)

Designed to run over a simulated-latency loopback in an unprivileged
network namespace (no root needed):

    unshare -rn sh -c '
      ip link set lo up
      tc qdisc add dev lo root netem delay 50ms limit 100000   # 100 ms RTT
      python grpcbench.py server --bdp 0 >/dev/null 2>&1 &
      sleep 2
      python grpcbench.py client --only push
    '

Key knobs (each side independently):
  --lookahead N   set grpc.http2.lookahead_bytes (HTTP/2 initial window)
  --bdp 0         disable gRPC BDP probing, freezing windows at defaults —
                  emulates a path where auto-tuning fails, which is the
                  regime the WAN spike observed in the field.
"""

import argparse
import time
from concurrent import futures

import grpc

ADDR = "127.0.0.1:50551"
MSG = 8 * 1024 * 1024  # 8 MB per message
MAXLEN = 2_147_483_647


def build_options(args):
    opts = [
        ("grpc.max_send_message_length", MAXLEN),
        ("grpc.max_receive_message_length", MAXLEN),
    ]
    if args.lookahead:
        opts.append(("grpc.http2.lookahead_bytes", args.lookahead))
    if args.bdp is not None:
        opts.append(("grpc.http2.bdp_probe", args.bdp))
    return opts


def ident(x):
    return x


def run_server(args):
    def push(request, context):  # pylint: disable=unused-argument
        return b"ok"

    def pull(request, context):  # pylint: disable=unused-argument
        return bytes(MSG)

    handler = grpc.method_handlers_generic_handler(
        "bench",
        {
            "Push": grpc.unary_unary_rpc_method_handler(push, request_deserializer=ident, response_serializer=ident),
            "Pull": grpc.unary_unary_rpc_method_handler(pull, request_deserializer=ident, response_serializer=ident),
        },
    )
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8), options=build_options(args))
    server.add_generic_rpc_handlers((handler,))
    server.add_insecure_port(ADDR)
    server.start()
    print("server ready", flush=True)
    server.wait_for_termination()


def run_client(args):
    channel = grpc.insecure_channel(ADDR, options=build_options(args))
    push = channel.unary_unary("/bench/Push", request_serializer=ident, response_deserializer=ident)
    pull = channel.unary_unary("/bench/Pull", request_serializer=ident, response_deserializer=ident)
    grpc.channel_ready_future(channel).result(timeout=10)
    payload = bytes(MSG)

    legs = [("push", push, payload), ("pull", pull, b"x")]
    if args.only:
        legs = [leg for leg in legs if leg[0] == args.only]
    for name, fn, arg in legs:
        rates = []
        for _ in range(args.nmsg):
            t0 = time.monotonic()
            fn(arg, timeout=300)
            rates.append(MSG * 8 / (time.monotonic() - t0) / 1e6)
        print(
            f"{name}: " + " ".join(f"{r:7.1f}" for r in rates) + "  Mbit/s per 8MB msg",
            flush=True,
        )


p = argparse.ArgumentParser()
p.add_argument("role", choices=["server", "client"])
p.add_argument("--lookahead", type=int, default=0)
p.add_argument("--bdp", type=int, default=None)
p.add_argument("--only", choices=["push", "pull"], default=None)
p.add_argument("--nmsg", type=int, default=3)
args = p.parse_args()
(run_server if args.role == "server" else run_client)(args)
