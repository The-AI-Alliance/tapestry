# Flower WAN Weight-Transfer Spike

**Status: Speculative**

De-risk spike for the [issue #70](https://github.com/The-AI-Alliance/tapestry/issues/70)
epic: **can a ~2B-parameter model's weights round-trip through a Flower SuperLink over a
real WAN, and how long does a round take?** This measures transport only — the "training"
node echoes the weights back unchanged.

## Bottom line

**Flower's transport is not a performance concern for this epic.** On a healthy ~100 ms
WAN path, stock flwr 1.32.1 moves weights within ~15 % of raw single-stream TCP in both
directions with no tuning — **a 2B-parameter (4 GB each way) exchange costs ~10 minutes
per round** ([field re-run](#field-re-run-2026-07-03-fresh-box-pair)). That comfortably
supports DiLoCo-cadence sync and is workable even for frequent-sync patterns.

The initial spike measured much worse (~1.5 h per 2B round) — that turned out to be a
**degraded network path on the first box pair, not Flower**: the identical setup on a
fresh pair, plus a local latency-simulation A/B, showed gRPC's flow-control auto-tuning
normally handles high-RTT paths fine. The sections below keep the full investigation
record, including the optional `patch_lookahead.py` hardening that pins throughput at the
raw-TCP limit and protects against paths where that auto-tuning fails.

## Design

- **Payload**: 2,000,000,000 parameters in float16 = **4.0 GB** each direction, split into
  80 × 50 MB tensors (like a real model's layer tensors; each message object stays far below
  gRPC size limits). float16 stands in for bfloat16 — NumPy has no bf16; wire size is identical.
  Values are random so transparent compression can't flatter the numbers.
- **Topology**: SuperLink + ServerApp on one host (the "central node"), one SuperNode +
  ClientApp on another (a "sovereign node"). The ServerApp sends the payload via a
  single-node FedAvg round; the client echoes it back; FedAvg aggregates (N=1 identity).
- **NumPy-only** app: node setup is `pip install flwr numpy`, no torch.

## Initial results (first box pair — timings later attributed to a degraded path)

Two WAN topology used: 

1. SuperLink + ServerApp on a Quebec (CA) vast.ai instance, SuperNode +
ClientApp on a Sweden (SE) instance. Measured path RTT ≈ 106 ms; raw single-stream TCP on
the same path: 114 Mbit/s (QC→SE), 167 Mbit/s (SE→QC).

> **Note:** the WAN timings in this section did not reproduce on a fresh box pair (see
> [field re-run](#field-re-run-2026-07-03-fresh-box-pair)) — they characterize that
> specific path, not Flower. The functional results (payload integrity at 4 GB per
> direction) stand.

2. SuperLink + ServerApp on a us-east-2 (Ohio) EC2 instance, SuperNode +
ClientApp on a ap-southeast-1 (Singapore) EC2 instance on AWS. Measure path RTT ≈ 200 ms;

| leg | payload | round-trip (1 round) | effective throughput* | performed by |
| :-- | :-- | :-- | :-- | :-- |
| loopback (WSL2, same host) | 0.5 GB ×2 | 20.5 s | ~0.39 Gbit/s | jneums |
| loopback (WSL2, same host) | 4.0 GB ×2 | 138.1 s | ~0.46 Gbit/s | jneums |
| WAN Quebec↔Sweden (106 ms) | 0.5 GB ×2 | 10 min 30 s | ~13 Mbit/s | jneums |
| WAN Quebec↔Sweden (106 ms) | 4.0 GB ×2 | 1 h 24 min | ~12.7 Mbit/s | jneums |
| WAN Quebec↔Norway (97 ms), unpatched | 0.5 GB ×2 | 8 min 13 s | ~16 Mbit/s | jneums |
| WAN Quebec↔Norway, lookahead patch | 0.5 GB ×2 | 6–9 min (3 runs; one 78 s outlier) | pull fixed, push not | jneums |
| WAN Quebec↔Norway, lookahead patch | 4.0 GB ×2 | 1 h 1 min | pull ~128 Mbit/s, push ~10 Mbit/s | jneums |
| AWS Ohio↔Singapore (200 ms), unpatched | 0.5 GB ×2 | 82.4 s | ~97.1 Mbit/s | jolson-allianceai |
| AWS Ohio↔Singapore (200 ms), unpatched | 4.0 GB ×2 | 8 min 32 s | ~0.125 Gbit/s | jolson-allianceai |

\* total bytes moved ÷ round time; includes flwr's serialization and store-and-forward
through the SuperLink object store, so this is *system* throughput, not link speed.

**Loopback finding:** even with no real network, the stack tops out around ~0.5 Gbit/s —
Flower's object store/serialization path, not bandwidth, is the first ceiling. For DiLoCo-class
outer loops (sync every ~500+ inner steps) a couple of minutes per exchange is comfortably
affordable; for frequent-sync patterns it would dominate.

**WAN finding (superseded — see field re-run):** on this pair the WAN round ran far below
the path's raw TCP capacity. Per-leg reconstruction of the 0.5 GB round: server→node
delivery ran at ~47 Mbit/s (~2.4× below raw TCP on that path), but the node→server **push
of the reply ran at ~7.5 Mbit/s — ~20× below raw TCP** (167 Mbit/s measured with a plain
socket seconds later on the same path). The rate corresponds to only ~100 KB in flight
per 106 ms round trip — a small effective window somewhere in the push path.

The 4.0 GB round scales linearly from the 0.5 GB one (~12.7 vs ~13 Mbit/s effective), so
the overhead is proportional to bytes moved, not a fixed per-round cost: a 2B-param
model exchange cost ~1.5 h per round *on this pair's path* (a healthy path costs ~10 min —
see the field re-run). Arrays are split into
5 MB chunk objects (`FLWR_PRIVATE_MAX_ARRAY_CHUNK_SIZE`); raising the chunk size 13×
did not change the round time (table below), so the cost is *per byte in flight*, not
per chunk boundary — consistent with a small effective in-flight window on the 106 ms
path rather than chunk-setup overhead.

**Knob A/B tests** (0.5 GB payload, same path, both daemons restarted with the env
override each time; baseline 10 min 30 s):

| variant | round-trip | conclusion |
| :-- | :-- | :-- |
| `FLWR_PRIVATE_MAX_ARRAY_CHUNK_SIZE` 5 MB → 64 MB | 10 min 21 s | no effect — chunk granularity is not the bottleneck |
| + `FLWR_PRIVATE_MAX_CONCURRENT_OBJ_{PUSHES,PULLS}` 2 → 16 | 12 min 42 s | no effect — parallel streams over one connection don't help |

(Env vars verified present in the running SuperNode's `/proc/<pid>/environ`.)

**Root cause class — confirmed.** The measured ~100 KB in flight per RTT matches gRPC
C-core's per-stream read-ahead limit,
[`grpc.http2.lookahead_bytes`](https://grpc.github.io/grpc/core/group__grpc__arg__keys.html)
(`GRPC_ARG_HTTP2_STREAM_LOOKAHEAD_BYTES`, default 64 KB) — documented as the knob to
raise "on high-latency connections." gRPC normally outgrows that default on its own via
BDP probing (verified in the simulation section below), so the field path was also
defeating the auto-tuning — but forcing a large window removes the dependence on BDP
probing behaving. Flower's channel construction (`flwr/supercore/grpc.py`) sets only
message-length options, and the window option is not operator-configurable.

**Patch results on the original spike's second pair** (Quebec↔Norway, 97 ms RTT — still
the degraded-path regime; `patch_lookahead.py` in this directory adds
`("grpc.http2.lookahead_bytes", 16 MB)` to Flower's client channels and server options;
unpatched same-pair baseline 8 min 13 s for 0.5 GB ×2):

- **Pull leg (SuperLink→node) is reliably fixed**: ~47 Mbit/s unpatched →
  **~90–128 Mbit/s patched**, reproduced across three runs including 4 GB — near raw
  single-stream TCP for the path. Consistent with flow-control mechanics: the pull
  receiver is the patched *client channel*.
- **Push leg (node→SuperLink) was NOT fixed in the field runs**: ~10–16 Mbit/s in every
  steady-state run, patched or not (4 GB patched round: 1 h 1 m, vs 1 h 24 m unpatched).
  At the time we concluded the server-side receive window couldn't be set from outside
  gRPC-core — **the local-simulation follow-up below overturned that conclusion**: the
  same option on the *server* does govern the push leg. The most likely field explanation
  is that the SuperLink process was not actually running the patched module (the original
  patch had no runtime verification; it now logs a banner at import). Also ruled out for
  the push leg: chunk size, app-level transfer concurrency, connection age
  (fresh-SuperNode rerun), and SuperLink state (fresh-SuperLink rerun).
- One 0.5 GB patched run completed in 78 s (~103 Mbit/s both legs) but did **not
  reproduce** under identical fresh-restart conditions (6–9 min in three attempts).
  Possible object-store dedup effect (the echo payload's content hashes match objects the
  store may still hold) or transient path conditions — flagged as an open question for
  upstream rather than claimed as a result.

Implications for the epic:

- **Functionally proven**: a 2B-param payload round-trips intact through SuperLink over
  a real WAN; no message-size or memory failures at 4 GB per direction.
- **Cost as shipped**: ~1.5 h per 2B exchange *on the original degraded path* — the field
  re-run below shows a healthy ~100 ms path costs **~10 min per 2B round with no patch at
  all** (~75 s for 0.5 GB each way). Even the degraded-path worst case is absorbed by
  DiLoCo-cadence sync; frequent-sync patterns need a healthy path or the window fix.
- **Cost with the patch**: pins the SuperLink→node direction at the raw-TCP limit
  (field-verified) and defends both legs against paths where gRPC's window auto-tuning
  fails (simulation below: push 73→218 Mbit/s with auto-tuning disabled).
- The patch is **optional hardening, not a requirement**: healthy paths need nothing. For
  sovereign nodes on links of unknown quality, apply `patch_lookahead.py` on every host
  (SuperLink and SuperNodes) and check the daemon logs for the patch banner. A low-priority
  upstream feature request ("expose HTTP/2 window options as SuperLink/SuperNode config")
  would make this unnecessary; no matching issue exists in the Flower tracker as of
  2026-07-03.
- Channel-level gzip compression would not help: weights are near-incompressible and the
  bottleneck is flow-control round trips, not bytes.

## Follow-up: local WAN simulation (2026-07-03)

The field boxes were gone, so to dig further we rebuilt the conditions locally: an
unprivileged network namespace gives full `tc netem` control over its own loopback with
no root required (`unshare -rn`, then `tc qdisc add dev lo root netem delay 50ms` =
100 ms RTT). The entire stack — SuperLink, SuperNode, `flwr run` — runs inside the
namespace; set `FLWR_DISABLE_RUNTIME_DEPENDENCY_INSTALLATION=1` since the namespace has
no route to PyPI.

Findings (flwr 1.32.1, grpcio 1.81.1, 100 ms RTT):

1. **Flower is not inherently slow at 100 ms.** Unpatched, 200 MB down + 200 MB up
   completes in 30 s (pull ~87 Mbit/s, push ~137 Mbit/s): gRPC's default BDP probing
   grows the flow-control windows fine on a clean path. The field path was defeating BDP
   probing (trigger not yet reproduced locally — pure delay, jitter, 0.05–0.3 % loss, and
   a 200 Mbit rate limit all still ramp).
2. **The server-side window option works** — the field conclusion above was wrong.
   `grpcbench.py` (in this directory) isolates the two directions; with BDP probing
   disabled to emulate the field's frozen-window regime, `grpc.http2.lookahead_bytes`
   16 MB on the *server* takes the push leg 73 → 218 Mbit/s, while the same option on
   the client does nothing for push (as HTTP/2 flow control predicts: the receiver's
   window governs). The option is harmless with BDP probing left on.
3. `patch_lookahead.py` therefore covers **both** legs when applied on both hosts. It now
   appends an import-time log banner (`wan-spike lookahead patch active`) so a running
   daemon proves it loaded the patched module — the missing verification that most likely
   explains the field push result.
4. One repro hazard worth knowing: `uv pip install` hardlinks files from its cache, so
   patching a venv's flwr in place can silently poison the cached wheel — later "fresh"
   installs come up already patched. `uv cache clean flwr` before reinstalling.

Example `grpcbench.py` A/B at 100 ms RTT (8 MB unary messages, BDP probing disabled,
first message includes ramp):

| variant | push (node→server analog) |
| :-- | :-- |
| no lookahead | 51, 73, 74 Mbit/s |
| lookahead 16 MB on client only | 51, 73, 74 Mbit/s |
| lookahead 16 MB on server only | 66, 215, 219 Mbit/s |

## Field re-run (2026-07-03, fresh box pair)

Same topology rebuilt from scratch the same day: fresh Quebec (SuperLink) and Norway
(SuperNode) vast.ai instances, same stack (flwr 1.32.1, grpcio 1.81.1, Python 3.12 venv),
same vast Docker-NAT port mappings, measured path RTT ~101–107 ms, raw single-stream TCP
215 Mbit/s (NO→QC) / 138 Mbit/s (QC→NO) — a faithful stand-in for the original pair.

| run (0.5 GB down + 0.5 GB up) | round | pull leg | push leg |
| :-- | :-- | :-- | :-- |
| unpatched #1 | 81.6 s | 32.8 s (~122 Mbit/s) | 48.8 s (~82 Mbit/s) |
| patched, banner-verified both hosts | 65.5 s | 29.1 s (~137 Mbit/s, at raw-TCP limit) | 36.5 s (~110 Mbit/s) |
| unpatched #2 (flwr reinstalled, banner absent) | 72.7 s | 32.8 s (~122 Mbit/s) | 39.9 s (~100 Mbit/s) |

Compare the original pair's consistent **8 min 13 s** unpatched (pull ~47, push ~7.5
Mbit/s). Conclusions:

- **The original slowness does not reproduce** on a fresh identical-topology pair. Two
  unpatched runs land at 73–82 s — within ~15 % of raw TCP on both legs, with TCP
  autotuning reaching ~3 MB receive windows during the push (`ss -ti` sampled on the
  SuperLink during the run). The original spike's one unexplained "78 s outlier" was the
  healthy behavior; the 6–9 min runs were the anomaly, specific to that box pair/path.
- **The patch is field-verified as harmless and mildly beneficial**: it pins the pull leg
  at the raw-TCP limit and the round improves ~10–20 %. The import-banner verification
  works in the field (present in both patched daemon logs, absent after reinstall).
- Practical cost for the epic: at these rates a 2B-param (4 GB each way) exchange costs
  **~10 min per round, not ~1.5 h** — the original spike's headline number reflected a
  degraded path, not Flower's design. What exactly degraded the original path (that
  specific host's link, middlebox, or transient conditions) is no longer testable — the
  boxes are gone; the local simulation above shows the *mechanism* such a path uses to
  hurt Flower (frozen flow-control windows) and that forcing large windows defends
  against it.

## Gotchas found (flwr 1.32)

- `FedAvg` defaults to `min_train_nodes=2` / `min_available_nodes=2`; with one node,
  `strategy.start` waits forever with no message. Set them to 1 for a single-node spike.
- ClientApp/ServerApp `print` output is block-buffered before it reaches `flwr run --stream`;
  use `flush=True`.
- `MetricRecord` values must be numeric — a string value fails the whole client reply.
- If the SuperLink becomes unreachable, the SuperNode retries briefly and then **exits**
  rather than backing off indefinitely; node-side supervision (systemd restart or similar)
  is required for unattended sovereign nodes.
- flwr ≥1.31 requires Python ≥3.11 (common GPU images still ship 3.10; `uv venv --python 3.12`
  is a quick fix).

## Reproducing

Environment (both hosts): Python ≥3.10, `pip install "flwr>=1.32,<1.33" numpy`, plus this
app installed (`pip install -e .`) wherever the SuperNode and SuperLink run.

For the patched configuration, run `python patch_lookahead.py` with each daemon's own
interpreter on **both** hosts, restart the daemons, and confirm each daemon's log prints
`wan-spike lookahead patch active` — a daemon without the banner is running unpatched code.

Central node:

```shell
flower-superlink --insecure   # control API :9093, fleet API :9092
```

Sovereign node:

```shell
flower-supernode --insecure --superlink <central-host>:9092
```

Driver (any machine that can reach the control API) — add to `~/.flwr/config.toml`:

```toml
[superlink.spike]
address = "<central-host>:9093"
insecure = true
```

then, from this directory:

```shell
flwr run . spike --stream
# smaller payload: flwr run . spike --run-config "payload-params=250000000" --stream
```

`--insecure` is acceptable for this throwaway spike on random weights; a real deployment
uses TLS + SuperNode auth (both built into Flower).

## Scope

This spike informs the "Flower as connectivity layer" recommendation on #70. It does not
test training, aggregation quality, node failure, or TLS — only that the epic's weight
payload fits through the pipe and what a round costs.
