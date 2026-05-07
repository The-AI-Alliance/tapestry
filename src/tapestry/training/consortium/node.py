"""Sovereign participant node for the consortium-training PoC."""

from __future__ import annotations

import copy
from typing import Sequence

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .messages import (
    ModelState,
    SovereignContribution,
    SovereignCycleResult,
    SovereignModelArtifact,
)


# pylint: disable=too-many-instance-attributes,too-few-public-methods
# pylint: disable=too-many-arguments,too-many-positional-arguments
class SovereignTrainingNode:
    """Institutional node that produces a sovereign model and contribution.

    A node receives the current shared base, runs a local sovereign pipeline
    stage on its own corpus, keeps the resulting model artifact, and shares
    only a weight delta with the coordinator.
    """

    def __init__(
        self,
        node_id: str,
        jurisdiction: str,
        model: nn.Module,
        sovereign_corpus: Sequence[list[int]],
        quality_score: float,
        local_epochs: int = 3,
        lr: float = 1e-3,
        batch_size: int = 8,
    ) -> None:
        self.node_id = node_id
        self.jurisdiction = jurisdiction
        self.model = copy.deepcopy(model)
        self.quality_score = quality_score
        self.local_epochs = local_epochs
        self.lr = lr
        self.batch_size = batch_size
        self.latest_artifact: SovereignModelArtifact | None = None
        self._dataloader = self._build_dataloader(sovereign_corpus)

    def run_sovereign_cycle(self, round_num: int, base_state: ModelState) -> SovereignCycleResult:
        """Run local continued pretraining and return artifact plus delta."""
        starting_state = {name: tensor.clone() for name, tensor in base_state.items()}
        self.model.load_state_dict(starting_state)

        avg_loss = self._train_locally()
        sovereign_state = {name: tensor.clone() for name, tensor in self.model.state_dict().items()}
        delta = {name: sovereign_state[name] - starting_state[name] for name in starting_state}

        metrics = {"loss": avg_loss}
        artifact = SovereignModelArtifact(
            node_id=self.node_id,
            jurisdiction=self.jurisdiction,
            stage="continued_pretraining",
            model_state=sovereign_state,
            metrics=metrics,
        )
        self.latest_artifact = artifact

        contribution = SovereignContribution(
            node_id=self.node_id,
            round_num=round_num,
            weight_delta=delta,
            quality_score=self.quality_score,
            token_count=sum(input_ids.numel() for input_ids, _target_ids in self._dataloader),
            metrics=metrics,
        )
        return SovereignCycleResult(artifact=artifact, contribution=contribution)

    def _build_dataloader(self, corpus: Sequence[list[int]]) -> DataLoader[tuple[torch.Tensor, ...]]:
        if not corpus:
            raise ValueError("sovereign_corpus must contain at least one sequence")
        max_len = max(len(sample) for sample in corpus)
        if max_len < 2:
            raise ValueError("sovereign_corpus sequences must contain at least 2 tokens")

        padded = [sample + [0] * (max_len - len(sample)) for sample in corpus]
        tensor = torch.tensor(padded, dtype=torch.long)
        dataset = TensorDataset(tensor[:, :-1], tensor[:, 1:])
        return DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

    def _train_locally(self) -> float:
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.lr)
        criterion = nn.CrossEntropyLoss()
        total_loss = 0.0
        steps = 0

        for _ in range(self.local_epochs):
            for input_ids, target_ids in self._dataloader:
                optimizer.zero_grad()
                logits = self.model(input_ids)
                loss = criterion(
                    logits.reshape(-1, logits.size(-1)),
                    target_ids.reshape(-1),
                )
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                steps += 1

        return total_loss / max(steps, 1)
