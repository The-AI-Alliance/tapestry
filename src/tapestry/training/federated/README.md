# Tapestry Federated Training

Privacy-preserving distributed training with data sovereignty.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Node-EU   │     │  Node-India │     │  Node-SEA   │
│             │     │             │     │             │
│ Local Data  │     │ Local Data  │     │ Local Data  │
│ Local Model │     │ Local Model │     │ Local Model │
│ DP Engine   │     │ DP Engine   │     │ DP Engine   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │  Δw (clipped +    │  Δw (clipped +    │  Δw (clipped +
       │    noised)        │    noised)        │    noised)
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Aggregator │
                    │   (FedAvg)  │
                    │             │
                    │  Global     │
                    │  Model      │
                    └─────────────┘
```

## Modules

| Module | Purpose |
|---|---|
| `node.py` | `TrainingNode` holds local data and model; trains locally and exports DP-protected weight deltas. Also defines `MiniTransformer`, a small GPT-style model for demonstrations. |
| `aggregator.py` | `Aggregator` collects updates from all nodes and merges them via sample-weighted Federated Averaging (FedAvg). |
| `privacy.py` | `DifferentialPrivacy` implements gradient clipping (L2 projection) and calibrated Gaussian noise injection, with cumulative privacy budget tracking. |
| `protocols.py` | Data structures (`NodeUpdate`, `RoundResult`) and the `FederatedProtocol` interface that all participants implement. |

## Privacy Guarantees

Each node applies two DP mechanisms before transmitting updates:

1. **Gradient Clipping** -- The L2 norm of the weight delta is projected onto a ball of radius `max_grad_norm`, bounding any single sample's influence.
2. **Gaussian Noise** -- Noise with `sigma = noise_multiplier * max_grad_norm` is added to each parameter, providing (epsilon, delta)-differential privacy per round.

Privacy budget is tracked cumulatively using conservative linear composition.

## Running the Demo

```bash
python examples/federated_training_demo.py
```

This simulates three sovereign nodes (EU, India, SEA) collaboratively training a small transformer on text data. You should see loss decreasing across rounds while differential privacy is applied at every step.

## Running Tests

```bash
pytest src/tests/tapestry/training/federated/ -v
```

## References

- McMahan et al., "Communication-Efficient Learning of Deep Networks from Decentralized Data" (AISTATS 2017)
- Abadi et al., "Deep Learning with Differential Privacy" (SIGSAC 2016)
