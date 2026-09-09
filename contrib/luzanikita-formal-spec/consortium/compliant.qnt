// Compliant Shared-Base Loop protocol (ADR-004): the honest aggregation
// protocol in which nodes contribute Contributed CPT weight vectors only,
// the coordinator averages/integrates them, and the Shared Base is updated.
//
// This module instantiates `shared` with a concrete, small node set (3
// consortium members — matching ADR-004's MVP note: "a Shared-Base Loop
// across 2-3 real members") and wires the shared "good" actions into a
// `step`. It adds no adversarial actions, so it is expected to SATISFY
// every invariant in `shared.qnt` under `quint run`.
//
// Run (see ../README.md for the full command set):
//   quint typecheck compliant.qnt
//   quint run --invariant main compliant.qnt
module compliant {
  import shared(NODES = Set(1, 2, 3)).* from "./shared"

  action step: bool = {
    nondet n = NODES.oneOf()
    any {
      contributedCPT(n),
      contributeWeights(n),
      aggregatorObserve,
      integrate,
      advanceClock,
      migrateBaseProvider,
    }
  }

  // Combined invariant for this module, checked generically by
  // `make formal-spec-verify` via the `val main: bool` convention in
  // .formal-spec.mk. Keep this in sync with shared.qnt's individual
  // invariants.
  val main: bool = no_raw_data_crosses and only_cpt_feeds_base and weights_portable
}
