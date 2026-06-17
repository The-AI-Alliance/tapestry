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
