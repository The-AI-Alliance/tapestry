// Non-compliant variant of the Shared-Base Loop protocol — the demonstration
// payoff of this pilot. This module adds two plausible adversarial actions
// on top of the same shared state and "good" actions from `shared.qnt`:
//
//  1. `leakyGossipRawData` — a node that gossips a raw sample directly onto
//     the wire "for efficiency", bypassing Contributed CPT entirely. This
//     violates the wire-tag half of `no_raw_data_crosses` almost
//     immediately (it can fire right after `init`).
//  2. `curiousAggregatorInspect` — a curious/Byzantine aggregator that
//     side-channels a raw token directly from a node (e.g. "just to verify
//     sample quality") without ever tagging it as a wire item. This
//     violates the knowledge-disjointness half of `no_raw_data_crosses`,
//     showing that check catches leakage the wire-tag check alone would
//     miss.
//
// Both are folded into this one file per the pilot's scope (adversary
// actions: Byzantine node, curious aggregator). A third adversary type
// named in the design doc — replay — is deliberately deferred: replay
// detection is a freshness/liveness concern, and this first model is
// safety-only (see ../README.md and the design doc's non-goals).
//
// Run (see ../README.md for the full command set):
//   quint typecheck leaky.qnt
//   quint run --invariant no_raw_data_crosses leaky.qnt
//     -> expected: violation found (concrete counterexample trace)
module leaky {
  import shared(NODES = Set(1, 2, 3)).* from "./shared"

  // Adversarial action 1: "gossip raw samples for efficiency."
  action leakyGossipRawData(n: NodeId): bool = {
    nondet tok = rawData.get(n).oneOf()
    all {
      rawData.get(n).size() > 0,
      wire' = wire.union(Set(RawData({ node: n, token: tok }))),
      rawData' = rawData,
      contributedWeights' = contributedWeights,
      view' = view,
      knowledge' = knowledge,
      sharedBase' = sharedBase,
      clock' = clock,
      baseProvider' = baseProvider,
      preMigrationBase' = preMigrationBase,
      hasMigrated' = hasMigrated,
    }
  }

  // Adversarial action 2: "curious aggregator reconstructs raw data."
  action curiousAggregatorInspect(n: NodeId): bool = {
    nondet tok = rawData.get(n).oneOf()
    all {
      rawData.get(n).size() > 0,
      knowledge' = knowledge.union(Set(tok)),
      rawData' = rawData,
      contributedWeights' = contributedWeights,
      wire' = wire,
      view' = view,
      sharedBase' = sharedBase,
      clock' = clock,
      baseProvider' = baseProvider,
      preMigrationBase' = preMigrationBase,
      hasMigrated' = hasMigrated,
    }
  }

  action step: bool = {
    nondet n = NODES.oneOf()
    any {
      contributedCPT(n),
      contributeWeights(n),
      aggregatorObserve,
      integrate,
      advanceClock,
      migrateBaseProvider,
      leakyGossipRawData(n),
      curiousAggregatorInspect(n),
    }
  }

  // Deliberately declares no `val main`: this is the negative fixture, and
  // `formal-spec-verify` only *runs* files whose `main` invariant is expected
  // to HOLD. leaky's whole point is that INV-1 does NOT hold here, which is an
  // expect-violation assertion (`! quint run --invariant no_raw_data_crosses
  // leaky.qnt`) — the opposite of an invariant that must hold. So leaky is
  // typechecked but not run; its counterexample is walked through manually in
  // ../README.md ("Reading a violation").
}
