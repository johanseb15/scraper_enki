# Live Evidence Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Founder gate:** this plan does not authorize implementation or git staging/commit/push; obtain separate approval first.

**Goal:** A real pricing query reuses admitted current evidence or triggers a directed local refresh, then decides only from a complete published cohort with RAW provenance.

**Architecture:** Keep the existing parser, collector, SQLite RAW, live bridges, admission gates, cohort builder and pricing engine. Add canonical requirement identity, versioned 24-hour service-price freshness, distinct acquisition events, isolated runs, atomic snapshot publication, and a single-process evaluation coordinator exposed by new polling endpoints. Current `/decision/pricing` remains unchanged.

**Tech Stack:** Python 3.14, FastAPI/Pydantic, SQLite, local filesystem snapshots, pytest; Next.js/React/TypeScript, Vitest, pnpm.

**Spec:** `docs/superpowers/specs/2026-09-28-live-evidence-refresh-design.md`, as approved with the founder's 2026-09-28 freshness/stale/first-slice decisions in this plan.

## Global Constraints

- Policy `service-price-freshness-v1`: maximum 24 hours from a **new acquisition event**, subject to source-declared validity and explicit historical date/period. At exactly 24 hours it remains within the maximum; after 24 hours it requires refresh. `acquired_at` is an operational reuse bound, not a guarantee of economic validity.
- Precedence: expired `source_valid_until` → STALE; explicit historical source date/period → STALE; otherwise a successful live acquisition with no contradicting source date can be `CURRENT_REPRODUCIBLE` for less than 24 hours. Preserve raw period text, explicit `source_valid_from`/`source_valid_until`, policy version, decision and reason separately. Do not turn a scheduled update into `valid_until` or invent month boundaries.
- Stale may be labeled `HISTORICAL_CONTEXT` only. It cannot join a current cohort, satisfy a current requirement, produce a current decision or silently replace a failed refresh.
- Keep all current lineage, explicit service reach, temporal, commercial, parts-scope and provider-independence gates; RAW first; REAL ≠ SYNTHETIC; UNKNOWN ≠ guessed; REMOTE ≠ NATIONAL. Never use provider address, registry metadata or filesystem timestamps as admitted reach/time.
- First slice is the hypothesis `VISITA_TECNICA_DOMICILIO / Buenos Aires / PER_HOUR / URGENCY`; existing minimums are 5 observations, 3 independent providers and spread ratio ≤ 2.5. Qualify real sources before committing to this target; pivot the slice if they cannot meet the contract, without changing thresholds or meaning.
- Runs use isolated paths under `data/live/<run_id>/`; no run overwrites `data/local_pricing_stats_temporal_v1.csv`, `data/remote_pricing_stats_temporal_v1.csv` or historical RAW. Complete manifest precedes atomic catalog pointer update. One API process with local single-flight jobs; no scheduler, distributed queue, new database, LLM or open crawler.
- Regular tests are offline using fixtures/fake HTTP and injected UTC clock. Real public-source verification is a separately marked step. Never use paid/quota APIs or secrets without separate authorization.
- Use RED → causal RED → minimal GREEN → related regressions for every task. After future implementation approval, use systematic-debugging for unexpected behavior, verification-before-completion before a success claim, and requesting-code-review at the end. **No git add/commit/push in this plan or its execution unless separately authorized.**

## Brownfield file map and sequence

`src/aplicacion/enki_pricing_query_service.py` already accepts `parsed_query`; `src/aplicacion/pricing_evidence_engine.py` owns `CohortePricing`/`evaluar_precio`; `src/aplicacion/pricing_cohort_loader.py` reads precomputed runtime CSVs. `src/aplicacion/colector_precios_batch.py` and `src/infraestructura/sqlite/repositorio_sqlite_evidencia.py` preserve RAW but deduplicate by source/record/hash, so they need a separate acquisition event. `src/aplicacion/pricing_live_pipeline.py`, `src/infraestructura/live_offer_evidence_bridge.py`, `src/infraestructura/live_temporal_evidence_bridge.py`, `src/infraestructura/economic_dimensions_v2_adapter.py`, and `scripts/build_pricing_statistics.py` already connect extraction to gated cohort building. `src/api/main.py` has only synchronous `POST /decision/pricing`; `frontend/src/features/decision/decision-api.ts` and `components/DecisionReviewFlow.tsx` call it once.

The intended dependency path is Tasks 1–3 → 4–6 → 7–9 → 10–12. Task 5 source safety and source qualification precede Task 6 reach fixture work; Task 13 checks the whole real-source slice. If the initial target fails qualification, switch the target of Tasks 6/13 before adding target-specific extraction. This is not permission to weaken semantics.

## Review Focus

These inputs from the approved design could otherwise fail without an obvious test; their owning tasks below pin them down:

1. Same bytes fetched again after the prior event aged out: Task 3 proves a new event/time while the RAW hash remains unchanged, and Task 2 rejects source-declared historical validity.
2. Source URL redirects to a private/loopback address or returns oversized/non-HTML content: Task 5 rejects before storing RAW.
3. Two prices under one page heading with ambiguous coverage: Task 6 keeps reach UNKNOWN rather than fanning out a page claim.
4. An older run completes after a newer one: Task 8 proves catalog generation compare-and-swap prevents regression.
5. An evaluation polled after its once-current snapshot expires: Task 10/11 rechecks freshness and never returns the old decision as current.

---

### Task 1: Canonical EvidenceRequirement from one parsed query

**Files:** Create `src/dominio/evidence_requirement.py` and `src/aplicacion/pricing_query_projection.py`; modify `src/aplicacion/enki_pricing_query_service.py` only to expose/reuse its existing route/price-scope resolution, and `src/api/main.py` only to reuse the extracted existing parsed-response projection; test `tests/test_evidence_requirement.py` and regress `tests/test_enki_pricing_query_service.py`/`tests/test_decision_pricing_api.py`.

**Interfaces:** `EvidenceRequirement` is an immutable dataclass with schema version, canonical service, market scope/market, required reach, modality, price scope, commercial context, parts scope only for `PARTS_SCOPE_SENSITIVE_SERVICES`, ARS currency and service-relevant scope qualifiers. `derive_evidence_requirement(parsed: ParsedPricingQuery) -> EvidenceRequirement | None`; `EvidenceRequirement.cache_key() -> str` hashes canonical sorted JSON. `project_parsed_query(parsed: ParsedPricingQuery) -> dict[str, object]` moves the existing `parsed` projection from `_serialize_decision_result` without changing fields. `None` requirement means the existing query service has a terminal clarification/unsupported route, not a guessed requirement. The coordinator later passes the original `ParsedPricingQuery` to `resolver_consulta_pricing(..., parsed_query=parsed)`.

- [ ] RED: `test_equivalent_quotes_share_requirement_key` asserts changed wording/price does not change key; `test_incompatible_parts_or_context_do_not_share_key` asserts sensitive parts, urgency, market, reach, modality and unit changes do; `test_unknown_does_not_match_known` and `test_requirement_route_matches_existing_service` cover fail-closed/route parity. Run `./.venv/Scripts/python.exe -m pytest tests/test_evidence_requirement.py -q`; expect missing interface/failing assertions.
- [ ] GREEN: implement the typed projection from the parsed object and reuse `_explicit_price_scope`/market resolution logic through a small shared helper if needed; do not invoke `parse_pricing_query` again. Run the same command; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_enki_pricing_query_service.py tests/test_pricing_evidence_engine.py tests/test_decision_pricing_api.py -q`; pass and prove terminal unsupported/clarification yields no refreshable key or API shape change.

### Task 2: Service-price freshness v1 and temporal admission

**Files:** Create `src/dominio/service_price_freshness.py`; modify `src/dominio/temporal_evidence.py`, `src/infraestructura/live_temporal_evidence_bridge.py`, `src/aplicacion/temporal_evidence_admission_gate.py`; test `tests/test_service_price_freshness.py`, `tests/test_live_temporal_evidence_bridge.py`, `tests/test_temporal_evidence_admissibility.py`.

**Interfaces:** `SERVICE_PRICE_FRESHNESS_VERSION = "service-price-freshness-v1"`; `evaluate_service_price_freshness(evidence: TemporalEvidence, *, now: datetime) -> FreshnessDecision`, with `state`, `reason`, policy version, event acquisition time, source-validity fields and evaluated-at. Add optional `source_valid_from`, `source_valid_until`, `freshness_decision`, `freshness_reason` to `TemporalEvidence` without breaking historical constructors; existing `valid_from`/`valid_to` are mapped only when source evidence supports exact bounds. Bridge accepts optional per-observation acquisition-event timestamps and `now`; absent live event retains historical behavior. Feed admitted `CURRENT_REPRODUCIBLE` plus known policy to the existing gate, not a bypass.

- [ ] RED: `test_recent_undated_live_event_is_current_through_24h`, `test_after_24h_requires_refresh`, `test_expired_source_valid_until_wins_over_today_fetch`, `test_explicit_historical_month_is_stale`, `test_explicit_current_period_is_compatible`, `test_source_validity_does_not_extend_ttl`, and `test_ambiguous_or_conflicting_period_fails_closed` assert state, version and reason. Run `./.venv/Scripts/python.exe -m pytest tests/test_service_price_freshness.py -q`; expect missing policy/failures.
- [ ] GREEN: apply source expiry/date/period before TTL, parse only source-supported granularity, use aware UTC clock, and preserve the raw period. A period explicitly before acquisition/current period is historical; an ambiguous period remains unknown. Run focal test; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_live_temporal_evidence_bridge.py tests/test_temporal_evidence_admissibility.py -q`; historical replay stays historical, no filesystem time, acquisition event alone cannot override contradictory RAW.

### Task 3: Distinct acquisition events and isolated run journal

**Files:** Create `src/dominio/acquisition_event.py` and `src/infraestructura/pricing_refresh_store.py`; modify `src/infraestructura/sqlite/repositorio_sqlite_evidencia.py`, `src/aplicacion/colector_precios_batch.py`, `src/aplicacion/pricing_live_pipeline.py`; test `tests/test_live_acquisition_events.py` and `tests/test_pricing_refresh_store.py`.

**Interfaces:** Define immutable `AcquisitionEvent` in the new domain file; add SQLite `acquisition_events(event_id, run_id, source_id, requested_url, final_url, acquired_at_utc, raw_document_id, content_hash, collector_version, outcome)` with append-only inserts. `RepositorioSQLiteEvidencia.record_acquisition_event(event: AcquisitionEvent) -> None` and `.events_for_run(run_id: str) -> tuple[AcquisitionEvent, ...]`. Extend `colectar_fuentes_pricing(..., run_id: str | None = None, event_sink: AcquisitionEventSink | None = None)` compatibly; `AcquisitionEventSink.record_acquisition_event(event: AcquisitionEvent) -> None`. Emit after each successful fetch even when RAW deduplicates. `PricingRefreshStore(root: Path)` writes/reads atomic per-run manifests with requirement key, timestamps, collectors/URLs, observation/gate/exclusion counts, candidate/published IDs and final state. Never rewrite the original RAW `retrieved_at`.

- [ ] RED: `test_identical_bytes_create_two_events_one_raw`, `test_event_url_hash_and_utc_reproduce`, `test_failed_run_keeps_auditable_manifest`, `test_interrupted_manifest_is_not_complete`. Run `./.venv/Scripts/python.exe -m pytest tests/test_live_acquisition_events.py tests/test_pricing_refresh_store.py -q`; expect missing table/store or second event absent.
- [ ] GREEN: migrate/create the event table in the existing SQLite repository and journal files under a fresh run directory; keep old collector call sites valid. Link live temporal input to *event* time, not reused RAW time. Run focal command; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_generic_pricing_batch.py tests/test_live_sqlite_raw_lineage.py -q`; old RAW dedup/hash lineage remains valid and no historical data is rewritten.

### Task 4: Evaluation/refresh state and durable identity

**Files:** Create `src/dominio/evidence_evaluation.py`; extend `src/infraestructura/pricing_refresh_store.py`; test `tests/test_evidence_evaluation_state.py`.

**Interfaces:** `EvidenceEvaluation` stores evaluation ID, original raw query and serialized interpretation, requirement key, optional client idempotency key, evidence state, optional run ID, outcome/decision reference and timestamps. The typed `ParsedPricingQuery` lives with an active in-process evaluation; after restart unfinished evaluations fail closed and require a fresh POST, while stored terminal responses may be served only after cache freshness recheck. No silent reparsing during GET. `RefreshJob` stores run ID, requirement key and persisted state. `PricingRefreshStore.create_or_get_evaluation(query: str, idempotency_key: str | None, interpretation: dict[str, object], requirement_key: str | None) -> EvidenceEvaluation`, `.find_active_job(requirement_key: str) -> RefreshJob | None`, `.save_job(job: RefreshJob) -> None`, `.get_evaluation(evaluation_id: str) -> EvidenceEvaluation | None`; identical idempotency key+payload returns one evaluation, differing payload raises `IdempotencyConflict`. State set is exactly the spec's seven evidence states; internal run phases are separate.

- [ ] RED: `test_same_key_and_payload_is_idempotent`, `test_key_conflict_rejected`, `test_equivalent_quotes_have_distinct_evaluations_but_one_job`, `test_restart_marks_incomplete_job_failed_without_decision`. Run `./.venv/Scripts/python.exe -m pytest tests/test_evidence_evaluation_state.py -q`; expect missing model/store.
- [ ] GREEN: persist small atomic journal records in the existing run root; make state transitions explicit and recover unfinished jobs on startup. Run focal command; expect PASS.
- [ ] Regression/DONE: test invalid transition (e.g. FAILED → DECISION_READY) is rejected; no parsed query is reconstructed by silently reparsing after restart.

### Task 5: Directed, bounded public-source acquisition

**Files:** Create `data/pricing_refresh_sources_v1.csv` and `src/aplicacion/pricing_refresh_sources.py`; modify `src/aplicacion/pricing_source_registry.py`, `src/infraestructura/downloader.py`, `scripts/run_pricing_live_pipeline.py` only to share a safe downloader/config if compatible; test `tests/test_pricing_refresh_sources.py`, `tests/test_pricing_safe_downloader.py`.

**Interfaces:** `select_refresh_sources(requirement: EvidenceRequirement, catalog_path: Path) -> tuple[FuentePricing,...]` returns only explicit matching known-source entries and rejects unsupported target dimensions. `download_public_html(url: str, *, allowed_hosts: frozenset[str], timeout_seconds: int, max_bytes: int, session: requests.Session) -> str` validates HTTP(S), host/IP on each redirect, content type, byte limit and response status; its injected session keeps ordinary tests offline. Catalog is targeting metadata, never a source claim. Preserve existing `descargar_html` callers unless migrating them is required by security.

- [ ] RED: `test_no_catalog_match_returns_empty`, `test_incompatible_market_context_not_selected`, `test_redirect_to_private_ip_rejected`, `test_oversize_or_wrong_content_type_rejected`, `test_public_html_download_succeeds_with_fake_session`. Run `./.venv/Scripts/python.exe -m pytest tests/test_pricing_refresh_sources.py tests/test_pricing_safe_downloader.py -q`; expect missing selector/downloader.
- [ ] GREEN: add a narrow versioned catalog and downloader limits; use source registry provider fields only as hints, keep actual reach/price proof in RAW. Run focal command; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_pricing_source_registry.py tests/test_generic_pricing_collector.py -q`; existing CLI behavior remains compatible and no live request occurs. Before Task 6, separately qualify current public sources for the first-target service, price unit, urgency, explicit reach, dates and independent providers; if the facts cannot support 5/3/≤2.5, record the blocker and pivot the slice without altering gates. This live check is never part of ordinary pytest and needs network authorization at execution time.

### Task 6: First-slice offer-level reach and semantic qualification

**Files:** Modify `src/infraestructura/live_offer_evidence_bridge.py` and `src/infraestructura/offer_evidence_extractor.py` only for a demonstrated source-backed gap; possibly `src/aplicacion/semantic_normalization_live.py` for a demonstrated service mapping; test `tests/test_live_refresh_reach.py` and existing `tests/test_offer_service_reach_admission_gate.py`.

**Interfaces:** Reuse `build_live_offer_evidence(repository=...) -> dict[str, OfferReachChargedScopeEvidence]` and `derive_economic_dimensions_v2(...)`. Any new extractor rule must name the exact RAW phrase/container and observation anchor. The existing `evaluate_service_reach` remains the authority. If current public sources do not support offer-level reach/price/unit/context, record `SOURCE_GAP` and qualify another target, not a synthetic rule.

- [ ] RED: fixture from a qualified public page: `test_offer_bounded_home_service_reach_is_observed` asserts exact offer-linked `NAMED_AREA`/province claim; `test_provider_address_does_not_become_reach` and `test_ambiguous_page_heading_does_not_fan_out` assert UNKNOWN/exclusion. Run `./.venv/Scripts/python.exe -m pytest tests/test_live_refresh_reach.py -q`; expect the specific missing claim, **not** a changed gate.
- [ ] GREEN: add only the bounded source-backed extraction/normalization needed by the chosen slice; preserve claim basis, RAW hash and extractor version. Run focal command; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_offer_service_reach_admission_gate.py tests/test_live_offer_evidence_bridge.py tests/test_live_page_scope_evidence.py -q`; provider location and remote capability still cannot prove reach.

### Task 7: Compatible candidate cohort from admitted live observations

**Files:** Create `src/aplicacion/pricing_snapshot_builder.py`; modify `src/aplicacion/runtime_cohort_lineage_gate.py` or `scripts/build_pricing_statistics.py` only if the existing grouping cannot preserve a required dimension; test `tests/test_live_candidate_snapshot.py` and regress `tests/test_runtime_cohort_lineage_gate.py`.

**Interfaces:** `build_candidate_snapshot(requirement: EvidenceRequirement, *, rows: Sequence[Mapping[str, str]], offer_evidence: Mapping[str, OfferReachChargedScopeEvidence], dimensions: Mapping[str, EconomicEvidenceDimensionsV2], temporal_evidence: Mapping[str, TemporalEvidence], raw_repository: RawDocumentRepository, out_dir: Path) -> CandidateSnapshot` filters by exact requirement dimensions and invokes `build_runtime_pricing_statistics_from_objects(...)` with all gate inputs. `CandidateSnapshot` exposes path/hash, requirement key, cohorts, member observation IDs, gate decisions/exclusions and provider IDs. Do not merge `PARTS_INCLUDED` with `LABOR_ONLY`, UNKNOWN with known scope, different units or contexts. Retain existing 5/3/spread thresholds.

- [ ] RED: `test_incompatible_parts_context_unit_excluded_before_aggregation`, `test_missing_reach_or_stale_excluded`, `test_five_observations_three_providers_with_valid_spread_can_be_ready`, `test_duplicate_provider_does_not_inflate_count`. Run `./.venv/Scripts/python.exe -m pytest tests/test_live_candidate_snapshot.py -q`; expect missing builder or wrong membership.
- [ ] GREEN: wrap existing rigorous builder and `CohortePricing` loader, projecting only already admitted comparable members. Persist candidate inside run directory, outside active catalog. Run focal command; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_runtime_cohort_lineage_gate.py tests/test_live_runtime_pricing_statistics.py tests/test_pricing_evidence_engine.py -q`; U-009 parts and provider gates remain fail closed.

### Task 8: Complete-only atomic publication and current cache lookup

**Files:** Extend `src/infraestructura/pricing_refresh_store.py`; modify `src/aplicacion/pricing_cohort_loader.py` only to add a complete-snapshot loader alongside the existing env/CSV loader; test `tests/test_pricing_snapshot_publication.py`.

**Interfaces:** `PricingRefreshStore.publish_candidate(run_id: str, candidate: CandidateSnapshot, *, expected_generation: int) -> PublishedSnapshot` validates RAW links/hash, gate versions, policy version, member compatibility and readiness, writes/finalizes `COMPLETE` manifest, then atomically replaces a per-requirement catalog pointer on the same volume. `.load_current_snapshot(requirement: EvidenceRequirement, *, now: datetime) -> PublishedSnapshot | None` reads only a catalog pointer to a `COMPLETE` manifest, validates hash and each member's freshness under current policy, then calls existing `cargar_cohortes_pricing(... require_*_gate=True)`. Existing `cargar_cohortes_pricing_runtime()` stays unchanged for `/decision/pricing`.

- [ ] RED: `test_partial_run_never_published`, `test_restart_ignores_incomplete_manifest`, `test_complete_snapshot_publish_is_atomic`, `test_old_run_cannot_replace_new_generation`, `test_expired_snapshot_requires_refresh`, `test_stale_snapshot_is_historical_context_only`. Run `./.venv/Scripts/python.exe -m pytest tests/test_pricing_snapshot_publication.py -q`; expect missing catalog/unsafe load.
- [ ] GREEN: write candidate then manifest via temp-file+atomic rename, catalog pointer last; validate on every read, reject policy mismatch/expired members. No scan of arbitrary run dirs. Run focal command; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_runtime_cohort_sqlite_lineage_transport.py tests/test_temporal_evidence_admissibility.py -q`; partial/old artifacts cannot enter runtime.

### Task 9: Directed refresh service using the existing pipeline

**Files:** Create `src/aplicacion/evidence_refresh_service.py`; adapt `src/aplicacion/pricing_live_pipeline.py` and `scripts/run_pricing_live_pipeline.py` only to reuse shared phases rather than shell out; test `tests/test_evidence_refresh_service.py`.

**Interfaces:** `EvidenceRefreshService.refresh(requirement: EvidenceRequirement, *, run_id: str, now: datetime) -> EvidenceRefreshResult` selects catalog sources, executes `colectar_fuentes_pricing` into isolated SQLite, runs `build_semantic_rows`, live offer/temporal bridges and dimensions, builds Task 7 candidate, then publishes through Task 8. Result contains `REFRESH_SUCCEEDED | REFRESH_PARTIAL | REFRESH_FAILED`, run ID, counts and exclusion reasons, optional snapshot ID. It never calls the pricing decision engine. Phase dependencies (downloader, clock, catalog, repository factory, store) are injected for offline tests.

- [ ] RED: `test_missing_evidence_runs_one_directed_refresh`, `test_no_source_is_insufficient_without_network`, `test_reach_missing_is_excluded`, `test_partial_run_preserves_raw_but_does_not_publish`, `test_collector_failure_keeps_previous_pointer_and_fails_closed`. Run `./.venv/Scripts/python.exe -m pytest tests/test_evidence_refresh_service.py -q`; expect missing service.
- [ ] GREEN: reuse the live pipeline phases in-process and write run/gate audit records; distinguish source failure, partial, and complete publication. Run focal command; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_pricing_live_pipeline.py tests/test_live_runner_rigorous_runtime_path.py -q`; no historical baseline promotion or runtime CSV overwrite.

### Task 10: Evaluation coordinator, single-flight and retry decision

**Files:** Create `src/aplicacion/evidence_evaluation_coordinator.py`; modify `src/aplicacion/enki_pricing_query_service.py` only if Task 1's shared route helper needs it; test `tests/test_evidence_evaluation_coordinator.py`.

**Interfaces:** `EvaluationCoordinator.submit(query: str, *, idempotency_key: str | None = None) -> EvidenceEvaluation`; `EvaluationCoordinator.get(evaluation_id: str, *, now: datetime) -> EvidenceEvaluation`. Parse once, derive Task 1 requirement, check Task 8 cache, coalesce active job by requirement key under a local lock, schedule Task 9 refresh with an injected executor, then call `resolver_consulta_pricing(..., parsed_query=original_parsed)` with current compatible cohorts. Persist quote-specific evaluation separately from the shared job; recheck freshness before returning a prior result. A failed/partial refresh leaves decision null and terminal outcome/evidence state explicit.

- [ ] RED: `test_current_cache_skips_refresh`, `test_missing_starts_one_job`, `test_equivalent_queries_share_job_but_not_quote_decision`, `test_incompatible_requirements_do_not_share`, `test_sufficient_refresh_retries_to_decision_ready`, `test_partial_and_failure_fail_closed`, `test_poll_after_expiry_cannot_return_old_decision`. Run `./.venv/Scripts/python.exe -m pytest tests/test_evidence_evaluation_coordinator.py -q`; expect missing coordinator.
- [ ] GREEN: use a bounded local executor and persisted job state, preserving original parsed query and price. `REFRESH_SUCCEEDED` alone never means `DECISION_READY`; no stale fallback. Run focal command; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_enki_pricing_query_service.py tests/test_pricing_evidence_engine.py -q`; existing direct-query behavior and parts checks still pass.

### Task 11: Evaluation API without changing `/decision/pricing`

**Files:** Extend `src/api/decision_pricing_contract.py`, `src/api/main.py`; test `tests/test_decision_pricing_evaluations_api.py`, regress `tests/test_decision_pricing_api.py`.

**Interfaces:** Pydantic `PricingEvaluationResponse` with `evaluation_id`, nullable `requirement_id`/`refresh_run_id`, `evidence_state`, `interpretation: DecisionPricingParsedResponse`, nullable nested `DecisionPricingResponse`, nullable typed `outcome`, `uncertainty`, nullable `retry_after_seconds`. Use Task 1's `project_parsed_query` to persist exactly the existing parsed JSON shape without a second parser. `POST /decision/pricing/evaluations` accepts existing `DecisionPricingRequest` and optional `Idempotency-Key`; `GET /decision/pricing/evaluations/{id}` polls. 202 pending; 200 terminal; 404 unknown ID; 409 idempotency conflict; 429 bounded admission; collector failure is a terminal response, not fabricated 500/decision. Dependency-inject coordinator for tests.

- [ ] RED: `test_post_then_poll_refreshing_to_decision`, `test_clarification_and_unsupported_never_refresh`, `test_refresh_succeeded_can_still_be_insufficient`, `test_idempotency_409_and_unknown_id_404`, `test_failed_refresh_has_no_economic_decision`, `test_old_endpoint_contract_unchanged`. Run `./.venv/Scripts/python.exe -m pytest tests/test_decision_pricing_evaluations_api.py -q`; expect 404/missing models.
- [ ] GREEN: add strict response model/route adapters and keep `_serialize_decision_result` for the nested existing contract. Run focal command; expect PASS.
- [ ] Regression/DONE: run `./.venv/Scripts/python.exe -m pytest tests/test_decision_pricing_api.py tests/test_td013_decision_api_contract.py -q`; old endpoint and uncertainty fields retain shape.

### Task 12: Minimal frontend polling and honest evidence states

**Files:** Modify `frontend/src/features/decision/decision-api.ts`, `frontend/src/features/decision/types.ts`, `frontend/src/features/decision/components/DecisionReviewFlow.tsx`, `frontend/src/features/decision/__tests__/decision-flow.test.tsx`; do not redesign unrelated components.

**Interfaces:** `createPricingEvaluation(query: string, idempotencyKey?: string): Promise<PricingEvaluationResponse>` and `getPricingEvaluation(id: string): Promise<PricingEvaluationResponse>` use the new endpoints. `DecisionReviewFlow` displays interpretation, then bounded polling while 202/REFRESHING, and renders explicit insufficient/failed/current-decision states. Poll cancellation on unmount/new query prevents an old result replacing a new one. Existing `DecisionPricingResponse` remains the nested decision type.

- [ ] RED: Vitest cases `shows_searching_current_evidence`, `shows_insufficient_or_refresh_failed_without_price_label`, `shows_unknown_and_source_date`, `only_ready_shows_bajo_razonable_alto`, `cancels_old_poll_after_query_change`. Run `pnpm test` in `frontend`; expect focused new assertions to fail.
- [ ] GREEN: add typed API methods, a small polling loop using server `retry_after_seconds`, cancellation, and state copy; no source detail unsupported by API. Run `pnpm test`; expect PASS.
- [ ] Regression/DONE: run `pnpm lint` and `pnpm build` in `frontend`; both exit 0, and existing 16-test behavior is preserved plus new cases.

### Task 13: Vertical real-world slice and final verification

**Files:** Create `tests/fixtures/live_refresh/` with small captured/controlled public HTML and provenance metadata; create `tests/test_live_refresh_vertical_slice.py` and `scripts/probe_live_refresh_slice.py`. Update `data/pricing_refresh_sources_v1.csv` only with sources qualified by the probe. Product code changes here are limited to a causally demonstrated gap handled by repeating the owning task's RED/GREEN cycle.

**Interfaces:** Offline fixture test invokes API/coordinator/collector substitute → SQLite RAW/event → bridge/gates → complete snapshot → API polling → `DECISION_READY` and verified `observation_ids`/RAW hashes. Separately marked manual live probe runs from this PC into a fresh isolated `data/live/<run_id>/`, never tracked runtime CSVs; it reports source URLs, acquisition events, each gate, provider IDs, spread and final decision. Do not run any live call as part of ordinary pytest.

- [ ] RED: `test_full_live_fixture_path_decides_only_from_five_current_independent_offers` first fails at the actual missing seam; a paired test with one failed gate ends `INSUFFICIENT_EVIDENCE`. Run `./.venv/Scripts/python.exe -m pytest tests/test_live_refresh_vertical_slice.py -q`; expect causal failure.
- [ ] GREEN: connect only the remaining seam; if actual public sources cannot support the hypothesis, record the source qualification and select the nearest legitimate target before adding a target fixture. Never fabricate a five-offer success by cloning a source/provider. Run focal command; expect PASS.
- [ ] Regression/DONE: run backend full suite with a new workspace tmpdir, frontend `pnpm test`, `pnpm lint`, `pnpm build`, `git diff --check`, and a local requesting-code-review pass. Run the separately marked public-source probe only with founder-authorized network access at execution time; report exact funnel. Success requires a **real**, current, source-backed 5+/3+/≤2.5 cohort and API `DECISION_READY` with BAJO/RAZONABLE/ALTO and traceable RAW. If source qualification cannot establish that, report the exact blocker and keep first-real-cohort/decision acceptance open.

## Execution checkpoints

**First executable milestone (Tasks 1–3):** a supported query yields a stable canonical key, a new acquisition event survives RAW dedup, and `service-price-freshness-v1` admits only a noncontradicted live event younger than 24 hours. All three focal suites and relevant regressions pass; nothing is published to runtime yet.

**First real cohort:** one isolated live run has ≥5 distinct comparable observations from ≥3 independent providers, spread ≤2.5, each with reproducible RAW/event/URL/hash, explicit offer-applicable reach, current v1 temporal admission, compatible unit/context/parts where relevant, and a complete atomically published snapshot. A historical or fixture-only cohort does not satisfy this milestone.

**Real decision:** a real query with a quoted ARS price, parsed once, is evaluated through the new API against that current published cohort and returns `DECISION_READY` plus BAJO/RAZONABLE/ALTO, uncertainty and verifiable provenance. A refresh success, range or insufficient status alone does not satisfy it.

**Main risks:** source shortage for the current target; false offer-level reach from page context; treating acquisition recency as economic validity despite historical source text; dedup aliasing new acquisition to old timestamp; compatibility dimensions lost in cohort serialization; partial/expired snapshot visibility; API job state after restart; stale frontend poll results. Each has an owning task/test above.

**Recommended execution mode after founder approval:** Native sequential implementation through shared interfaces, with an independent final code review. The 13 tasks have tight state/type dependencies and economically consequential gates; spinning up a fresh implementer and reviewer for every small boundary would add context and quota cost. A separate reviewer at the final gate retains independent scrutiny. No execution starts from this recommendation.
