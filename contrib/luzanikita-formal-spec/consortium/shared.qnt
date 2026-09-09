// Tapestry INV-1 formal-spec pilot — shared types, state, and invariants.
//
// Formalizes ARCHITECTURE.md's "Design Goals and Invariants":
//   INV-1 (headline): "No raw data crosses node boundaries — only model
//                      weight vectors after Contributed CPT."
//   INV-2: "Sovereign layers are portable across base models — no
//           provider-specific lock-in."
//   INV-3: "Only Contributed CPT feeds the Shared Base — the rest of the
//           Sovereign Build stays local."
//
// Modeled at design altitude: opaque symbolic tokens (never byte-level
// crypto), matching the pilot's scope (docs/superpowers/specs/
// 2026-07-29-quint-formal-spec-practice-design.md, §4 and §6). Safety-only —
// no liveness/temporal properties in this first model.
//
// This module is shared by `compliant.qnt` (the honest protocol, which
// satisfies every invariant below) and `leaky.qnt` (a non-compliant variant
// that adds adversarial actions and violates `no_raw_data_crosses`).
module shared {

  // ---------- types ----------

  // Symbolic node identifier. An int used only for identity/equality — not
  // an address, not a cryptographic key. One instance per consortium member
  // (ADR-002: "a small number of large, trusted, heterogeneous members").
  type NodeId = int

  // Opaque token standing in for either a raw data sample or a weight
  // vector. Design altitude: we do not model tensor contents, only which
  // node produced a token and (via the wire tag) what kind of thing it is.
  type Token = int

  // The payload actually carried by a wire transmission.
  type WireItemPayload = { node: NodeId, token: Token }

  // Everything that can be transmitted between a node and the coordinator.
  // This tagged union is the crux of INV-1: `CptWeights` is the only
  // variant the compliant protocol ever constructs; `RawData` exists so a
  // non-compliant variant (leaky.qnt) has something illegal to construct.
  type WireItem =
    | RawData(WireItemPayload)
    | CptWeights(WireItemPayload)

  // ---------- module parameters ----------

  // The (small, fixed) set of consortium member nodes. Instantiated by
  // compliant.qnt / leaky.qnt, e.g. `import shared(NODES = Set(1, 2, 3)).*`.
  const NODES: Set[NodeId]

  // ---------- state ----------

  // Raw data local to each node (ADR-008 sovereign/private/controlled
  // data). Never intended to leave the node boundary — this is what
  // `no_raw_data_crosses` protects.
  var rawData: NodeId -> Set[Token]

  // Weight-vector tokens each node has produced via Contributed CPT
  // (ADR-004 step 2: "data stays local; nothing crosses"). These *may*
  // legitimately be contributed back to the coordinator.
  var contributedWeights: NodeId -> Set[Token]

  // Everything actually transmitted on the wire between nodes and the
  // coordinator (ADR-004 step 3: "Contribute weights").
  var wire: Set[WireItem]

  // The coordinator/aggregator's accumulated view of everything it has
  // received off the wire.
  var view: Set[WireItem]

  // Tokens a curious/Byzantine observer (the aggregator, or a peer) has
  // learned by any means — observing the wire, or (in leaky.qnt) a
  // side-channel. `no_raw_data_crosses` requires this stays disjoint from
  // every node's raw data.
  var knowledge: Set[Token]

  // Tokens integrated into the Shared Base (ADR-004 step 4: "Integration").
  // INV-3 requires this only ever grows from Contributed CPT weights.
  var sharedBase: Set[Token]

  // Abstract round/step counter — no wall-clock time is modeled (see
  // quint-lang convention: model time as a round counter, not timers).
  var clock: int

  // Which base-model provider the Shared Base currently derives from
  // (ADR-006 phased base-model strategy: Phase 1 adopts an open-weights
  // base; Phase 2 transitions to a consortium-trained base). Used to model
  // INV-2 (no provider-specific lock-in): switching providers must never
  // discard sovereign contributions already in the Shared Base.
  var baseProvider: str

  // Snapshot of `sharedBase` taken at the moment of the most recent
  // provider migration, so `weights_portable` can check that nothing was
  // discarded by the switch.
  var preMigrationBase: Set[Token]

  // Whether at least one provider migration has occurred (so
  // `weights_portable` is non-vacuous only once a migration has happened).
  var hasMigrated: bool

  // ---------- pure helpers ----------

  pure def rawTokensFor(n: NodeId): Set[Token] = Set(n * 100, n * 100 + 1)

  pure def weightTokenFor(n: NodeId, round: int): Token = n * 100 + 1000 + round

  pure def isCptWeights(wi: WireItem): bool =
    match wi {
      | CptWeights(_) => true
      | RawData(_)    => false
    }

  pure def payloadOf(wi: WireItem): WireItemPayload =
    match wi {
      | CptWeights(p) => p
      | RawData(p)    => p
    }

  pure def tokenOf(wi: WireItem): Token = payloadOf(wi).token

  pure def allRawData(rd: NodeId -> Set[Token], nodes: Set[NodeId]): Set[Token] =
    nodes.fold(Set(), (acc, n) => acc.union(rd.get(n)))

  pure def allContributedWeights(cw: NodeId -> Set[Token], nodes: Set[NodeId]): Set[Token] =
    nodes.fold(Set(), (acc, n) => acc.union(cw.get(n)))

  pure def nextProvider(current: str): str =
    if (current == "phase1-open-weights") "phase2-consortium-base" else "phase1-open-weights"

  // ---------- init ----------

  action init: bool = all {
    rawData' = NODES.mapBy(n => rawTokensFor(n)),
    contributedWeights' = NODES.mapBy(n => Set()),
    wire' = Set(),
    view' = Set(),
    knowledge' = Set(),
    sharedBase' = Set(),
    clock' = 0,
    baseProvider' = "phase1-open-weights",
    preMigrationBase' = Set(),
    hasMigrated' = false,
  }

  // ---------- compliant protocol actions ----------
  // (ADR-004's Shared-Base Loop: Distribute -> Contributed CPT -> Contribute
  // weights -> Merge & redistribute.)

  // Step 2 of the loop: a node runs Contributed CPT on its own raw data.
  // The data stays local — this action never touches `wire`.
  action contributedCPT(n: NodeId): bool = all {
    not(contributedWeights.get(n).contains(weightTokenFor(n, clock))),
    contributedWeights' = contributedWeights.set(
      n, contributedWeights.get(n).union(Set(weightTokenFor(n, clock)))
    ),
    rawData' = rawData,
    wire' = wire,
    view' = view,
    knowledge' = knowledge,
    sharedBase' = sharedBase,
    clock' = clock,
    baseProvider' = baseProvider,
    preMigrationBase' = preMigrationBase,
    hasMigrated' = hasMigrated,
  }

  // Step 3 of the loop: a node sends back ONLY its post-CPT weight token —
  // never raw data. This is the only action in the compliant protocol that
  // writes to `wire`, and it only ever constructs `CptWeights`.
  action contributeWeights(n: NodeId): bool = all {
    contributedWeights.get(n).contains(weightTokenFor(n, clock)),
    not(wire.exists(wi => wi == CptWeights({ node: n, token: weightTokenFor(n, clock) }))),
    wire' = wire.union(Set(CptWeights({ node: n, token: weightTokenFor(n, clock) }))),
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

  // The coordinator observes whatever is currently on the wire. It
  // necessarily learns the token carried by each item it sees (that is
  // expected for CptWeights — the point of `no_raw_data_crosses` is that
  // this token is never a raw-data token).
  action aggregatorObserve: bool = all {
    not(wire.subseteq(view)),
    view' = view.union(wire),
    knowledge' = knowledge.union(wire.map(wi => tokenOf(wi))),
    rawData' = rawData,
    contributedWeights' = contributedWeights,
    wire' = wire,
    sharedBase' = sharedBase,
    clock' = clock,
    baseProvider' = baseProvider,
    preMigrationBase' = preMigrationBase,
    hasMigrated' = hasMigrated,
  }

  // Step 4 of the loop: the coordinator merges observed CptWeights tokens
  // into the Shared Base (FedAvg-class averaging is abstracted here as
  // token-set integration — the pilot models the data-boundary protocol,
  // not the ML averaging math).
  action integrate: bool = all {
    view.exists(wi => isCptWeights(wi) and not(sharedBase.contains(tokenOf(wi)))),
    sharedBase' = sharedBase.union(view.filter(wi => isCptWeights(wi)).map(wi => tokenOf(wi))),
    rawData' = rawData,
    contributedWeights' = contributedWeights,
    wire' = wire,
    view' = view,
    knowledge' = knowledge,
    clock' = clock,
    baseProvider' = baseProvider,
    preMigrationBase' = preMigrationBase,
    hasMigrated' = hasMigrated,
  }

  action advanceClock: bool = all {
    clock' = clock + 1,
    rawData' = rawData,
    contributedWeights' = contributedWeights,
    wire' = wire,
    view' = view,
    knowledge' = knowledge,
    sharedBase' = sharedBase,
    baseProvider' = baseProvider,
    preMigrationBase' = preMigrationBase,
    hasMigrated' = hasMigrated,
  }

  // Models INV-2: a Phase 1 -> Phase 2 (or back) base-model provider
  // migration (ADR-006) never discards sovereign contributions already
  // integrated into the Shared Base or held locally by nodes.
  action migrateBaseProvider: bool = all {
    baseProvider' = nextProvider(baseProvider),
    preMigrationBase' = sharedBase,
    hasMigrated' = true,
    sharedBase' = sharedBase,
    contributedWeights' = contributedWeights,
    rawData' = rawData,
    wire' = wire,
    view' = view,
    knowledge' = knowledge,
    clock' = clock,
  }

  // ---------- invariants ----------

  // HEADLINE (INV-1): every item ever placed on the wire is a CPT weight
  // vector, never raw data; AND no observer's accumulated knowledge ever
  // contains a token belonging to any node's raw data.
  val no_raw_data_crosses: bool =
    wire.forall(wi => isCptWeights(wi)) and
    knowledge.intersect(allRawData(rawData, NODES)) == Set()

  // INV-3: only Contributed CPT weights ever enter the Shared Base — its
  // contents are always a subset of the union of all nodes' contributed
  // weight tokens.
  val only_cpt_feeds_base: bool =
    sharedBase.subseteq(allContributedWeights(contributedWeights, NODES))

  // INV-2 (modeled constraint): once a base-model provider migration has
  // occurred, everything that was in the Shared Base immediately before
  // the switch is still present afterward — no provider-specific lock-in
  // that would force sovereign contributions to be discarded or re-derived.
  val weights_portable: bool =
    hasMigrated implies preMigrationBase.subseteq(sharedBase)

  // ---------- witnesses (reachability) ----------

  val someWeightsIntegrated: bool = sharedBase.size() > 0
  val migrationOccurred: bool = hasMigrated
  val multipleRoundsReached: bool = clock >= 2
}
