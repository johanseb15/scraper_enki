# Enki Technical Debt Register

Audit version: `technical-debt-audit-v1`

Program: ENKI TECHNICAL DEBT CONSOLIDATION

Baseline: `main@b03e65ef287e3286bcca47e0355852b4fb8b6d77`

Machine-readable sources: `data/evaluation/technical_debt_audit_v1.json` (historical audit), `data/evaluation/runtime_cohort_lineage_gate_v1.json` (TD-001 remediation), `data/evaluation/offer_service_reach_admission_gate_v1.json` (TD-002 remediation), and `data/evaluation/temporal_evidence_admissibility_v1.json` (TD-003 remediation).

## Executive decision

The repository is test-green, but it is not yet safe to expand real market acquisition or authorize knowledge promotion. TD-001 is resolved by a fail-closed constituent RAW-lineage gate, TD-002 by a composable explicit service-reach gate, TD-003 by explicit temporal identity/current-compatibility admission, and TD-004 by one typed commercial-context truth propagated through parser, runtime, comparability and trace. No P0 remains open. Founder field testing may continue under supervision; the active runtime still has zero admitted evidence and promotion/runtime learning writes remain disabled.

The TD-003 remediation recovers only explicit RAW/manifest temporal facts, keeps all five dated observations historical because no freshness policy exists, and excludes all UNKNOWN or incompatible temporal states from current pricing. Filesystem timestamps, historical evidence, HUMAN_REAL data, readiness thresholds and promotion state remain untouched.

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

Historical audit baseline against v2 cohorts produced `21 WRONG_INTERPRETATION`, `0 UNSAFE_DECISION`: intent 3, semantic alias 2, technical need 0, market resolution 7, normalization 1, commercial context 3, device 0, other control-flow/bundle 5. TD-006 remediation later reduced the official 50-case runtime replay to `0 WRONG_INTERPRETATION` and `0 UNSAFE_DECISION`; this partition is retained as the historical root-cause baseline, not current state.

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
- STATUS: RESOLVED by `temporal-evidence-admissibility-v1`.
- EVIDENCE: The 273 semantic rows still correctly preserve their original schema without invented dates. Exact RAW identity joins recover `acquired_at` for 5 observations and exact month/year price context for 30; 268 remain `TEMPORAL_UNKNOWN`. Because no validated freshness policy exists, all 5 dated observations are `HISTORICAL_REPRODUCIBLE`, none is `CURRENT_REPRODUCIBLE`, and current-pricing admission remains 0/84.
- REPRODUCTION: Regenerate `temporal_evidence_admissibility_v1.json`; runtime temporal decisions exclude 79 eligible observations with `MISSING_TEMPORAL_PROVENANCE` and 5 with `TEMPORAL_MISMATCH`/`FRESHNESS_POLICY_UNKNOWN`. Filesystem mtime/ctime/git/sync timestamps are never read as evidence.
- AFFECTED_FILES: `src/dominio/temporal_evidence.py`, `src/aplicacion/temporal_evidence_admission_gate.py`, `src/aplicacion/runtime_cohort_lineage_gate.py`, `src/infraestructura/temporal_evidence_artifact.py`, `scripts/build_pricing_statistics.py`, temporal sidecars/projections, cohort loader/engine and API projection.
- AFFECTED_LAYERS: DATA_ARTIFACTS, APPLICATION, API.
- ROOT_CAUSE: Fixture, publication and acquisition time were never unified before historical data became runtime input.
- PRODUCT_IMPACT: Enki cannot say whether a range is current, historical or mixed.
- DATA_RISK: New observations can silently coexist with undated legacy rows.
- SAFETY_RISK: Stale evidence can look current.
- MAINTENANCE_COST: HIGH.
- LIKELIHOOD: HIGH.
- BLAST_RADIUS: All runtime cohorts and future reacquisition.
- DEPENDENCIES: TD-001.
- IMPLEMENTED_FIX: A deterministic temporal sidecar joins only exact offer/RAW identities to captured acquisition manifests, preserves raw month/year price context without adding precision, and types `CURRENT_REPRODUCIBLE`, `HISTORICAL_REPRODUCIBLE`, `TEMPORAL_UNKNOWN`, `TEMPORAL_CONFLICT` and `TEMPORAL_MISMATCH`. The third independent admission gate requires both temporal identity and an explicit compatible freshness policy before aggregation; no policy or threshold was invented.
- REGRESSION_TEST: Thirteen focused contracts cover exact RAW recovery, missing acquisition, filesystem rejection, historical preservation, UNKNOWN/conflict/mismatch, every required gate composition, causal exclusion visibility, API/trace fail-closed behavior and exact artifact/sidecar regeneration.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: false for TD-003; unresolved TD-004 and P1 operability still block the program gate.
- BLOCKS_FIELD_TESTING: false for TD-003; the program remains `CONDITIONAL_SHADOW_ONLY` because TD-004 remains.
- BLOCKS_PROMOTION: false for TD-003; promotion remains unauthorized at program level.
- NOTES: Closed without acquisition, fabricated dates, freshness thresholds, historical rewrites, HUMAN_REAL mutation or runtime learning writes. See `data/evaluation/temporal_evidence_admissibility_v1.json`.

### TD-004 — Commercial context has divergent sources of truth and false trace projection

- DEBT_ID: `TD-004`
- TITLE: Commercial context has divergent sources of truth and false trace projection.
- CATEGORY: CORRECTNESS, OBSERVABILITY, DUPLICATED_LOGIC, SAFETY.
- SEVERITY: `P0`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `commercial-context-single-truth-v1`.
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
- IMPLEMENTED_FIX: `CommercialContext` is the single typed identity for user and source claims, preserves distinct origin/raw basis, represents STANDARD/URGENCY/UNKNOWN/AMBIGUOUS, and is propagated without reinterpretation through parser, cohort selection, comparability, API and trace. UNKNOWN and AMBIGUOUS fail closed.
- REGRESSION_TEST: End-to-end STANDARD/URGENCY/UNKNOWN/AMBIGUOUS, user/source provenance, mismatch/unknown-side safety, rq003/rq032, API boundary, corpus 50, HUMAN_REAL and exact engine/trace parity.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false for TD-004; no remaining blocker is attributed to TD-008.
- BLOCKS_FIELD_TESTING: false; supervised field testing remains non-promotional and the runtime currently has zero admitted evidence.
- BLOCKS_PROMOTION: false for TD-004; candidate-validation constraints still block the program gate.
- NOTES: Closed without acquisition, thresholds, evidence additions, historical rewrites, HUMAN_REAL mutation, promotion or runtime learning writes. See `data/evaluation/commercial_context_single_truth_v1.json`.

### TD-005 — Repository-wide direct CLI/import contract is not defined or enforced

- DEBT_ID: `TD-005`
- TITLE: Repository-wide direct CLI/import contract is not defined or enforced.
- CATEGORY: OPERABILITY, DEVELOPER_EXPERIENCE, TESTABILITY, REPRODUCIBILITY.
- SEVERITY: `P1`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `enki-cli-execution-contract-v1`.
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
- REMEDIATION_NOTE: Closed with one shared `scripts/_repo_bootstrap.py` execution-boundary shim across all 49 current `__main__` entrypoints. Direct top-level probes pass 49/49 with `PYTHONPATH` unset. The project `.venv` was synchronized to the already-declared `requirements.txt`, including `truststore==0.10.4`. No product/runtime semantics changed.

### TD-006 — Real-query interpretation defects remain across five causal families

- DEBT_ID: `TD-006`
- TITLE: Real-query interpretation defects remain across five causal families.
- CATEGORY: CORRECTNESS, TESTABILITY, DOMAIN_MODEL.
- SEVERITY: `P1`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `td006-real-query-causal-recovery-v1-v3`.
- BASELINE_EVIDENCE: The historical v2 replay produced `21 WRONG_INTERPRETATION` and `0 UNSAFE_DECISION`, partitioned into intent, semantic alias, market resolution, normalization, commercial-context and control-flow/bundle causes.
- FINAL_EVIDENCE: Official runtime replay of all 50 adjudicated cases produces `28 CLARIFICATION_CORRECT`, `10 EXPECTED_SAFETY_CHANGE`, `1 PARSE_CORRECT`, `11 SAFE_UNSUPPORTED`, `0 WRONG_INTERPRETATION`, and `0 UNSAFE_DECISION`.
- REPRODUCTION: Replay `data/language/real_query_corpus_v1.jsonl` through `parse_pricing_query`, `resolver_consulta_pricing`, `trace_real_world_query`, and `adjudicate_trace` using runtime cohorts from `cargar_cohortes_pricing_runtime`; assert zero wrong and zero unsafe outcomes.
- AFFECTED_FILES: `src/aplicacion/parser_consulta_pricing.py`, `src/aplicacion/enki_pricing_query_service.py`, `scripts/audit_real_query_corpus.py`, `src/infraestructura/real_world_trace_artifact.py`, `data/evaluation/commercial_context_single_truth_v1.json`, and TD-006 regression tests.
- AFFECTED_LAYERS: APPLICATION, DOMAIN, EVALUATION.
- ROOT_CAUSE: Intent, aliases, cadence requirements, commercial context and runtime clarification/evidence ordering evolved independently without a single causal regression loop over the adjudicated real-query corpus.
- PRODUCT_IMPACT: The audited query corpus no longer contains known wrong interpretations or unsafe decisions; valid language is either parsed, safely clarified, safely unsupported, or conservatively downgraded when evidence is insufficient.
- DATA_RISK: Aggregate totals are no longer used alone; causal regression tests preserve the recovered interpretation boundaries.
- SAFETY_RISK: Fail-closed behavior preserved. No unsafe decision was introduced during remediation.
- MAINTENANCE_COST: LOW after remediation, with causal regression coverage retained.
- LIKELIHOOD: LOW for the remediated corpus families.
- BLAST_RADIUS: The original 21/50 wrong interpretations were reduced to 0/50 on the official runtime replay without unsafe promotion.
- DEPENDENCIES: TD-007 and TD-011, both resolved before final TD-006 closure.
- IMPLEMENTED_FIX: Block A recovered service/object, intent and parts-supplied semantics and aligned audit safety classification. Block B moved cadence ambiguity for `SOPORTE_REMOTO` and `VISITA_TECNICA_DOMICILIO` into semantic clarification independent of evidence availability and aligned conservative safety downgrades. Block C recovered BUY price recommendation phrasing, `conviene` evaluation, `ARMADO_PC` direct/anaphoric aliases, active SELL phrasing, and explicit labor-only component separation.
- REGRESSION_TEST: TD-006 Blocks A/B/C plus parser, pricing-query-service, price-scope, commercial-context and real-world-trace contracts cover the recovered causes and negative boundaries. Final repository suite: `993 passed`. Deterministic commercial-context artifact regeneration passes with zero boundary mismatches, trace-engine parity true, zero unexpected semantic drift, zero auto-promotions, and zero runtime learning writes.
- ESTIMATED_SCOPE: XL_SPLIT_REQUIRED, completed as three causal remediation blocks.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Legitimate UNKNOWN, clarification, unsupported and insufficient-evidence outcomes remain valid when they match adjudication. Historical baseline metrics remain preserved rather than rewritten as current truth.

### TD-007 — Terminal unsupported checks run after clarification selection

- DEBT_ID: `TD-007`
- TITLE: Terminal unsupported checks run after clarification selection.
- CATEGORY: CORRECTNESS, APPLICATION_SERVICES, TESTABILITY.
- SEVERITY: `P1`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `terminal-fact-precedence-v1`.
- EVIDENCE: Root-cause replay narrowed the original six-case hypothesis. `rq015` already carries a positive BUNDLE fact plus `BUNDLE_REQUIRES_COMPARABLE_SCOPE`, and `rq039` explicitly names unsupported USDT; both previously reached clarification first. `rq013`, `rq017`, and `rq027` remain parser/interpretation debt because their complete bundle/intent facts are not represented. `rq043` already reaches terminal unsupported without clarification.
- REPRODUCTION: Replay `rq015` and `rq039` against the published pre-fix service, then compare `rq013`, `rq017`, `rq027`, and `rq043` to distinguish gate-order from parser/intent causes.
- AFFECTED_FILES: `src/aplicacion/enki_pricing_query_service.py`, `tests/test_td007_gate_order.py`, dependent deterministic regression artifacts/tests.
- AFFECTED_LAYERS: APPLICATION, EVALUATION.
- ROOT_CAUSE: Positive terminal facts for an already-recognized unsupported bundle and an explicitly unsupported currency were evaluated after generic clarification selection.
- PRODUCT_IMPACT: Enki no longer asks an irrelevant follow-up when those terminal facts are already known.
- DATA_RISK: None added; incomplete parser facts remain fail-closed and are not promoted into terminal facts.
- SAFETY_RISK: Fail-closed.
- MAINTENANCE_COST: LOW after remediation.
- LIKELIHOOD: LOW for the remediated terminal-fact family.
- BLAST_RADIUS: Positively recognized unsupported bundles carrying the bundle terminal marker and explicit unsupported currencies.
- DEPENDENCIES: None.
- IMPLEMENTED_FIX: Advance only positively known terminal facts before clarification. Missing/unknown currency remains actionable clarification; broad UNKNOWN intent and incomplete bundle interpretations keep their existing fail-closed path.
- REGRESSION_TEST: Focused controls cover explicit bundle terminal precedence, explicit USDT precedence, missing currency, generic actionable clarification, incomplete parser bundle families, and the non-actionable fragment. Product-boundary E2E remains unchanged.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: The original six-case root-cause grouping was partially refuted by runtime probes. `rq013`, `rq017`, and `rq027` remain under TD-006; no bundle decomposition or fabricated parser facts were introduced.

### TD-008 — Artifact lifecycle mixes historical snapshots, mutable defaults and nondeterministic telemetry

- DEBT_ID: `TD-008`
- TITLE: Generated artifact lifecycle mixes historical snapshots, mutable defaults and nondeterministic telemetry.
- CATEGORY: REPRODUCIBILITY, OPERABILITY, DATA_MIGRATION_VERSIONING, IDEMPOTENCE.
- SEVERITY: `P1`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `artifact-lifecycle-contract-v1`.
- EVIDENCE: The repository now distinguishes immutable evidence, deterministic derived artifacts and telemetry; deterministic manifests carry commit, generator, input and output hashes; known mutating historical CLI entrypoints require explicit output destinations; semantic real-world traces exclude timing telemetry and replay byte-identically; HUMAN_REAL append-only paths remain protected.
- REPRODUCTION: Run `test_artifact_lifecycle_contract.py`, `test_td008_explicit_historical_outputs.py`, `test_td008_manifest_destination.py` and `test_td008_trace_telemetry_split.py`; replay real-world trace artifacts into two distinct temporary destinations and compare deterministic outputs and manifests.
- AFFECTED_FILES: `src/infraestructura/artifact_lifecycle.py`, `src/infraestructura/real_world_query_tracer.py`, `src/infraestructura/real_world_trace_artifact.py`, known mutating historical CLI entrypoints, and TD-008 regression tests.
- AFFECTED_LAYERS: INFRASTRUCTURE, SCRIPTS_OPERABILITY, DATA_ARTIFACTS, TESTS.
- ROOT_CAUSE: Per-sprint version/idempotence conventions previously lacked repository-wide artifact classes and explicit output ownership.
- PRODUCT_IMPACT: Operators can distinguish immutable evidence, deterministic derived output and telemetry, while historical generators do not silently own tracked output destinations.
- DATA_RISK: Lower; deterministic artifacts are reproducibly manifested and HUMAN_REAL append-only evidence is protected from regenerable writers.
- SAFETY_RISK: Lower; semantic conclusions no longer depend on nondeterministic timing telemetry and manifests identify code/input provenance.
- MAINTENANCE_COST: LOW after remediation.
- LIKELIHOOD: LOW after remediation.
- BLAST_RADIUS: Artifact lifecycle, trace reproducibility and historical generation entrypoints.
- DEPENDENCIES: TD-005.
- IMPLEMENTED_FIX: Added `artifact-lifecycle-contract-v1`, explicit artifact classes, canonical deterministic serialization/hashing, reproducibility manifests, explicit historical output destinations, semantic/telemetry trace separation and append-only HUMAN_REAL guards.
- REGRESSION_TEST: Fixed payloads and semantic traces replay byte-identically; manifests bind commit/generator/input/output hashes; known mutating historical CLIs require explicit destinations; telemetry is separate; regenerable writers reject HUMAN_REAL mutation.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Closed without rewriting historical evidence, mutating HUMAN_REAL, acquisition, pricing threshold changes or promotion.

### TD-009 — Offer and price-expression identity is fragmented and incomplete

- DEBT_ID: `TD-009`
- TITLE: Offer and price-expression identity is fragmented and incomplete.
- CATEGORY: DOMAIN_MODEL, DATA_LINEAGE, ARCHITECTURAL_CONSISTENCY.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `offer-observation-identity-v1`.
- EVIDENCE: The official deterministic projection emits 9 offer snapshot rows: 5 targeted snapshots are `RESOLVED`, 4 historical snapshots are preserved as `UNRESOLVED`, and the 5 resolved rows have unique `snapshot_observation_id` values. `OfferObservation` composes logical offer, price expression, unit, period, bound, source observation, RAW snapshot and optional `EconomicEvidenceDimensionsV2`. Snapshot dimensions are materialized in `offer_observations_v1.jsonl`, loaded with typed status/claims/provenance, and filtered so RAW claims only survive when their `raw_document_id` matches the snapshot. Legacy projection rows without `economic_dimensions` remain loadable.
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
- IMPLEMENTED_FIX: Versioned `OfferObservation` and `PriceExpressionIdentity` provide stable logical offer, price-expression and snapshot identities without using economic dimensions as identity inputs. The projection artifact composes targeted and historical snapshots, preserves unresolved historical rows without strong identity, serializes snapshot-safe `EconomicEvidenceDimensionsV2`, includes `data/economic_dimensions_v2.jsonl` in the lifecycle manifest, and requires explicit output destinations.
- REGRESSION_TEST: Fifty-seven TD-009 contracts cover stable identity, multi-price separation, source/RAW conflict detection, snapshot preservation, artifact determinism, typed dimension serialization/loading, legacy loading without dimensions, lifecycle manifest inputs, real 9-snapshot invariants and RAW-claim snapshot compatibility.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Closed without acquisition, pricing threshold changes, historical artifact rewrites, fabricated logical identities, fabricated provenance or runtime consumer migration. TD-010 was closed by provider-independence-contract-v1.

### TD-010 — Runtime provider independence counts source ids instead of stable provider ids

- DEBT_ID: `TD-010`
- TITLE: Runtime provider independence counts source ids instead of stable provider ids.
- CATEGORY: CORRECTNESS, ARCHITECTURAL_CONSISTENCY, DATA_LINEAGE.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `provider-independence-contract-v1`.
- EVIDENCE: Runtime cohorts now count only stable provider ids from `EconomicEvidenceDimensionsV2.provider_identity` as `providers_n` and expose source cardinality separately as `source_count`. UNKNOWN, CONFLICTED or absent provider identity contributes zero provider independence. The real-data probe found no admitted runtime cohorts after lineage/reach/temporal gates, so no current RANGE_READY cohort changed.
- REPRODUCTION: Build runtime cohorts with same-provider/multi-source rows, distinct-provider rows, same-provider/multi-snapshot rows and UNKNOWN/CONFLICTED provider dimensions; compare `providers_n` with `source_count`.
- AFFECTED_FILES: `src/aplicacion/provider_independence.py`, `src/aplicacion/runtime_cohort_lineage_gate.py`, `src/aplicacion/pricing_cohort_loader.py`, `src/aplicacion/pricing_evidence_engine.py`, `src/aplicacion/technical_need_evidence_probe.py`, `src/api/main.py`, `scripts/build_pricing_statistics.py`, `data/local_pricing_stats_temporal_v1.csv`, `data/remote_pricing_stats_temporal_v1.csv`.
- AFFECTED_LAYERS: APPLICATION, DATA_ARTIFACTS, READINESS, API.
- ROOT_CAUSE: Runtime statistics predated stable provider identity and conflated source ids with provider independence.
- PRODUCT_IMPACT: Multi-page/provider acquisition can no longer inflate readiness by source cardinality alone.
- DATA_RISK: Provider/source/observation/temporal independence are now separate published axes for runtime cohorts.
- SAFETY_RISK: Lower; unknown or conflicted provider identity fails closed and does not fabricate independence.
- MAINTENANCE_COST: LOW after remediation.
- LIKELIHOOD: LOW after remediation.
- BLAST_RADIUS: Future cohort confidence/readiness, runtime loader contract, API/probe evidence payloads.
- DEPENDENCIES: TD-009.
- IMPLEMENTED_FIX: Added `provider-independence-contract-v1`, split `source_count` from `providers_n`, passed provider dimensions into runtime cohort building, made runtime loading require the provider-independence schema/version, propagated the new fields through pricing evidence/API/probe boundaries, and updated empty runtime temporal artifact headers without changing acquisition or thresholds.
- REGRESSION_TEST: Same provider across sources counts once; distinct providers count separately; same provider across snapshots counts once; UNKNOWN/CONFLICTED provider identity never creates independence; legacy runtime artifacts missing the provider-independence contract fail closed.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Frequency is not independence. Closed without acquisition, HUMAN_REAL mutation, pricing threshold changes, runtime evidence additions or frontend changes.

### TD-011 — Price-scope parsing remains duplicated between user and source paths

- DEBT_ID: `TD-011`
- TITLE: Price-scope parsing remains duplicated between user and source paths.
- CATEGORY: DUPLICATED_LOGIC, ARCHITECTURAL_CONSISTENCY, MAINTAINABILITY.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `price-scope-single-engine-v1`.
- EVIDENCE: Functional remediation is present and green: parser/extractor/context, adapter projection and single scope engine tests all pass against the current runtime. TD-006 already records TD-011 as resolved before final interpretation recovery.
- REPRODUCTION: Run `python -m pytest tests/test_td011_adapter_projection.py tests/test_td011_parser_extractor_context.py tests/test_td011_single_scope_engine.py -q`.
- AFFECTED_FILES: `src/dominio/price_scope_contract.py`, `src/aplicacion/pricing_dimensions.py`, `src/aplicacion/parser_consulta_pricing.py`, `scripts/build_pricing_statistics.py`, `src/infraestructura/economic_dimensions_v2_adapter.py`.
- AFFECTED_LAYERS: DOMAIN, APPLICATION, INFRASTRUCTURE.
- ROOT_CAUSE: Source cadence inference survived introduction of the typed user contract.
- PRODUCT_IMPACT: Equivalent phrases normalize through one scope contract instead of drifting by origin.
- DATA_RISK: UNKNOWN behavior remains fail-closed and no scope fact is fabricated.
- SAFETY_RISK: LOW after remediation.
- MAINTENANCE_COST: LOW after remediation.
- LIKELIHOOD: LOW after remediation.
- BLAST_RADIUS: User parsing, source dimensions, cohort keys and adapter projection.
- DEPENDENCIES: None.
- IMPLEMENTED_FIX: Price scope normalization is centralized in the typed scope contract with distinct origins and UNKNOWN fail-closed behavior preserved across parser, extractor context and adapter projection.
- REGRESSION_TEST: TD-011 adapter projection, parser/extractor context and single scope engine suites cover scope parity and fail-closed boundaries.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: This is formal registry alignment only; no runtime TD-011 code was reopened in this alignment commit.

### TD-012 — Acquisition boundaries collapse exceptions into counters without causal diagnostics

- DEBT_ID: `TD-012`
- TITLE: Acquisition boundaries collapse exceptions into counters without causal diagnostics.
- CATEGORY: OBSERVABILITY, OPERABILITY, EXCEPTION_HANDLING.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `acquisition-failure-diagnostics-v1`.
- EVIDENCE: Acquisition failures now preserve typed source/operation/category/retryability/exception diagnostics with credential-safe redaction. Raw and USASpending distinguish remote acquisition failures, rejected records and persistence failures; Argentina bulk distinguishes download, raw preparation, raw persistence, persisted-row inspection and extracted-row persistence while continuing across resources; CompraGamer no longer silently drops product JSON parse failures.
- REPRODUCTION: Inject transport, HTTP/auth, parse and persistence failures through `tests/test_acquisition_failure_contract.py`, `tests/test_raw_document_collector.py`, `tests/test_usaspending_collector.py`, `tests/test_argentina_bulk_ingestion.py` and `tests/scrapers/test_compragamer_scraper.py`.
- AFFECTED_FILES: `src/aplicacion/acquisition_failure.py`, `src/aplicacion/colector_documentos_raw.py`, `src/aplicacion/colector_argentina_bulk.py`, `src/aplicacion/colector_usaspending.py`, `src/infraestructura/ted/cliente_busqueda.py`, `src/infraestructura/usaspending/cliente_busqueda.py`, `src/infraestructura/scrapers/compragamer_playwright_scraper.py`.
- AFFECTED_LAYERS: APPLICATION, INFRASTRUCTURE, ACQUISITION.
- ROOT_CAUSE: Batch-continuation counters and scraper callbacks predated a shared typed causal failure contract; retry wrappers also discarded transport cause chaining.
- PRODUCT_IMPACT: Operators can now distinguish network, auth, HTTP, parse/decode and persistence failures instead of treating empty acquisition as unexplained absence.
- DATA_RISK: Reduced; failed acquisition remains distinguishable from absent market evidence.
- SAFETY_RISK: Low; failures remain fail-closed and do not fabricate evidence.
- MAINTENANCE_COST: LOW_POST_REMEDIATION.
- LIKELIHOOD: CONTROLLED_BY_TYPED_BOUNDARY_CONTRACT.
- BLAST_RADIUS: External acquisition flows now share one diagnostic contract without changing acquisition volume.
- DEPENDENCIES: None.
- IMPLEMENTED_FIX: Added immutable `AcquisitionFailure` diagnostics with typed categories, retryability, exception-chain classification and secret redaction; preserved rejected-record semantics separately; added explicit persistence boundary diagnostics and batch continuation; preserved underlying TED/USASpending transport causes with exception chaining; CompraGamer propagates intercepted JSON parse failure diagnostics instead of swallowing them.
- REGRESSION_TEST: Focused TD-012 suite passes 31/31 and injected failures cover redaction, HTTP/auth/network classification, exception chaining, persistence, batch continuation and CompraGamer callback parsing. Static audit reports `TD012_NO_SILENT_BROAD_EXCEPTIONS=PASS` and `TD012_COMPRAGAMER_TYPED_FAILURE=PASS`.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: `rejected_records`/rejected rows remain distinct from acquisition failures by design. This remediation does not expand acquisition, change pricing thresholds, promote knowledge or modify HUMAN_REAL.

### TD-013 — Green suites under-test real process and cross-stack boundaries

- DEBT_ID: `TD-013`
- TITLE: Green suites under-test real process and cross-stack boundaries.
- CATEGORY: TESTABILITY, REPRODUCIBILITY, DEVELOPER_EXPERIENCE.
- SEVERITY: `P2`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `real-boundary-test-matrix-v1`.
- EVIDENCE: Repository-wide direct CLI coverage now executes every argparse `__main__` surface as a real subprocess from repository root with `PYTHONPATH` removed; non-argparse entrypoints are explicitly classified and the safe `estado_repo.py` boundary is executed directly. This matrix reproduced a real Windows `cp1252` `UnicodeEncodeError` that the prior green suite did not detect and the CLI was made encoding-safe. `/decision/pricing` now has an explicit Pydantic response contract and FastAPI `response_model`, producing a concrete OpenAPI schema instead of `{}`. A deterministic frontend JSON Schema projection and parity tests bind the frontend boundary to that backend contract, while the TypeScript response surface includes the current nested API fields. Artifact lifecycle now exposes hash-based freshness verification for generator, inputs and output; the pre-existing `full_product_e2e_v1.json` is explicitly treated as historical evidence rather than current-HEAD proof.
- REPRODUCTION: `tests/test_td013_cli_boundary_matrix.py` executes the direct CLI boundary; `tests/test_td013_decision_api_contract.py`, `tests/test_td013_frontend_api_schema_parity.py` and `tests/test_td013_frontend_type_surface.py` protect API/frontend parity; `tests/test_td013_artifact_freshness.py`, `tests/test_full_product_e2e_artifact.py` and `tests/test_full_product_e2e.py` distinguish reproducible current-state checks from historical snapshots.
- AFFECTED_FILES: `scripts/estado_repo.py`, `scripts/export_decision_pricing_schema.py`, `src/api/decision_pricing_contract.py`, `src/api/main.py`, `frontend/src/features/decision/types.ts`, `frontend/src/features/decision/decision-pricing.schema.json`, `src/infraestructura/artifact_lifecycle.py`, `tests/test_td013_cli_boundary_matrix.py`, `tests/test_td013_decision_api_contract.py`, `tests/test_td013_frontend_api_schema_parity.py`, `tests/test_td013_frontend_type_surface.py`, `tests/test_td013_artifact_freshness.py`, `tests/test_full_product_e2e_artifact.py`, `tests/test_full_product_e2e.py`.
- AFFECTED_LAYERS: TESTS, API_FRONTEND, SCRIPTS_OPERABILITY, ARTIFACT_LIFECYCLE.
- ROOT_CAUSE: Helper/import-level and manually duplicated contract tests grew faster than true executable-process, HTTP-schema and artifact-freshness boundaries, allowing a fully green suite to coexist with broken direct execution, cross-stack schema drift or stale historical artifacts.
- PRODUCT_IMPACT: Resolved. A green suite now exercises the operator-facing CLI boundary, binds the public pricing response to a formal backend schema and frontend parity contract, and distinguishes historical E2E evidence from current executable product behavior.
- DATA_RISK: Reduced. Historical artifacts cannot silently satisfy currentness semantics, and modified/missing generator, input or output files fail freshness verification.
- SAFETY_RISK: Reduced; boundary failures are fail-closed and no pricing threshold, evidence admission, promotion policy or economic truth was changed.
- MAINTENANCE_COST: Reduced by repository-discovered CLI coverage, one backend schema authority and reusable artifact-freshness verification.
- LIKELIHOOD: LOW after remediation; new argparse entrypoints enter the process matrix automatically and unclassified non-argparse entrypoints fail the classification contract.
- BLAST_RADIUS: CLI operability, `/decision/pricing`, frontend decision types/schema and deterministic artifact verification.
- DEPENDENCIES: TD-005 and TD-008, both resolved before this remediation.
- IMPLEMENTED_FIX: Added a real subprocess CLI matrix with `PYTHONPATH` removed and explicit side-effectful entrypoint classification; fixed the Windows console boundary exposed by that matrix; introduced strict Pydantic pricing-response models and FastAPI `response_model`; exported a deterministic backend-derived JSON Schema to the frontend and protected exact schema/type parity; added reusable generator/input/output hash freshness verification; and classified the legacy full-product E2E JSON as a historical snapshot with valid Git provenance rather than a current manifest.
- REGRESSION_TEST: TD-013 integrated focused suite passed `82/82`; final backend suite passed `1137/1137`; frontend TypeScript check passed, Vitest passed `10/10`, and Next.js production build completed successfully. Artifact lifecycle compatibility remained green with existing TD-008 contracts.
- ESTIMATED_SCOPE: L.
- BLOCKS_MARKET_ACQUISITION: false for TD-013 after remediation; remaining technical debt still controls the program-level acquisition gate.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false for TD-013 after remediation; promotion remains governed by the remaining program constraints.
- NOTES: No acquisition volume was expanded, no pricing/readiness threshold changed, no knowledge was promoted, no HUMAN_REAL evidence was modified, and no historical artifact was rewritten or falsely rebound to the current HEAD. `ArtifactManifest.commit_sha` remains provenance; currentness is verified through reproducible generator/input/output identity rather than a circular same-commit SHA requirement.

### TD-014 — README and architecture baseline materially diverge from runtime

- DEBT_ID: `TD-014`
- TITLE: README and architecture baseline materially diverge from current runtime.
- CATEGORY: DOCUMENTATION, ARCHITECTURAL_CONSISTENCY, DEVELOPER_EXPERIENCE.
- SEVERITY: `P3`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `current-state-documentation-v1`.
- EVIDENCE: README no longer encodes a fixed HEAD or hand-maintained backend/frontend test counts as current state. It now points to `docs/ENKI_ARCHIVO_RECTOR.md` as governance authority, preserves the executive sequence ENTENDER -> CONECTAR -> APRENDER -> EXPLOTAR ECONOMICAMENTE and gives commands that verify the actual checkout. ARCHITECTURE no longer claims README is the highest strategic source, now declares Rector precedence, documents the live `POST /decision/pricing` boundary and `DecisionPricingResponse`, and no longer lists the pricing engine as future/unimplemented.
- REPRODUCTION: `tests/test_td014_current_state_documentation.py` asserts verifiable current-state commands, Rector precedence, the current decision runtime and removal of volatile/stale baselines. A focused stale-document audit confirms the old HEAD/test-count and obsolete architecture claims are absent from README/ARCHITECTURE.
- AFFECTED_FILES: `README.md`, `ARCHITECTURE.md`, `docs/TECHNICAL_DEBT_REGISTER.md`, `tests/test_td014_current_state_documentation.py`.
- AFFECTED_LAYERS: DOCUMENTATION, REPOSITORY.
- ROOT_CAUSE: Causal sprint narratives accumulated without a maintained current-state index, so volatile prose and historical architecture statements outlived the runtime they described.
- PRODUCT_IMPACT: Resolved. Operators and contributors now verify repository state from commands and follow the Rector for governance instead of stale prose.
- DATA_RISK: LOW.
- SAFETY_RISK: LOW.
- MAINTENANCE_COST: Reduced by removing manually maintained SHA/test-count baselines and clarifying document authority.
- LIKELIHOOD: LOW after remediation; the regression contract rejects the known stale baseline classes.
- BLAST_RADIUS: Onboarding, planning and architectural orientation.
- DEPENDENCIES: None.
- IMPLEMENTED_FIX: Declared `docs/ENKI_ARCHIVO_RECTOR.md` as governance authority; replaced volatile README baselines with executable verification commands; aligned README with the current program sequence; documented the real decision API/runtime in ARCHITECTURE; and removed obsolete future-pricing claims.
- REGRESSION_TEST: `tests/test_td014_current_state_documentation.py` passed `4/4`; the focused stale-document audit passed all checks.
- ESTIMATED_SCOPE: S.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Documentation-only remediation. No runtime behavior, evidence, thresholds, HUMAN_REAL data, acquisition volume or promotion state changed.

### TD-015 — Dependency and test configuration carry duplicated and deprecated surfaces

- DEBT_ID: `TD-015`
- TITLE: Dependency and test configuration carry duplicated and deprecated surfaces.
- CATEGORY: DEPENDENCIES, DEPRECATIONS, DEVELOPER_EXPERIENCE, CONFIGURATION.
- SEVERITY: `P3`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `dependency-config-consolidation-v1`.
- EVIDENCE: `pyproject.toml` is now the only pytest authority and exposes explicit build/project metadata. The dead hidden pytest coverage options were removed instead of activated without `pytest-cov`. Frontend Vitest no longer emits the Vite CJS Node API deprecation after declaring the frontend package as ESM. `httpx2` was retained because `starlette.testclient` imports it in this environment; `pip check` remains green.
- REPRODUCTION: Run `python -m pytest tests/test_td015_dependency_configuration.py -q`, `python -m pytest -q`, `corepack pnpm test -- --run`, `corepack pnpm lint`, `corepack pnpm build`, dependency metadata probes for FastAPI/Starlette/httpx/httpx2 and `python -m pip check`.
- AFFECTED_FILES: `pyproject.toml`, `pytest.ini`, `frontend/package.json`, `tests/test_td015_dependency_configuration.py`.
- AFFECTED_LAYERS: CONFIGURATION, TESTS, FRONTEND, PACKAGING.
- ROOT_CAUSE: Incremental environment snapshots left a hidden pytest authority, implicit package metadata and a frontend CJS module boundary.
- PRODUCT_IMPACT: Test configuration is explicit, package metadata exists, and the verified frontend deprecation warning no longer masks future incompatibility.
- DATA_RISK: NONE.
- SAFETY_RISK: LOW.
- MAINTENANCE_COST: LOW after remediation.
- LIKELIHOOD: LOW after remediation.
- BLAST_RADIUS: Setup, tests and upgrades.
- DEPENDENCIES: TD-005.
- IMPLEMENTED_FIX: Removed `pytest.ini`, kept effective pytest behavior in `pyproject.toml` with `addopts = "-v"`, added `[build-system]` and `[project]` metadata, removed inactive coverage configuration, declared `frontend/package.json` as ESM, and preserved `requirements.txt` because the suspected `httpx2` removal was refuted by runtime metadata/import probes.
- REGRESSION_TEST: TD-015 configuration test asserts one pytest authority, explicit backend metadata, absence of inactive coverage config and frontend ESM declaration. Full backend suite, frontend lint/test/build and `pip check` are green.
- ESTIMATED_SCOPE: M.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Closed without dependency upgrades, lockfile churn, acquisition, HUMAN_REAL mutation, pricing threshold changes, knowledge promotion or frontend product behavior changes.

### TD-016 — Legacy compatibility modules and unused fixture adapters obscure canonical ownership

- DEBT_ID: `TD-016`
- TITLE: Legacy compatibility modules and unused fixture adapters obscure canonical ownership.
- CATEGORY: MAINTAINABILITY, DEAD_CODE, PARALLEL_SOURCES_OF_TRUTH.
- SEVERITY: `P3`.
- CONFIDENCE: HIGH.
- STATUS: RESOLVED by `legacy-surface-retirement-v1`.
- EVIDENCE: Runtime and scripts already used the canonical `src.infraestructura.scrapers` namespace. Remaining `src.scrapers` consumers were tests, so they were migrated to the canonical namespace before deleting the legacy wrappers. Frontend `interpret-quote.ts` had no live consumer and was removed; `support-quote.ts` is still consumed by review page/flow as explicit demo input and was preserved.
- REPRODUCTION: Run `python -m pytest tests/test_td016_legacy_surface_retirement.py -q`, search for `src.scrapers`, `interpretQuoteForReview` and `createDecisionReadout`, and run affected scraper/pipeline plus frontend lint/test/build suites.
- AFFECTED_FILES: `src/scrapers/`, `tests/`, `frontend/src/features/decision/interpret-quote.ts`, `frontend/src/features/decision/fixtures/support-quote.ts`, `docs/TECHNICAL_DEBT_REGISTER.md`.
- AFFECTED_LAYERS: INFRASTRUCTURE, TESTS, FRONTEND.
- ROOT_CAUSE: Brownfield compatibility lacked a retirement ledger; prototype adapters remained after API integration.
- PRODUCT_IMPACT: Developers now have one scraper namespace to extend, and the frontend no longer carries an unused fixture adapter that can be mistaken for product logic.
- DATA_RISK: NONE.
- SAFETY_RISK: LOW.
- MAINTENANCE_COST: LOW after remediation.
- LIKELIHOOD: LOW after remediation.
- BLAST_RADIUS: Scraper maintenance and frontend review flow defaults.
- DEPENDENCIES: TD-013.
- IMPLEMENTED_FIX: Migrated tests from `src.scrapers` to `src.infraestructura.scrapers`, removed the legacy wrapper package, removed the dead frontend interpretation adapter, preserved the live support quote fixture, and added a TD-016 contract test that prevents reintroducing those legacy surfaces.
- REGRESSION_TEST: TD-016 retirement contract, architecture checks, affected scraper/pipeline tests, frontend lint/test/build and full backend suite.
- ESTIMATED_SCOPE: S.
- BLOCKS_MARKET_ACQUISITION: false.
- BLOCKS_FIELD_TESTING: false.
- BLOCKS_PROMOTION: false.
- NOTES: Closed without changing scraper behavior, acquisition, HUMAN_REAL, pricing thresholds, evidence admission, knowledge promotion or frontend API/schema contracts.

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

TECHNICAL_DEBT_PROGRAM=CLOSED. TD-001 through TD-016 are resolved. Promotion remains disabled by candidate-validation constraints, not by unresolved technical-debt gates.

## Remediation waves

### WAVE 0 — P0 correctness and safety

1. **RUNTIME COHORT LINEAGE GATE v1 — COMPLETE** — Every contributor is auditable or fails closed. Closed TD-001.
2. **OFFER SERVICE REACH ADMISSION GATE v1 — COMPLETE** — Provider location and remote capability cannot stand in for explicit offer reach. Closed TD-002.
3. **TEMPORAL EVIDENCE ADMISSIBILITY v1 — COMPLETE** — Every current-pricing contributor requires explicit temporal identity and compatible freshness policy. Closed TD-003.
4. **COMMERCIAL CONTEXT SINGLE TRUTH v1 — COMPLETE** — One typed user/source identity with raw basis and exact parser/runtime/trace parity. Closed TD-004.

### WAVE 1 — P1 operability and reproducibility

1. **CLI EXECUTION CONTRACT v1** — TD-005; risk medium; all 45 surfaces explicitly classified and intended CLIs subprocess-green without PYTHONPATH.
2. **ARTIFACT RUN MANIFEST v1 - COMPLETE** - TD-008; deterministic outputs have commit/input/output hashes, telemetry is separated, historical writes are explicit, and HUMAN_REAL remains append-only.
3. **QUERY GATE PRECEDENCE v1** — TD-007; risk medium; six known cases become safe unsupported without valid-clarification drift.
4. **REAL QUERY CAUSAL RECOVERY v1-v3 — COMPLETED** — TD-006; dependencies gate precedence and scope engine resolved first; three causal remediation blocks completed with final official runtime replay at `0 WRONG_INTERPRETATION` and `0 UNSAFE_DECISION`.

### WAVE 2 — Provenance and data model

1. **OFFER OBSERVATION IDENTITY v1 — COMPLETE** — TD-009; stable multi-price/snapshot identity with backwards-compatible loading.
2. **PROVIDER INDEPENDENCE CONTRACT v1 — COMPLETE** — TD-010; stable provider ids feed `providers_n`, source cardinality is exposed separately, and UNKNOWN/CONFLICTED provider identity fails closed.
3. **PRICE SCOPE SINGLE ENGINE v1 - COMPLETE** - TD-011; one semantic engine with distinct origins and UNKNOWN fail-closed, formally aligned in the register.

### WAVE 3 — Architecture and test consolidation

1. **ACQUISITION FAILURE TAXONOMY v1 - COMPLETE** - TD-012; typed/redacted causal failures preserve source, operation, retryability and failure category without collapsing rejected records or breaking batch continuation.
2. **REAL BOUNDARY TEST MATRIX v1 - COMPLETE** - TD-013; real subprocess execution, formal API/frontend schema parity and hash-based artifact freshness now fail closed while historical E2E evidence remains explicitly historical.

### WAVE 4 — Deprecations and maintenance

1. **CURRENT STATE DOCUMENTATION v1 - COMPLETE** - TD-014; Rector precedence, verifiable current-state commands and the live decision runtime are now documented without volatile baselines.
2. **DEPENDENCY CONFIG CONSOLIDATION v1 - COMPLETE** - TD-015; pyproject is the single pytest authority, backend metadata is explicit, `httpx2` ownership is documented, and the frontend Vite CJS warning is gone.
3. **LEGACY SURFACE RETIREMENT v1 - COMPLETE** - TD-016; one canonical scraper namespace remains and the unused frontend fixture adapter is retired.

Estimated consolidation: **18 small causal sprints** (the broad interpretation item is explicitly split into three). No wave is authorized by this document.

## Gates

### SAFE_FOR_FOUNDER_FIELD_TESTING

`YES_SUPERVISED`. Continue append-only HUMAN_REAL capture and supervised parser/clarification observation. The active runtime has zero admitted evidence, so there are no economic ranges to rely on. Keep promotion and runtime learning writes disabled.

### SAFE_FOR_MARKET_ACQUISITION_EXPANSION

`NO`. TD-008 is closed; market acquisition remains disabled by the current program sequence rather than an unresolved TD-008 gate.

### SAFE_FOR_KNOWLEDGE_PROMOTION

`NO`. TD-011 and TD-013 are resolved; promotion remains disabled because the current candidate remains `FAIL_SHADOW_VALIDATION`. Existing currency conflicts remain preserved and no promotion is authorized.

## Exact next remediation sprint

**END-TO-END UNDERSTANDING MODEL v1**. Start phase 2: complete the real-input understanding model end to end before any economic acquisition, pricing expansion or knowledge promotion.


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

## Historical audit validation baseline

- Backend full suite: `844 passed, 0 failed, 1 warning in 35.53s` (`37.271s` wall clock). The warning is the recorded Starlette/httpx deprecation.
- Compile: `python -m compileall src scripts` passed in `0.35s`.
- Frontend: lint passed; `10/10` tests passed; production build passed. Vite emitted the recorded CJS API deprecation.
- Dependencies: `pip check` reported no broken requirements.
- Audit artifact: valid JSON, 16/16 items contain every required field, and its SHA-256 was unchanged across the full suite.
- Product/evidence mutation: none; `data/field/` was not modified.
