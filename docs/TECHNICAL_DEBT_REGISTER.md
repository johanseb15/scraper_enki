# Enki Technical Debt Register

Audit version: `technical-debt-audit-v1`

Program: ENKI TECHNICAL DEBT CONSOLIDATION

Baseline: `main@b03e65ef287e3286bcca47e0355852b4fb8b6d77`

Machine-readable sources: `data/evaluation/technical_debt_audit_v1.json` (historical audit), `data/evaluation/runtime_cohort_lineage_gate_v1.json` (TD-001 remediation), and `data/evaluation/offer_service_reach_admission_gate_v1.json` (TD-002 remediation).

## Executive decision

The repository is test-green, but it is not yet safe to expand real market acquisition or authorize knowledge promotion. TD-001 is resolved by a fail-closed constituent RAW-lineage gate and TD-002 by a composable explicit service-reach gate. Two P0 debts still affect runtime evidence truth: temporal freshness and commercial-context projection. Founder field capture may continue only as supervised shadow testing; economic results must not be relied on until the remaining P0s close.

The TD-002 remediation changes runtime admission only: provider location no longer supplies service reach, UNKNOWN remains UNKNOWN, REMOTE does not imply NATIONAL, and no historical evidence, HUMAN_REAL data, readiness threshold or promotion state was changed.

| Severity | Count | Meaning in this register |
|---|---:|---|
| P0 | 4 | Demonstrated non-auditable/incorrect runtime evidence truth |
| P1 | 4 | Broken operations, replay or material user-language workflow |
| P2 | 5 | Incomplete data/architecture/test contracts with future safety risk |
| P3 | 3 | Configuration, documentation and legacy maintenance debt |
| **Total** | **16** | All confirmed; zero speculative tickets |

## Audit coverage and probes

The audit read the Rector, architecture, README, package/config files, every tracked path inventory, `scripts/`, `src/`, `tests/`, frontend product boundary, field evidence, current/historical evaluation artifacts, RAW manifests and Git/worktree state. Static searches covered debt markers, broad/silent exceptions, path manipulation, hardcoded geography/currency, duplicated enums/inference functions, timestamps, artifact writes, secrets and legacy surfaces.

The 50 requested dimensions were covered in these causal groups:

- Runtime boundary: entrypoints, imports, API, frontend contract, application services and developer workflow.
- Economic truth: parser, normalizers, pricing, comparability, readiness, trace, price scope, commercial context, geography, currency, bundles, hardware and features.
- Evidence lifecycle: RAW, provenance, historical/current data, temporal model, provider/source/document independence, offer identity, acquisition, candidates, validation, HUMAN_REAL and founder feedback.
- Reliability: artifacts, determinism, idempotence, schemas/versioning, tests/E2E/fixtures, performance, exception handling, type/enum duplication, dependencies and deprecations.
- Repository: architecture/documentation drift, dead/legacy code, worktrees, ignored outputs, field data and secret handling.

Safe runtime probes covered the public API, parser, normalization, price scope, comparability, evidence selection, tracing, artifact generation in temp paths, HUMAN_REAL append-only behavior, candidate/shadow flow and current corpus replay. Focused backend result: `64 passed, 1 warning in 4.43s`. Frontend lint passed, `10` tests passed, and production build passed. `pip check` reported no broken requirements.

## Entrypoint contract

Every one of the 45 scripts has a `__main__` guard, so none was classified as “not intended direct.” Forty-one import `src`; only two of those establish the repository root. Safe `--help` probes were used where available; operational/no-help scripts were not allowed to touch real data.

| Classification | Count |
|---|---:|
| DIRECT_SAFE | 5 |
| BROKEN_CONFIRMED | 34 |
| POTENTIALLY_BROKEN | 6 |
| NOT_INTENDED_AS_DIRECT_ENTRYPOINT | 0 |

DIRECT_SAFE: `audit_golden_language_corpus.py`, `estado_repo.py`, `ingestar_todo.py`, `report_usaspending_market.py`, `trace_real_query.py`.

BROKEN_CONFIRMED: `acquire_near_comparable_evidence.py`, `append_founder_feedback.py`, `audit_real_query_corpus.py`, `build_cohort_pair_evidence_plan.py`, `build_cohort_pair_unlock_report.py`, `build_economic_dimensions.py`, `build_economic_dimensions_v2.py`, `build_economic_gap_register.py`, `build_evidence_acquisition_plan.py`, `build_knowledge_candidates.py`, `build_offer_evidence.py`, `build_pricing_statistics.py`, `build_semantic_economic_shadow.py`, `build_semantic_normalization_live.py`, `build_semantic_understanding.py`, `build_targeted_source_claims.py`, `build_targeted_unlock_report.py`, `collect_argentina_bulk.py`, `collect_mercado_publico.py`, `collect_os_installation_jadetech.py`, `collect_pricing_sources.py`, `collect_ted.py`, `collect_usaspending.py`, `enrich_ted_full_notices.py`, `execute_cohort_pair_acquisition.py`, `extract_mercado_publico_orders.py`, `extract_ted_observations.py`, `extract_usaspending_awards.py`, `importar_evidencia.py`, `query_enki.py`, `query_pricing_evidence.py`, `report_mercado_publico_semantics.py`, `run_pricing_live_pipeline.py`, `source_gauntlet.py`.

POTENTIALLY_BROKEN: `acquire_candidate_validation_evidence.py`, `guardar_compragamer_sqlite.py`, `probar_compragamer.py`, `reconcile_price_scope_contract.py`, `run_candidate_shadow_validation.py`, `trace_real_world_queries.py`. Five share the unbootstrapped `src` import pattern; `guardar_compragamer_sqlite.py` imports the `scripts` package from a direct-file surface. They were not executed because their no-argument paths can acquire, persist or rewrite artifacts.

## Corpus root-cause partition

Current replay against v2 cohorts produces `21 WRONG_INTERPRETATION`, `0 UNSAFE_DECISION`: intent 3, semantic alias 2, technical need 0, market resolution 7, normalization 1, commercial context 3, device 0, other control-flow/bundle 5.

The six specifically incorrect clarifications have one control-flow family:

- `rq013`, `rq015`, `rq017`, `rq027`: terminal unsupported bundles reach missing-detail clarification first.
- `rq039`: unsupported USDT reaches clarification first.
- `rq043`: a fragment without actionable economic intent reaches clarification first.

## Debt items

### TD-001 — Runtime pricing cohorts can emit ranges without constituent RAW lineage

- DEBT_ID: `TD-001`
- TITLE: Runtime pricing cohorts can emit ranges without constituent RAW lineage.
- CATEGORY: CORRECTNESS, OBSERVABILITY, DATA_LINEAGE, SAFETY.
- SEVERITY: `P0`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `runtime-cohort-lineage-gate-v1`.
- EVIDENCE: The historical audit remains unchanged at 78/273 TRACEABLE_RAW. The versioned runtime projection admits only 31/84 eligible observations and preserves/excludes 53 with `MISSING_REPRODUCIBLE_RAW_LINEAGE`. The active remote hourly support cohort now contains only observation 68; observations 147 and 213 remain preserved but cannot affect provider count, median, range or readiness. `CohortePricing` and the API expose admitted `observation_ids` and the gate version.
- REPRODUCTION: Regenerate `runtime_cohort_lineage_gate_v1.json`; `pricing-cohort:AR:SOPORTE_REMOTO:PER_HOUR:STANDARD` changes from 3 observations/3 sources/RANGE_READY to 1 observation/1 source/INSUFFICIENT_EVIDENCE, with exact exclusion reasons for 147 and 213.
- AFFECTED_FILES: `scripts/build_pricing_statistics.py`, `src/aplicacion/pricing_evidence_engine.py`, `src/aplicacion/pricing_cohort_loader.py`, `src/api/main.py`, `data/offer_evidence_v1.jsonl`, `data/pricing_cohort_scope_evidence_v1.jsonl`.
- AFFECTED_LAYERS: APPLICATION, API, DATA_ARTIFACTS.
- ROOT_CAUSE: Runtime cohorts predate offer-level lineage as an admission contract.
- PRODUCT_IMPACT: A user can receive a range that cannot be completely replayed to preserved RAW.
- DATA_RISK: Unverifiable legacy extraction can contribute to statistics.
- SAFETY_RISK: Non-auditable economic evidence appears usable.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: Every runtime cohort and evidence-bearing public response.
- DEPENDENCIES: None.
- IMPLEMENTED_FIX: `runtime_cohort_lineage_gate` validates observation/source identity, extractor/import provenance, repository-contained RAW path, content hash and RAW document id before aggregation. Runtime loading rejects ungated cohort artifacts. Excluded observations remain historical input.
- REGRESSION_TEST: Ten focused contracts cover admission, URL-only/missing/tampered RAW exclusion, mixed constituents, aggregate/provider integrity, historical preservation, trace parity, HUMAN_REAL replay, public fail-closed behavior and deterministic artifact regeneration.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: false for TD-001; TD-002, TD-003, TD-004 and P1 operability still block the program gate.
- BLOCKS_FIELD_TESTING: false for TD-001; the program remains `CONDITIONAL_SHADOW_ONLY` because other P0s remain.
- BLOCKS_PROMOTION: false for TD-001; promotion remains unauthorized at program level.
- NOTES: Closed without acquisition, new data, inferred lineage, threshold changes, historical rewrites or runtime learning writes. See `data/evaluation/runtime_cohort_lineage_gate_v1.json`.

### TD-002 — Local cohort geography treats provider location as service reach

- DEBT_ID: `TD-002`
- TITLE: Local cohort geography treats provider location as service reach.
- CATEGORY: CORRECTNESS, SAFETY, ARCHITECTURAL_CONSISTENCY, DATA_LINEAGE.
- SEVERITY: `P0`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `offer-service-reach-admission-gate-v1`.
- EVIDENCE: Provider location is known for 273 observations, while explicit service reach is OBSERVED for 1 and UNKNOWN for 272. Of the 84 eligible observations, 31 pass RAW-lineage but fail reach, 1 passes reach but fails lineage, 52 fail both and 0 pass both. The active projections therefore change from 18 local/4 remote cohorts to 0/0 without deleting any source observation.
- REPRODUCTION: Regenerate `offer_service_reach_admission_gate_v1.json`; the 31 previously admitted observations are excluded with `MISSING_SERVICE_REACH`. Observation 234 proves the independent inverse path: its explicit `NAMED_AREA:Córdoba` reach passes while its RAW-lineage decision fails.
- AFFECTED_FILES: `scripts/build_pricing_statistics.py`, `src/aplicacion/service_reach_admission_gate.py`, `src/aplicacion/runtime_cohort_lineage_gate.py`, `src/aplicacion/pricing_cohort_loader.py`, `src/aplicacion/pricing_evidence_engine.py`, `src/api/main.py`, reach-gated pricing projections and the TD-002 evaluation artifact.
- AFFECTED_LAYERS: APPLICATION, DATA_ARTIFACTS, COMPARABILITY.
- ROOT_CAUSE: A legacy provider/source location field was reused as runtime market before reach was typed.
- PRODUCT_IMPACT: Evidence can be shown for a province the provider has not demonstrated serving.
- DATA_RISK: Provider geography and service geography become indistinguishable.
- SAFETY_RISK: Geographically non-comparable offers can enter ranges.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: Every LOCAL_SERVICE cohort.
- DEPENDENCIES: None.
- IMPLEMENTED_FIX: Compose offer-level RAW-lineage and service-reach decisions before aggregation. LOCAL requires an exact source-observed `NAMED_AREA` or `PROVINCE` match; REMOTE_NATIONAL requires explicit `NATIONAL`; provider location and remote capability are retained as distinct facts but never admit reach. Runtime loading rejects projections without both gate-version markers.
- REGRESSION_TEST: Eleven contracts cover provider-location isolation, UNKNOWN exclusion, exact local match, mismatch, REMOTE-not-NATIONAL, explicit NATIONAL, both asymmetric gate failures, joint admission and aggregate integrity, runtime/API fail-closed behavior, legacy-artifact rejection and deterministic replay.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false for TD-002; unresolved TD-003, TD-004 and P1 operability still block the program gate.
- BLOCKS_FIELD_TESTING: false for TD-002; the program remains `CONDITIONAL_SHADOW_ONLY` because other P0s remain.
- BLOCKS_PROMOTION: false for TD-002; promotion remains unauthorized at program level.
- NOTES: Closed without acquisition, inferred reach, containment, historical rewrites, HUMAN_REAL mutation or runtime learning writes. Exact conservative geography remains the policy. See `data/evaluation/offer_service_reach_admission_gate_v1.json`.

### TD-003 — Runtime pricing evidence has no enforceable temporal or freshness contract

- DEBT_ID: `TD-003`
- TITLE: Runtime pricing evidence has no enforceable temporal or freshness contract.
- CATEGORY: CORRECTNESS, REPRODUCIBILITY, DATA_LINEAGE, SAFETY.
- SEVERITY: `P0`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: All 273 semantic rows lack an `acquired_at` column; all four legacy RAW-manifest `acquired_at` values are blank; cohort/API evidence exposes no acquisition window or freshness state.
- REPRODUCTION: Inspect headers/values of `semantic_normalization_v4.csv`, `offer_evidence_raw_manifest_v1.csv`, runtime cohort CSVs and the API evidence payload.
- AFFECTED_FILES: `data/semantic_normalization_v4.csv`, `data/offer_evidence_raw_manifest_v1.csv`, `scripts/build_pricing_statistics.py`, `src/aplicacion/pricing_evidence_engine.py`, `src/api/main.py`.
- AFFECTED_LAYERS: DATA_ARTIFACTS, APPLICATION, API.
- ROOT_CAUSE: Fixture, publication and acquisition time were never unified before historical data became runtime input.
- PRODUCT_IMPACT: Enki cannot say whether a range is current, historical or mixed.
- DATA_RISK: New observations can silently coexist with undated legacy rows.
- SAFETY_RISK: Stale evidence can look current.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: All runtime cohorts and future reacquisition.
- DEPENDENCIES: TD-001.
- PROPOSED_FIX: Propagate acquired/publication/snapshot/extractor identity, type temporal state and fail closed on incompatible/unknown mixes under an explicit policy.
- REGRESSION_TEST_REQUIRED: Historical/current mixes without exact offer identity yield TEMPORAL_MISMATCH or insufficient evidence, never silent replacement.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: true.
- BLOCKS_FIELD_TESTING: true for economic-result reliance.
- BLOCKS_PROMOTION: true.
- NOTES: The two newer selective RAW snapshots have timestamps; propagation into the baseline/runtime is the missing contract.

### TD-004 — Commercial context has divergent sources of truth and false trace projection

- DEBT_ID: `TD-004`
- TITLE: Commercial context has divergent sources of truth and false trace projection.
- CATEGORY: CORRECTNESS, OBSERVABILITY, DUPLICATED_LOGIC, SAFETY.
- SEVERITY: `P0`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: Query runtime uses `_commercial_context`, cohorts use `infer_commercial_context`, and trace economic dimensions hardcode `STANDARD`. A probe selected `pricing-cohort:AR:SOPORTE_REMOTO:PER_HOUR:URGENCY` while trace declared inferred `STANDARD`.
- REPRODUCTION: Resolve “me quieren cobrar 48 lucas la hora por soporte remoto de urgencia, esta bien?” and compare engine evidence id with trace economic context.
- AFFECTED_FILES: `src/aplicacion/enki_pricing_query_service.py`, `src/aplicacion/pricing_dimensions.py`, `src/infraestructura/real_world_query_tracer.py`, `scripts/build_pricing_statistics.py`.
- AFFECTED_LAYERS: APPLICATION, INFRASTRUCTURE, TRACING, COMPARABILITY.
- ROOT_CAUSE: Context was implemented independently in source inference, query selection and trace projection.
- PRODUCT_IMPACT: Trace truth is false and vocabulary drift can select the wrong cohort.
- DATA_RISK: Persistent traces contain a context not derived from actual selection.
- SAFETY_RISK: Standard and urgency prices can be misexplained or mismatched.
- MAINTENANCE_COST: MEDIUM.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: All non-standard contexts and trace consumers.
- DEPENDENCIES: None.
- PROPOSED_FIX: One typed CommercialContext with raw basis/provenance consumed by parser, builder, engine and trace.
- REGRESSION_TEST_REQUIRED: STANDARD/URGENCY vocabulary matrix and exact engine/trace accepted-evidence parity.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: true.
- BLOCKS_FIELD_TESTING: true for trace/economic-result reliance.
- BLOCKS_PROMOTION: true.
- NOTES: The prior selected-evidence-id mismatch is verified fixed; this is a separate dimension projection defect.

### TD-005 — Repository-wide direct CLI/import contract is not defined or enforced

- DEBT_ID: `TD-005`
- TITLE: Repository-wide direct CLI/import contract is not defined or enforced.
- CATEGORY: OPERABILITY, DEVELOPER_EXPERIENCE, TESTABILITY, REPRODUCIBILITY.
- SEVERITY: `P1`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: 45 intended scripts; 41 import `src`; 39 lack bootstrap; 33 safe help probes failed on `src`, one failed on `scripts`, six remain statically affected.
- REPRODUCTION: Remove PYTHONPATH and invoke argparse surfaces as `.venv/Scripts/python.exe scripts/<name>.py --help`; `build_knowledge_candidates.py` reproduces the known failure.
- AFFECTED_FILES: `scripts/*.py`, `pyproject.toml`, `tests/test_trace_real_query_cli.py`.
- AFFECTED_LAYERS: SCRIPTS_OPERABILITY, PACKAGING, TESTS.
- ROOT_CAUSE: No installed console-script/module contract; rooted pytest imports conceal direct-file semantics.
- PRODUCT_IMPACT: Real acquisition/evaluation/artifact commands fail as direct files.
- DATA_RISK: Ad-hoc environment/path workarounds make outputs non-reproducible.
- SAFETY_RISK: LOW; mostly fail-fast.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: 40/45 surfaces confirmed or potentially affected.
- DEPENDENCIES: None.
- PROPOSED_FIX: Select one installed/module execution contract, add package metadata, and boundary-test every intended CLI safely.
- REGRESSION_TEST_REQUIRED: Parameterized subprocess tests with PYTHONPATH removed; destructive paths restricted to help/temp probes.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: true.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: DIRECT_SAFE 5; BROKEN_CONFIRMED 34; POTENTIALLY_BROKEN 6; NOT_INTENDED 0.

### TD-006 — Real-query interpretation defects remain across five causal families

- DEBT_ID: `TD-006`
- TITLE: Real-query interpretation defects remain across five causal families.
- CATEGORY: CORRECTNESS, TESTABILITY, DOMAIN_MODEL.
- SEVERITY: `P1`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: Current v2 replay yields 21 wrong interpretations, partitioned above, with zero unsafe decisions.
- REPRODUCTION: Run `python -m scripts.audit_real_query_corpus` against v2 local/remote stats to a temp output.
- AFFECTED_FILES: `src/aplicacion/parser_consulta_pricing.py`, `src/aplicacion/enki_pricing_query_service.py`, `src/aplicacion/technical_need_market_resolution.py`, `data/language/real_query_corpus_v1.jsonl`.
- AFFECTED_LAYERS: APPLICATION, DOMAIN, EVALUATION.
- ROOT_CAUSE: Intent, aliases, context and market routing evolved independently without root-cause-partitioned remediation.
- PRODUCT_IMPACT: Valid language is misunderstood, prematurely rejected or routed to the wrong evidence state.
- DATA_RISK: Aggregate totals hide causal regressions.
- SAFETY_RISK: Audited corpus remains fail-closed.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: 21/50 adjudicated cases.
- DEPENDENCIES: TD-007, TD-011.
- PROPOSED_FIX: Separate causal sprints for gate order, market resolution, intent, aliases, context and currency normalization.
- REGRESSION_TEST_REQUIRED: Per-cause deltas, no new wrong cases, zero unsafe decisions.
- ESTIMATED_SCOPE: XL_SPLIT_REQUIRED.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Legitimate UNKNOWN/insufficient evidence is not counted unless it contradicts adjudication.

### TD-007 — Terminal unsupported checks run after clarification selection

- DEBT_ID: `TD-007`
- TITLE: Terminal unsupported checks run after clarification selection.
- CATEGORY: CORRECTNESS, APPLICATION_SERVICES, TESTABILITY.
- SEVERITY: `P1`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: Four bundles, one USDT query and one non-economic fragment are adjudicated SAFE_UNSUPPORTED but return CLARIFICATION_REQUIRED.
- REPRODUCTION: Replay `rq013`, `rq015`, `rq017`, `rq027`, `rq039`, `rq043`.
- AFFECTED_FILES: `src/aplicacion/enki_pricing_query_service.py`, `src/aplicacion/parser_consulta_pricing.py`, `data/language/real_query_corpus_v1.jsonl`.
- AFFECTED_LAYERS: APPLICATION, PARSER, EVALUATION.
- ROOT_CAUSE: Clarification precedes terminal eligibility/currency/bundle checks.
- PRODUCT_IMPACT: Enki asks irrelevant follow-ups for requests that remain unsupported.
- DATA_RISK: Feedback can misclassify eligibility defects as missing context.
- SAFETY_RISK: Fail-closed but misleading.
- MAINTENANCE_COST: MEDIUM.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: Six known cases and analogous inputs.
- DEPENDENCIES: None.
- PROPOSED_FIX: Establish explicit order: parsed facts → terminal eligibility → actionable clarification → evidence/readiness.
- REGRESSION_TEST_REQUIRED: Six safe-unsupported regressions plus valid clarification controls.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: No bundle decomposition is permitted.

### TD-008 — Artifact lifecycle mixes historical snapshots, mutable defaults and nondeterministic telemetry

- DEBT_ID: `TD-008`
- TITLE: Generated artifact lifecycle mixes historical snapshots, mutable defaults and nondeterministic telemetry.
- CATEGORY: REPRODUCIBILITY, OPERABILITY, DATA_MIGRATION_VERSIONING, IDEMPOTENCE.
- SEVERITY: `P1`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: Generators default to tracked versioned paths; trace rows contain latency outside their fingerprint; historical E2E/performance files have old HEAD/time/runtime results without a common run manifest; tests assert static fields rather than freshness.
- REPRODUCTION: Inspect generator defaults/write helpers, build traces into two temp directories and compare timing-bearing outputs, then compare historical artifacts to current HEAD/replay.
- AFFECTED_FILES: `src/infraestructura/real_world_query_tracer.py`, `src/infraestructura/real_world_trace_artifact.py`, `src/infraestructura/*_artifact.py`, `scripts/*.py`, `data/e2e/full_product_e2e_v1.json`.
- AFFECTED_LAYERS: INFRASTRUCTURE, SCRIPTS_OPERABILITY, DATA_ARTIFACTS, TESTS.
- ROOT_CAUSE: Per-sprint version/idempotence conventions lack repository-wide artifact classes.
- PRODUCT_IMPACT: Operators cannot uniformly distinguish current, historical, reproducible and regenerable outputs.
- DATA_RISK: Historical tracked artifacts can be overwritten or silently stale.
- SAFETY_RISK: Conclusions can be attributed to the wrong code/input snapshot.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: Most artifact generators.
- DEPENDENCIES: TD-005.
- PROPOSED_FIX: Define immutable evidence vs deterministic derived output vs telemetry; add commit/input/generator/output hashes; require explicit historical destinations.
- REGRESSION_TEST_REQUIRED: Fixed inputs hash-identically across clean runs; immutable paths reject mutation; telemetry is separate.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: true.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: true.
- NOTES: Append-only HUMAN_REAL is verified correct and excluded from this debt.

### TD-009 — Offer and price-expression identity is fragmented and incomplete

- DEBT_ID: `TD-009`
- TITLE: Offer and price-expression identity is fragmented and incomplete.
- CATEGORY: DOMAIN_MODEL, DATA_LINEAGE, ARCHITECTURAL_CONSISTENCY.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: 5 resolved offer identities for 273 observations; offer key, economic dimensions, RAW linkage and cohort membership live in separate partial contracts; runtime has no constituent identity.
- REPRODUCTION: Count `offer_evidence_identities_v1.jsonl` and trace one observation through identity, evidence, dimensions, scope sidecar and runtime cohort.
- AFFECTED_FILES: `src/dominio/oferta.py`, `src/dominio/offer_evidence.py`, `src/dominio/price_scope_contract.py`, `data/offer_evidence_identities_v1.jsonl`, `data/economic_dimensions_v2.jsonl`, `data/pricing_cohort_scope_evidence_v1.jsonl`.
- AFFECTED_LAYERS: DOMAIN, INFRASTRUCTURE, DATA_ARTIFACTS.
- ROOT_CAUSE: Sidecars accumulated around a legacy row instead of one versioned OfferObservation aggregate.
- PRODUCT_IMPACT: Corrections, temporal replacement and comparability require fragile multi-file joins.
- DATA_RISK: Multi-price offers or repeated snapshots can be conflated.
- SAFETY_RISK: No additional current unsafe result beyond TD-001 demonstrated.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: MEDIUM.
- BLAST_RADIUS: Evidence, cohorts, temporal reconciliation and acquisition reuse.
- DEPENDENCIES: None.
- PROPOSED_FIX: Versioned OfferObservation composing offer, price expression, unit, period, bound, context, bundle/device, source observation and RAW snapshot without rewriting history.
- REGRESSION_TEST_REQUIRED: Stable identity, multi-price separation, snapshot behavior and backwards-compatible loading.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: true.
- NOTES: TD-001 is the immediate runtime gate; this is the durable model.

### TD-010 — Runtime provider independence counts source ids instead of stable provider ids

- DEBT_ID: `TD-010`
- TITLE: Runtime provider independence counts source ids instead of stable provider ids.
- CATEGORY: CORRECTNESS, ARCHITECTURAL_CONSISTENCY, DATA_LINEAGE.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: Runtime adds `row["source"]` to a set and publishes it as `providers_n`; shadow uses stable provider ids; registry can contain multiple source ids for one exact provider name.
- REPRODUCTION: Compare `build_pricing_statistics.py` with `semantic_economic_evidence_bridge.py` and provider-identity tests.
- AFFECTED_FILES: `scripts/build_pricing_statistics.py`, `src/aplicacion/semantic_economic_evidence_bridge.py`, `data/pricing_sources.csv`, `data/economic_dimensions_v2.jsonl`.
- AFFECTED_LAYERS: APPLICATION, DATA_ARTIFACTS, READINESS.
- ROOT_CAUSE: Runtime statistics predate stable provider identity.
- PRODUCT_IMPACT: Multi-page/provider acquisition can inflate or deflate readiness.
- DATA_RISK: Provider/source/URL/document/observation/temporal independence collapse into one count.
- SAFETY_RISK: No current DECISION_READY is affected; future threshold risk is concrete.
- MAINTENANCE_COST: MEDIUM.
- LIKELIHOOD: HIGH_DURING_ACQUISITION.
- BLAST_RADIUS: Future cohort confidence/readiness.
- DEPENDENCIES: TD-009.
- PROPOSED_FIX: Carry provider_id and expose all independence axes separately; only stable provider id feeds `providers_n`.
- REGRESSION_TEST_REQUIRED: Same provider across sources counts once; distinct providers count separately; UNKNOWN never fabricates independence.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: true.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: true.
- NOTES: Frequency is not independence.

### TD-011 — Price-scope parsing remains duplicated between user and source paths

- DEBT_ID: `TD-011`
- TITLE: Price-scope parsing remains duplicated between user and source paths.
- CATEGORY: DUPLICATED_LOGIC, ARCHITECTURAL_CONSISTENCY, MAINTAINABILITY.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: User input uses typed `normalize_price_scope`; source/cohort/adapters use overlapping but different `infer_price_scope` regexes.
- REPRODUCTION: Search all consumers and compare the two implementations/pattern sets.
- AFFECTED_FILES: `src/dominio/price_scope_contract.py`, `src/aplicacion/pricing_dimensions.py`, `src/aplicacion/parser_consulta_pricing.py`, `scripts/build_pricing_statistics.py`, `src/infraestructura/economic_dimensions_v2_adapter.py`.
- AFFECTED_LAYERS: DOMAIN, APPLICATION, INFRASTRUCTURE.
- ROOT_CAUSE: Source cadence inference survived introduction of the typed user contract.
- PRODUCT_IMPACT: Equivalent phrases can normalize differently by origin.
- DATA_RISK: Cohort keys drift after vocabulary changes.
- SAFETY_RISK: Current UNKNOWN behavior fails closed; no new unsafe decision demonstrated.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: MEDIUM.
- BLAST_RADIUS: Parser, dimensions, cohorts and reconciliation.
- DEPENDENCIES: None.
- PROPOSED_FIX: One typed semantic engine with origin-specific provenance/raw basis.
- REGRESSION_TEST_REQUIRED: Shared phrase matrix and origin provenance; UNKNOWN remains insufficient.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: true.
- NOTES: Distinct provenance is correct; duplicate semantic rules are not.

### TD-012 — Acquisition boundaries collapse exceptions into counters without causal diagnostics

- DEBT_ID: `TD-012`
- TITLE: Acquisition boundaries collapse exceptions into counters without causal diagnostics.
- CATEGORY: OBSERVABILITY, OPERABILITY, EXCEPTION_HANDLING.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: Raw/USASpending collectors return `failed=1` without cause; Argentina bulk drops exception detail; CompraGamer response JSON errors are silently passed.
- REPRODUCTION: Inspect broad exception paths or inject a failing client and examine result diagnostics.
- AFFECTED_FILES: `src/aplicacion/colector_documentos_raw.py`, `src/aplicacion/colector_argentina_bulk.py`, `src/aplicacion/colector_usaspending.py`, `src/infraestructura/scrapers/compragamer_playwright_scraper.py`.
- AFFECTED_LAYERS: APPLICATION, INFRASTRUCTURE, ACQUISITION.
- ROOT_CAUSE: Batch-continuation counters predate a typed failure contract.
- PRODUCT_IMPACT: Operators cannot distinguish network, auth, schema, parse or persistence failure.
- DATA_RISK: Empty acquisition can be mistaken for absent market evidence.
- SAFETY_RISK: No fabricated data, but absence cause is obscured.
- MAINTENANCE_COST: MEDIUM.
- LIKELIHOOD: HIGH_DURING_ACQUISITION.
- BLAST_RADIUS: Several external acquisition flows.
- DEPENDENCIES: None.
- PROPOSED_FIX: Typed, redacted failure records with source/operation/retryability/cause while preserving batch continuation.
- REGRESSION_TEST_REQUIRED: Injected failures preserve type/cause and redact credentials/headers.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Broad exceptions that already preserve per-record reasons were not separately ticketed.

### TD-013 — Green suites under-test real process and cross-stack boundaries

- DEBT_ID: `TD-013`
- TITLE: Green suites under-test real process and cross-stack boundaries.
- CATEGORY: TESTABILITY, REPRODUCIBILITY, DEVELOPER_EXPERIENCE.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: One true no-PYTHONPATH CLI subprocess regression; most script tests import helpers; frontend mocks a hand-maintained API object; E2E artifact test is not bound to current HEAD/input hashes.
- REPRODUCTION: Compare CLI tests, frontend decision tests and `test_full_product_e2e_artifact.py` with the actual boundaries.
- AFFECTED_FILES: `tests/`, `frontend/src/features/decision/__tests__/decision-flow.test.tsx`, `pytest.ini`, `pyproject.toml`.
- AFFECTED_LAYERS: TESTS, API_FRONTEND, SCRIPTS_OPERABILITY.
- ROOT_CAUSE: Helper/sprint artifact tests grew faster than executable and schema-contract tests.
- PRODUCT_IMPACT: Full green coexists with 34 broken CLIs and schema-drift risk.
- DATA_RISK: Stale historical artifacts can be validated as current.
- SAFETY_RISK: Indirect escape path for future drift.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: Developer workflow, release and operational commands.
- DEPENDENCIES: TD-005, TD-008.
- PROPOSED_FIX: Parameterized CLI subprocess matrix, generated/shared API contract, local cross-stack smoke and artifact freshness hashes.
- REGRESSION_TEST_REQUIRED: Boundary suite must reproduce a known pre-fix failure and protect external contracts.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: true.
- NOTES: The 844-test breadth is useful; boundary selection is the debt.

### TD-014 — README and architecture baseline materially diverge from runtime

- DEBT_ID: `TD-014`
- TITLE: README and architecture baseline materially diverge from current runtime.
- CATEGORY: DOCUMENTATION, ARCHITECTURAL_CONSISTENCY, DEVELOPER_EXPERIENCE.
- SEVERITY: `P3`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: README says HEAD `40624fd`/252 tests and describes pricing engine as future; current HEAD is `b03e65e`/844 tests with a decision runtime. ARCHITECTURE names README as highest source while governance uses the Rector.
- REPRODUCTION: Compare README sections 6/14/17, ARCHITECTURE introduction, current Git/test/runtime and Rector.
- AFFECTED_FILES: `README.md`, `ARCHITECTURE.md`, `docs/ENKI_ARCHIVO_RECTOR.md`.
- AFFECTED_LAYERS: DOCUMENTATION, REPOSITORY.
- ROOT_CAUSE: Causal sprint narratives accumulated without a maintained current-state index.
- PRODUCT_IMPACT: Operators select stale commands, priorities and baselines.
- DATA_RISK: LOW.
- SAFETY_RISK: LOW.
- MAINTENANCE_COST: MEDIUM.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: Onboarding and planning.
- DEPENDENCIES: None.
- PROPOSED_FIX: Explicit Rector precedence; separate current state from history; prefer verifiable commands over volatile prose counts.
- REGRESSION_TEST_REQUIRED: Documentation path/command smoke; avoid volatile count assertions.
- ESTIMATED_SCOPE: S.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Documentation-only remediation.

### TD-015 — Dependency and test configuration carry duplicated and deprecated surfaces

- DEBT_ID: `TD-015`
- TITLE: Dependency and test configuration carry duplicated and deprecated surfaces.
- CATEGORY: DEPENDENCIES, DEPRECATIONS, DEVELOPER_EXPERIENCE, CONFIGURATION.
- SEVERITY: `P3`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: pytest ignores pyproject pytest config because pytest.ini wins; backend emits Starlette/asyncio deprecation; frontend emits Vite CJS deprecation; full transitive requirements include unreferenced `httpx2`; pyproject lacks project/build metadata. `pip check` is green.
- REPRODUCTION: Run backend/frontend tests, inspect both pytest configs and search imports for `httpx2`.
- AFFECTED_FILES: `requirements.txt`, `pyproject.toml`, `pytest.ini`, `frontend/package.json`, `frontend/vitest.config.ts`, `frontend/pnpm-lock.yaml`.
- AFFECTED_LAYERS: CONFIGURATION, TESTS, FRONTEND, PACKAGING.
- ROOT_CAUSE: Incremental environment snapshots without direct dependency ownership or a single config authority.
- PRODUCT_IMPACT: Warnings mask future incompatibility and packaging stays implicit.
- DATA_RISK: NONE.
- SAFETY_RISK: LOW.
- MAINTENANCE_COST: MEDIUM.
- LIKELIHOOD: MEDIUM.
- BLAST_RADIUS: Setup, tests and upgrades.
- DEPENDENCIES: TD-005.
- PROPOSED_FIX: Prove direct dependencies, remove unused entries, establish package metadata/one pytest authority, then isolate upgrades.
- REGRESSION_TEST_REQUIRED: `pip check`, full backend, frontend lint/test/build and CLI/package smoke.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: No dependency update is part of this audit.

### TD-016 — Legacy compatibility modules and unused fixture adapters obscure canonical ownership

- DEBT_ID: `TD-016`
- TITLE: Legacy compatibility modules and unused fixture adapters obscure canonical ownership.
- CATEGORY: MAINTAINABILITY, DEAD_CODE, PARALLEL_SOURCES_OF_TRUTH.
- SEVERITY: `P3`.
- CONFIDENCE: HIGH.
- STATUS: CONFIRMED.
- EVIDENCE: `src/scrapers` wraps `src/infraestructura/scrapers` with wildcard exports/fallback; tests use both paths; frontend `interpret-quote.ts` returns fixtures and has no live consumer.
- REPRODUCTION: Inventory wrappers and search consumers of `src.scrapers`, `interpretQuoteForReview` and `createDecisionReadout`.
- AFFECTED_FILES: `src/scrapers/`, `src/infraestructura/scrapers/`, `tests/`, `frontend/src/features/decision/interpret-quote.ts`, `frontend/src/features/decision/fixtures/support-quote.ts`.
- AFFECTED_LAYERS: INFRASTRUCTURE, TESTS, FRONTEND.
- ROOT_CAUSE: Brownfield compatibility lacks a retirement ledger; prototype adapters remained after API integration.
- PRODUCT_IMPACT: Developers can extend the wrong namespace or mistake fixtures for product logic.
- DATA_RISK: NONE.
- SAFETY_RISK: LOW.
- MAINTENANCE_COST: MEDIUM.
- LIKELIHOOD: MEDIUM.
- BLAST_RADIUS: Scraper maintenance and frontend navigation.
- DEPENDENCIES: TD-013.
- PROPOSED_FIX: Prove consumers, declare canonical ownership, use explicit temporary deprecations, migrate tests, remove only proven-dead code.
- REGRESSION_TEST_REQUIRED: Canonical/temporary compatibility imports and frontend build/dead-code checks.
- ESTIMATED_SCOPE: S.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: No compatibility file is removed during this audit.

## Dependency graph

```text
TD-001 runtime lineage ───────> TD-003 temporal admissibility
TD-009 offer identity ────────> TD-010 provider independence
TD-011 scope truth ───────────> TD-006 interpretation recovery
TD-007 gate precedence ───────> TD-006 interpretation recovery
TD-005 CLI contract ──────────> TD-008 artifact lifecycle ──> TD-013 boundary tests
TD-005 CLI contract ─────────────────────────────────────────> TD-013 boundary tests
TD-005 CLI contract ──────────> TD-015 dependency/config
TD-013 boundary tests ────────> TD-016 legacy retirement
```

TD-004 can be remediated independently. Market acquisition still requires TD-003/004/005/008/010. Promotion additionally requires TD-009/011/013.

## Remediation waves

### WAVE 0 — P0 correctness and safety

1. **RUNTIME COHORT LINEAGE GATE v1 — COMPLETE** — Every contributor is auditable or fails closed. Closed TD-001.
2. **OFFER SERVICE REACH ADMISSION GATE v1 — COMPLETE** — Provider location and remote capability cannot stand in for explicit offer reach. Closed TD-002.
3. **TEMPORAL EVIDENCE ADMISSIBILITY v1** — Goal: type/enforce acquisition and freshness. Closes TD-003. Files: observation/cohort/API contracts. Risk: high. Tests: historical/current mismatch and freshness. Exit: every admitted row/cohort has explicit temporal state/window. Dependency: lineage gate.
4. **COMMERCIAL CONTEXT SINGLE TRUTH v1** — Goal: unify context and trace truth. Closes TD-004. Files: context/parser/service/tracer. Risk: high. Tests: STANDARD/URGENCY matrix and engine/trace parity. Exit: parsed/selected/traced values and raw basis match. Dependency: none.

### WAVE 1 — P1 operability and reproducibility

1. **CLI EXECUTION CONTRACT v1** — TD-005; risk medium; all 45 surfaces explicitly classified and intended CLIs subprocess-green without PYTHONPATH.
2. **ARTIFACT RUN MANIFEST v1** — TD-008; dependency CLI; risk medium; deterministic outputs have commit/input/output hashes and historical writes are explicit.
3. **QUERY GATE PRECEDENCE v1** — TD-007; risk medium; six known cases become safe unsupported without valid-clarification drift.
4. **REAL QUERY CAUSAL RECOVERY v1-v3** — TD-006; dependencies gate precedence and scope engine; risk medium; separate market, intent/alias and context/normalization sprints with zero new wrong/unsafe cases.

### WAVE 2 — Provenance and data model

1. **OFFER OBSERVATION IDENTITY v1** — TD-009; risk medium; stable multi-price/snapshot identity with backwards-compatible loading.
2. **PROVIDER INDEPENDENCE CONTRACT v1** — TD-010; dependency offer identity; risk high because readiness inputs change while thresholds remain untouched; provider/source/document/URL/observation/time axes become explicit.
3. **PRICE SCOPE SINGLE ENGINE v1** — TD-011; risk medium; one semantic engine with distinct origins and UNKNOWN fail-closed.

### WAVE 3 — Architecture and test consolidation

1. **ACQUISITION FAILURE TAXONOMY v1** — TD-012; risk low; typed/redacted causal failures replace unexplained counters.
2. **REAL BOUNDARY TEST MATRIX v1** — TD-013; dependencies CLI/artifact; risk low; CLI, API/frontend and artifact freshness failures cannot pass green.

### WAVE 4 — Deprecations and maintenance

1. **CURRENT STATE DOCUMENTATION v1** — TD-014; risk low; Rector precedence/current state are unambiguous.
2. **DEPENDENCY CONFIG CONSOLIDATION v1** — TD-015; dependency CLI; risk medium; direct dependencies/package metadata/one pytest authority and causal deprecation upgrades.
3. **LEGACY SURFACE RETIREMENT v1** — TD-016; dependency boundary tests; risk low; one canonical scraper namespace and no unused fixture adapter.

Estimated consolidation: **18 small causal sprints** (the broad interpretation item is explicitly split into three). No wave is authorized by this document.

## Gates

### SAFE_FOR_FOUNDER_FIELD_TESTING

`CONDITIONAL_SHADOW_ONLY`. Continue append-only HUMAN_REAL capture and supervised parser/clarification observation. Do not rely on displayed economic ranges until TD-003 and TD-004 close. Keep promotion and runtime learning writes disabled.

### SAFE_FOR_MARKET_ACQUISITION_EXPANSION

`NO`. Required closures: TD-003, TD-004, TD-005, TD-008 and TD-010. This is risk-based, not “debt zero”: corpus cleanup, documentation and legacy wrappers do not block acquisition.

### SAFE_FOR_KNOWLEDGE_PROMOTION

`NO`. Required closures: TD-003, TD-004, TD-008, TD-009, TD-010, TD-011 and TD-013; additionally, the current candidate remains `FAIL_SHADOW_VALIDATION`. Existing currency conflicts remain preserved and no promotion is authorized.

## Exact next remediation sprint

**TEMPORAL EVIDENCE ADMISSIBILITY v1**. It closes only TD-003. Every admitted row and cohort must carry an explicit temporal state and enforceable freshness window while preserving historical evidence and existing thresholds. TD-004 remains independent and out of scope for that sprint.

## Explicitly not debt

- Legitimate UNKNOWN, real evidence insufficiency and absence of DECISION_READY.
- Current candidate `FAIL_SHADOW_VALIDATION` and preserved currency conflicts 159–161.
- Safe bundle exclusion/no silent decomposition; no silent currency conversion.
- Append-only HUMAN_REAL_001, RAW input, founder feedback as unpromoted evidence, and zero runtime learning writes.
- No orphan worktree metadata; one valid registered worktree.
- Ignored `.venv`, caches, node_modules and build outputs.
- No material measured performance regression.
- No tracked secret/private-key/credential file found.

## Rector alignment

The register treats missing knowledge as UNKNOWN rather than false, preserves RAW/canonical and historical artifacts, requires provenance and independence, rejects silent geography/currency/bundle inference, keeps candidates shadow-only, changes no thresholds, and proposes reversible fail-closed contracts. The P0 prioritization follows the Rector: economic evidence must be comparable, recent and auditable before Enki exploits it.

## Final validation

- Backend full suite: `844 passed, 0 failed, 1 warning in 35.53s` (`37.271s` wall clock). The warning is the recorded Starlette/httpx deprecation.
- Compile: `python -m compileall src scripts` passed in `0.35s`.
- Frontend: lint passed; `10/10` tests passed; production build passed. Vite emitted the recorded CJS API deprecation.
- Dependencies: `pip check` reported no broken requirements.
- Audit artifact: valid JSON, 16/16 items contain every required field, and its SHA-256 was unchanged across the full suite.
- Product/evidence mutation: none; `data/field/` was not modified.
