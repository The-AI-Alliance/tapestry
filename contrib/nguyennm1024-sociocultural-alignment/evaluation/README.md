# evaluation/ — shared evaluation harness

Score ANY model (a trained member from `training/`, or a fused model from `consortium/`)
on capability and cultural alignment. Called identically by both parts, so members and
combined models are judged the same way. See `api.py` for the shared `evaluate()` contract.

- `zs_full_mmlu.py` (+ `zs_full_mmlu_sweep.py`) — full 14042-item MMLU, zero-shot.
- `iw/` — Inglehart-Welzel cultural-map projection: `iw_gen_tao.py` elicits the 10 WVS
  items, `iw_project.py` (a bit-exact port of Tao et al., validated by `run_tao_verbatim.R`)
  projects them, and `plot_*.py` render the map. Reference data lives alongside; the
  registration-walled WVS/EVS microdata is excluded.
