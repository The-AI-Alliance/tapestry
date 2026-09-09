"""ClientApp: receive the weight payload, echo it back, log timing legs."""

import time

from flwr.app import Context, Message, MetricRecord, RecordDict
from flwr.clientapp import ClientApp

app = ClientApp()


@app.train()
def train(msg: Message, context: Context) -> Message:
    t0 = time.time()
    arrays = msg.content["arrays"]
    # Measure without deserializing to numpy: transport is what we're testing.
    nbytes = sum(len(arr.data) for arr in arrays.values()) # ty: ignore[unresolved-attribute]
    t1 = time.time()
    print(
        f"SPIKE client: received {nbytes / 1e9:.3f} GB " f"(handler_start_unix={t0:.3f}, counted at {t1:.3f})",
        flush=True,
    )

    content = RecordDict(
        {
            "arrays": arrays,  # echo the payload back unchanged
            "metrics": MetricRecord(
                {
                    "num-examples": 1,
                    "recv-gb": nbytes / 1e9,
                    "handler-start-unix": t0,
                }
            ),
        }
    )
    return Message(content=content, reply_to=msg)
