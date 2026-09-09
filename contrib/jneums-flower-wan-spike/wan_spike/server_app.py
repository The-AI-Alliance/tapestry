"""ServerApp: build a ~4 GB ArrayRecord, run FedAvg rounds, report timing."""

import time

from flwr.app import ArrayRecord, Context
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg

from wan_spike.task import make_ndarrays, total_bytes, validate_positive_int

app = ServerApp()


@app.main()
def main(grid: Grid, context: Context) -> None:
    # payload/tensor params are validated inside make_ndarrays; num_rounds is
    # only used here, so it is validated at this call site.
    payload_params = int(context.run_config["payload-params"])
    tensor_params = int(context.run_config["tensor-params"])
    num_rounds = validate_positive_int("num-server-rounds", int(context.run_config["num-server-rounds"]))

    t0 = time.time()
    ndarrays = make_ndarrays(payload_params, tensor_params)
    gb = total_bytes(ndarrays) / 1e9
    arrays = ArrayRecord(numpy_ndarrays=ndarrays, keep_input=False)
    del ndarrays
    t1 = time.time()
    print(
        f"SPIKE server: payload built: {gb:.3f} GB in {len(arrays)} tensors " f"({t1 - t0:.1f}s), unix={t1:.3f}",
        flush=True,
    )

    # The spike runs a single node; FedAvg defaults require 2.
    strategy = FedAvg(
        fraction_train=1.0,
        fraction_evaluate=0.0,
        min_train_nodes=1,
        min_evaluate_nodes=1,
        min_available_nodes=1,
    )
    t2 = time.time()
    result = strategy.start(
        grid=grid,
        initial_arrays=arrays,
        num_rounds=num_rounds,
    )
    t3 = time.time()

    per_round = (t3 - t2) / num_rounds
    print(
        f"SPIKE server: {num_rounds} round(s) in {t3 - t2:.1f}s "
        f"(~{per_round:.1f}s/round for {gb:.3f} GB down + {gb:.3f} GB up); "
        f"effective one-way throughput ~{2 * gb / per_round * 8:.2f} Gbit/s "
        f"if legs were symmetric. start_unix={t2:.3f} end_unix={t3:.3f}",
        flush=True,
    )
    # Keep the result object alive until after timing so nothing is GC'd early.
    print(f"SPIKE server: final ArrayRecord holds {len(result.arrays)} tensors", flush=True)
