"""Rubric judge for the behavioral probe's free-form (generate) mode.

In generate mode the model writes an open-ended response to a scenario instead of
choosing among fixed options. A *judge* then maps that free text back onto the
scenario's action options, so the behavioral coordinate is still the expected
Inglehart-Welzel axis value -- only the scoring of each option changes from the
model's own teacher-forced log-prob to "how consistent is the model's actual
response with this action?".

:class:`EmbeddingJudge` answers that with multilingual sentence-embedding cosine
similarity between the response and each option's text. It is deterministic and
self-contained (no external API), and works for English and Arabic. The ``Judge``
protocol lets tests inject a lightweight stub instead of loading the embedder.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable


@runtime_checkable
class Judge(Protocol):
    """Scores a free-form response against candidate action descriptions."""

    def score_options(self, response: str, option_texts: Sequence[str]) -> list[float]:
        """Return one score per option; higher = the response is more consistent
        with that action. The caller softmaxes these into a distribution over the
        options' axis values."""
        ...


class EmbeddingJudge:
    """Judge free-form behavior by multilingual embedding similarity.

    Lazily loads a sentence-transformer (default a 50-language MiniLM that covers
    Arabic). Scoring is cosine similarity between the response and each option,
    so a response that *describes deferring to elders* scores highest on the
    deferring option regardless of exact wording.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device: str = "cpu",
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - optional dep
            raise ImportError(
                "behavior generate mode needs `sentence-transformers`; install it " "or use --behavior-mode logprob."
            ) from exc
        self.model_name = model_name
        self._st = SentenceTransformer(model_name, device=device)

    def score_options(self, response: str, option_texts: Sequence[str]) -> list[float]:
        if not response.strip():
            return [0.0] * len(option_texts)
        embs = self._st.encode([response, *option_texts], normalize_embeddings=True)
        resp, opts = embs[0], embs[1:]
        return [float(resp @ opt) for opt in opts]

    def score_axis(self, response: str, neg_anchors: Sequence[str], pos_anchors: Sequence[str]) -> float:
        """Signed SemAxis lean of ``response`` toward the +pole vs the -pole, in [-1, 1].

        Scoring a free response by softmax over cosine similarity to several
        *crowded* action options saturates: the options for one scenario sit close
        together in embedding space, so even a perfectly pole-aligned response only
        nudges the coordinate (~±0.25 empirically). Instead we build a SemAxis from
        anchor *centroids* -- the scenario's own pole option plus axis-level exemplar
        sentences -- and score the **calibrated cosine difference**
        ``cos(resp, +pole) - cos(resp, -pole)`` normalised by ``1 - cos(+pole, -pole)``
        so the poles map to ±1. The difference cancels the generic first-person-opinion
        component both poles share, leaving the axis lean; anchoring each pole with
        several exemplars denoises the direction. This recovers the dynamic range the
        option-softmax judge throws away (~5x the spread on pole-aligned responses).
        """
        import numpy as np

        if not response.strip() or not neg_anchors or not pos_anchors:
            return 0.0
        n_neg = len(neg_anchors)
        embs = np.asarray(self._st.encode([response, *neg_anchors, *pos_anchors], normalize_embeddings=True))
        resp = embs[0]
        neg_centroid = embs[1 : 1 + n_neg].mean(axis=0)
        pos_centroid = embs[1 + n_neg :].mean(axis=0)
        neg_norm, pos_norm = float(np.linalg.norm(neg_centroid)), float(np.linalg.norm(pos_centroid))
        if neg_norm < 1e-9 or pos_norm < 1e-9:  # a pole's anchors cancelled out
            return 0.0
        neg_centroid /= neg_norm
        pos_centroid /= pos_norm
        denom = max(1e-6, 1.0 - float(pos_centroid @ neg_centroid))  # rescale so poles -> ±1
        val = (float(resp @ pos_centroid) - float(resp @ neg_centroid)) / denom
        return max(-1.0, min(1.0, val))
