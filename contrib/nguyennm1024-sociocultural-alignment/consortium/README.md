# consortium/ — consortium learning

Combine several independently-trained **member** models into one. Rather than training a
single monolithic model, Part 1 (`data_synthesis/` + `training/`) trains specialized
members; this part fuses them.

## Method v1: model soup (`soup/`)

Weight-space averaging of fine-tunes of the same base: `out = sum(w_i * member_i)`.

```bash
# 2-member CLI (alpha = weight on A):
python consortium/soup/model_soup.py <A> <B> <out_dir> <alpha>
```

```python
from consortium import Member
from consortium.soup import Soup
Soup().combine(
    [Member("…/culture", weight=0.5), Member("…/rehearsal", weight=0.5)],
    out_dir,
)
```

## The contract (`base.py`)

Every method implements `ConsortiumMethod.combine(members, out_dir, **config) -> out_dir`.
The result is just another model, so the shared `evaluation/` harness scores it like any
member.

## Roadmap

- Smarter weight merges: TIES, DARE, Fisher-weighted, learned coefficients.
- Output-space: ensembling / logit averaging.
- Input-conditional: mixture-of-experts / routing.
