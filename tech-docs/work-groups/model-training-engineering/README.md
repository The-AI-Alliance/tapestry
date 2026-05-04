# README for the Model Training Engineering Work Group

The team implementing the distributed model training capabilities.

Begin constructing distributed training infrastructure, both PoCs and production deployments:
* Identify candidate tools and techniques.
* Prototype and iterate on the training stack and management infrastructure towards meeting anticipated requirements.
* Identify and plan for delivery milestones.

## Preliminary Scope

- Federated gradient aggregation with homomorphic encryption and differential privacy (ε < 1.0 per round)
- Byzantine fault tolerance for up to 1/3 malicious nodes
- Asynchronous gradient aggregation with <5 minute sync latency at 1,000 nodes
- Transformer-based (Track 1) and JEPA (Track 2) training support
- MBZUAI validation hooks for independent privacy certification

## Source Code

[`src/tapestry/training/`](../../../src/tapestry/training/)

**Status:** Early formation. Begins active implementation once Model Training Requirements are ratified.
