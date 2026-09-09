// Deterministic scenario tests for the compliant Shared-Base Loop protocol.
// Run with: quint test compliant_test.qnt --main compliantTest
module compliantTest {
  import shared(NODES = Set(1, 2, 3)).* from "./shared"

  // One full round for a single node: Contributed CPT -> contribute weights
  // -> coordinator observes -> integrate. Confirms the weight token (and
  // only the weight token) ends up in the Shared Base, and that both
  // headline invariants still hold at every step.
  run oneRoundIntegratesWeightsOnlyTest =
    init
      .then(contributedCPT(1))
      .expect(contributedWeights.get(1).contains(weightTokenFor(1, 0)))
      .expect(no_raw_data_crosses)
      .then(contributeWeights(1))
      .expect(wire.contains(CptWeights({ node: 1, token: weightTokenFor(1, 0) })))
      .expect(no_raw_data_crosses)
      .then(aggregatorObserve)
      .expect(view.contains(CptWeights({ node: 1, token: weightTokenFor(1, 0) })))
      .then(integrate)
      .expect(sharedBase.contains(weightTokenFor(1, 0)))
      .expect(no_raw_data_crosses)
      .expect(only_cpt_feeds_base)

  // Contributed CPT + contribute, for any node, never places that node's
  // raw data on the wire — only its derived weight token.
  run contributeNeverPutsRawDataOnWireTest =
    init
      .then(contributedCPT(2))
      .then(contributeWeights(2))
      .expect(not(wire.exists(wi => not(isCptWeights(wi)))))
      .expect(rawData.get(2).forall(tok => not(wire.exists(wi => tokenOf(wi) == tok))))

  // A base-provider migration never discards Shared Base contents already
  // present (the `weights_portable` / INV-2 scenario, made concrete).
  run migrationPreservesSharedBaseTest =
    init
      .then(contributedCPT(3))
      .then(contributeWeights(3))
      .then(aggregatorObserve)
      .then(integrate)
      .expect(sharedBase.contains(weightTokenFor(3, 0)))
      .then(migrateBaseProvider)
      .expect(sharedBase.contains(weightTokenFor(3, 0)))
      .expect(weights_portable)
}
