# README for the Model Training Requirements Work Group

Identify and prioritize the requirements for distributed (i.e., federated) training and tuning, which satisfy the data requirements.

## Key Questions

1. What privacy guarantees are required for gradient sharing between sovereign nodes (homomorphic encryption? differential privacy budget)?
2. What is the acceptable latency ceiling for gradient synchronization across nodes at 7-node and 1,000-node scale?
3. How does the federated protocol handle nodes operating on a slow sync cycle (24–48 hours)?
4. What Byzantine fault tolerance guarantees must the training protocol provide?
5. How should the federated protocol handle heterogeneous model architectures (Transformer vs. JEPA nodes)?
6. What are the measurable criteria for a JEPA-architecture node to qualify for production federated training?
7. What infrastructure is required to support asynchronous gradient aggregation without degrading global model quality?

## PRD References

- Section 7 (Architecture Requirements): AR-1, AR-5
- Section 6.4 (Cross-Level Sovereignty): SR-12, SR-13
- Section 5 (Performance Requirements): PR-1, PR-2, PR-5

**Status:** Forming. Requirements ratification is the prerequisite for Model Training Engineering implementation.
