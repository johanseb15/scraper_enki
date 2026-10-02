# Live evidence refresh for Enki Decision — architectural design

Date: 2026-09-28  
Status: founder review; design only  
Authority: `docs/ENKI_ARCHIVO_RECTOR.md`  
Product boundary: `scraper_enki`

## 1. Goal and invariant

An understood pricing query must reuse current, comparable real evidence when it exists. Otherwise Enki must run a bounded acquisition from the machine hosting the API, preserve RAW and provenance, apply the existing admission gates, publish a complete cohort snapshot, and retry the decision. If evidence remains insufficient, the result remains insufficient. Historical and synthetic evidence never become current real evidence by inference.

The chain remains REALITY → OBSERVATIONS → IDENTITY → NORMALIZATION → COMPARABILITY → PROVENANCE → TEMPORAL UNDERSTANDING → ANALYSIS → SIMULATION → DECISION. RAW comes first; unknown is not guessed; missing is not zero; provider location is not service reach; REMOTE is not NATIONAL. The refresh path neither changes these gates nor interprets a query a second time.

## 2. Brownfield baseline and exact break

| Existing component | Disposition | Role in this design |
| --- | --- | --- |
| `EnkiPricingQueryService` | ADAPT | Parse once, return the parsed query and typed requirement to the evaluation coordinator, then re-evaluate the same parsed quote against an admitted cohort. Keep its existing direct-call behavior. |
| `PricingEvidenceEngine` and U-009 parts compatibility | NO_CHANGE | Compare and decide only from cohorts admitted for the requirement. |
| Runtime cohort loader and builder, lineage/reach/temporal gates | EXTEND at the input/publication boundary | Build and validate candidate cohorts from isolated live observations; load only published, complete, currently admissible snapshots. Reuse gate logic and thresholds. |
| HTTP collector, SQLite RAW repository, live offer/temporal bridges, source registry | EXTEND | Directed collection, acquisition-event identity, extraction, provenance and gate inputs. The registry is a targeting hint, not evidence of reach. |
| `POST /decision/pricing` | NO_CHANGE | Existing synchronous contract and behavior remain available. |
| Decision API and frontend Decision flow | ADAPT through new endpoints/states | Add asynchronous evaluation/polling without silently changing the existing endpoint. UX implementation is outside this design gate. |

The current CLI can fetch and store real HTML, then emit semantic and temporal artifacts, but its outputs are not automatically a runtime snapshot that the API can load. The API currently loads precomputed cohort CSVs and calls the query service/evidence engine; it does not request refresh. The live probe acquired 7 public pages into isolated SQLite RAW, verified 7 hashes, extracted 94 semantic observations, and obtained 6 eligible observations with lineage admitted. None had admitted explicit reach or current temporal status, so no cohort could be published. The temporal bridge marked them `HISTORICAL_REPRODUCIBLE` with unknown freshness even though acquisition happened today. The one source with explicit Córdoba home-service wording did not produce an offer-level reach claim; a provider address cannot fill that gap. Two Buenos Aires urgent hourly price observations were from two providers and included source price periods that cannot be silently treated as current. Thus the missing orchestration is real, and making it alone will not cure source, reach or freshness gaps.

## 3. Architecture choice and boundaries

Choose **cache-first plus directed refresh-on-demand** in one API process. A canonical EvidenceRequirement identifies admissible cache entries and coalesces concurrent refresh jobs. The coordinator checks a complete snapshot with the current freshness policy. If none can satisfy the requirement, it selects a bounded set of known public collectors, starts one isolated local run, and exposes progress through a persisted evaluation/job record. A run creates candidate observations and cohorts, validates them, and publishes atomically. The coordinator then retries the existing decision path using the same parsed query. No job success is itself a price decision.

Precomputed/manual refresh is simpler but does not meet the user-triggered refresh requirement. Pure refresh-on-demand reacquires needlessly, adds latency to every query, and loses reuse. The hybrid adds a small cache index and job coordinator; it uses the current collector, SQLite and gates, and needs no scheduler or queue. It is not a generic crawler. A single process and a local single-flight lock per requirement are the MVP concurrency boundary. Startup recovery is deterministic; multi-process job coordination is out of scope.

Proposed new application boundaries:

- `EvidenceRequirement`: immutable typed projection of the *already parsed* query. It expresses required economic dimensions, not a purported source claim.
- `EvidenceEvaluationCoordinator`: owns lookup, refresh need, job coalescing, retry, and evaluation state; it never extracts source facts or decides price.
- `EvidenceRefreshService`: requirement → known-source candidates → existing collector and processing pipeline → candidate snapshot → validation/publication → structured refresh result. It never parses user text, bypasses a gate, or returns BAJO/RAZONABLE/ALTO.
- `SnapshotCatalog` and `RefreshRunJournal`: small local, durable metadata around per-run SQLite/RAW artifacts and cohort snapshots. Existing persistence remains the source of RAW; a new database is not required.
- `FreshnessPolicy`: versioned, auditable policy evaluator invoked at admission and again on cache read.

These are ownership boundaries, not a mandate for one class or file per name. Prefer existing application modules where responsibilities already fit.

## 4. EvidenceRequirement and identity

The parser runs once per evaluation. For a supported pricing query it yields a typed requirement containing `schema_version`, `canonical_service`, `market`, required `geographic_reach`, `modality`, `price_scope`, `commercial_context`, and `parts_scope` when the service is economically sensitive to parts. It also retains the existing economic qualifiers that affect comparability, including currency, bundle/inclusions, device or hardware/materials scope when applicable to that service, and any scope qualifier actually enforced by the current comparators. Explicit `UNKNOWN` remains distinct from every known value and cannot become a positive match. The exact field projection must be checked against existing service-specific comparators during implementation; adding a key field must be justified by a real economic distinction. No unsupported dimension is invented.

Canonical identity is a stable hash of versioned canonical JSON: normalized enum/value names, sorted keys, explicit unknown/null treatment, and only dimensions that determine cohort membership. The user's wording, quoted price amount, acquisition URL and provider identity are **not** part of this key. Two economically equivalent queries can therefore share one refresh job and cohort, while evaluations keep their own quoted price, interpretation and decision. Incompatible requirements never share a snapshot merely because service and city match. A parts-sensitive included-parts requirement cannot consume a labor-only cohort; an insensitive service does not gain a false parts filter. A policy or comparator version change forces revalidation or invalidates the cached admission, rather than trusting an old key blindly.

Current runtime cohort rows group by market, service, price scope and commercial context; the U-009 check also uses parts scope. Before publishing a live snapshot, the representation must carry every dimension that the selected service's comparability contract requires. If a required dimension cannot be represented or proven from RAW, that candidate is excluded; it is never collapsed into an apparently compatible cohort. This is a publication constraint, not a request to loosen the existing cohort contract.

## 5. Acquisition targeting and safety

A small versioned catalog maps supported requirements to known collector/source candidates and allowed public URLs. It filters by declared source capability and market to avoid Internet-wide search. Catalog location and source metadata may direct a request, but they cannot become admitted reach, price scope, parts scope, currency, temporal identity or provider identity. Those facts must come from captured RAW and existing semantic/gate paths. No matching collector yields a terminal insufficient-evidence result with `SOURCE_GAP`.

Collectors accept only HTTP/HTTPS from an explicit allowlist. Resolve and reject private, loopback, link-local and metadata destinations before connection and after each controlled redirect; bound redirect count, connect/read timeouts, response bytes, accepted content types and per-source request rate. Never execute downloaded content. Preserve response bytes immutably with SHA-256 and source URL/identity; validate the hash on read. These controls protect the API from source-driven network and storage abuse. A collector needing credentials, paid quota or an LLM is unavailable to this MVP path.

## 6. Run and provenance model

Each refresh has `run_id`, canonical requirement identity and schema/policy versions, `started_at`, optional `finished_at`, status, selected collectors, requested URLs, acquisition events, RAW references, semantic observations, gate decisions and exclusion reasons, candidate cohorts, published snapshot ID and final result. Use an isolated `data/live/<run_id>/` layout or equivalent current run-isolation convention. Historical artifacts and tracked runtime CSVs are never overwritten by a probe or incomplete run.

An acquisition event has its own event ID, run ID, source/collector ID and version, requested/final URL, fetched/acquired-at UTC, HTTP outcome, RAW storage reference and SHA-256. Content-addressed RAW may be deduplicated, but a repeated fetch of identical bytes still records a separate acquisition event. This closes the current SQLite dedup behavior where the same source/record/hash can return the original RAW row and timestamp: the new fetch must not pretend to be the old fetch. `acquired_at` is distinct from publication time and from any source-validity dates. Extraction and normalization record their code/schema versions and link each observation to the specific acquisition event and RAW hash. Provider identity and independence remain explicit gate inputs.

Persist a small journal/manifest durably for each local job. Its state is one of `STARTED`, `ACQUIRING`, `PROCESSING`, `VALIDATING`, `COMPLETE`, `FAILED` (with explicit failure reason). The public evaluation states in section 9 are a separate contract. A restart treats any journal without a validated `COMPLETE` manifest and published catalog reference as unpublished; it may mark it interrupted and schedule a fresh run. It never loads its candidate cohorts. Raw material from interrupted runs remains auditable but is not runtime evidence until successfully reprocessed and republished under a complete run.

## 7. Freshness contract

Store and evaluate separately:

- `acquired_at` UTC: when these bytes were acquired; it is not proof the quoted price is economically current.
- `source_valid_from` / `source_valid_until`: only if the source explicitly supports those bounds. Preserve unparsed source period text separately; never manufacture a first/last day from a month label.
- `freshness_policy_version`: immutable version of the approved policy used for this decision.
- `freshness_decision` and structured `freshness_reason`, plus evaluation time, source/date references and applicable limit.

The MVP policy is conservative and combined. It requires (1) an approved maximum age since acquisition for the evidence class and (2) compatibility with any explicit source validity interval or period. An explicit source expiry or contradictory period overrides a recent acquisition and rejects current admission. A source-valid-until date in the future does not override an acquisition older than the approved maximum age. A future-dated validity start or ambiguous/unparseable period is not silently converted into current; the policy defines whether it is `UNKNOWN` or rejected, and either way it is not admitted as current. A source without an explicit validity period can be admitted only if the approved policy explicitly permits that evidence class, the acquisition is recent enough, and all other temporal facts/gates are satisfied. Re-evaluate at each cache read, because a once-valid snapshot can expire while stored.

The numerical age limit and treatment of undated or month-only price statements require founder approval before any live observation can be labeled `CURRENT_REPRODUCIBLE`. The design intentionally sets no TTL. The policy is versioned and its values and reasons are recorded with each gate decision; changing it triggers revalidation rather than reinterpretation of historical records. Existing temporal gate behavior remains fail closed until such a policy exists.

## 8. Atomic cohort publication and cache read

Publication order is strict:

1. Create isolated run and journal; select known sources.
2. Acquire and preserve RAW plus distinct acquisition events.
3. Extract and normalize observations linked to RAW.
4. Apply lineage, explicit reach, temporal/freshness, commercial, parts and provider-independence gates; record admissions and exclusions.
5. Build a candidate snapshot for only the affected requirement/cohort family from admitted current real observations. A full internal rebuild is acceptable if necessary, but unrelated/historical rows cannot leak into the published key.
6. Validate schema, hashes, raw links, requirement dimensions, provenance, provider independence, minimum observations/providers, dispersion and current policy. Candidate bytes stay outside the active catalog.
7. Write and durably finalize a `COMPLETE` manifest naming the validated snapshot and hash.
8. Atomically replace the catalog entry for the requirement with a pointer to that complete snapshot. The catalog update occurs on the same filesystem and is itself atomic; readers validate the pointed manifest/hash before use.

The complete manifest precedes publication. A crash before step 8 leaves a complete but unreferenced snapshot; a retry may validate and publish it. A crash after step 8 leaves a pointer to a complete snapshot. No reader scans arbitrary run directories for cohorts. Failed or partial runs never modify the active pointer. A previously published snapshot remains physically intact, but is usable for a new decision only while it independently passes the current freshness and comparability checks; otherwise return insufficient evidence and refresh. No stale fallback is presented as current. Snapshot replacement should use a per-requirement lock and compare the expected catalog generation to prevent an older run overwriting a newer complete one.

`REFRESH_SUCCEEDED` means the run completed and published a validated artifact. It does **not** imply the quoted query satisfies `DECISION_READY`: the re-evaluation may still yield `NO_EVIDENCE` or `INSUFFICIENT_EVIDENCE` under the existing engine. A run with valid RAW but no publishable cohort is `REFRESH_PARTIAL` and carries gate reasons, never a partially visible snapshot.

## 9. API, idempotency and evaluation states

Keep `POST /decision/pricing` unchanged. Add a separate flow:

`POST /decision/pricing/evaluations` accepts `{"query": "..."}` as the existing endpoint does, plus an optional `Idempotency-Key` request header. It parses once, stores the parsed interpretation/quoted amount with an evaluation ID, derives the canonical requirement, checks the cache, and either evaluates immediately or attaches to/starts a refresh job. A response envelope has the following stable fields (nullable fields are present as `null` when inapplicable):

```json
{
  "evaluation_id": "opaque-id",
  "requirement_id": "canonical-key-or-null",
  "evidence_state": "REFRESHING",
  "refresh_run_id": "opaque-run-id-or-null",
  "interpretation": { "existing_parsed_fields": "..." },
  "decision": null,
  "outcome": null,
  "uncertainty": ["safe-public-reason-code"],
  "retry_after_seconds": 2
}
```

`interpretation` retains the existing parsed query semantics, including unknown/clarification fields. `decision` is a nested existing `DecisionPricingResponse` only after that service has actually run against a compatible published cohort; it may report the existing engine's `INSUFFICIENT_EVIDENCE`, but only its `DECISION_READY` status permits BAJO/RAZONABLE/ALTO. `outcome` is a typed terminal non-decision result such as `CLARIFICATION_REQUIRED`, `UNSUPPORTED_QUERY`, `NO_EVIDENCE`, `INSUFFICIENT_EVIDENCE`, or a refresh failure reason. This makes an uncompleted refresh distinguishable from an attempted but unsupported decision. `retry_after_seconds` is non-null only while pending; its exact bounded value is server configuration, not an economic policy. Clarification and unsupported outcomes are terminal without refresh. Reusing the same client idempotency key and identical request returns the same evaluation; reusing it with a different payload is a conflict. Without that key, two POSTs may have distinct evaluation IDs but share a refresh job by canonical requirement.

`GET /decision/pricing/evaluations/{id}` returns the same envelope with current persisted state and, when ready, the result of rerunning the existing decision engine on its original parsed quote and the published cohort. A pending response uses HTTP 202 and a terminal response HTTP 200. Validation errors use 4xx, unknown ID 404, idempotency conflict 409, and request/rate limits 429. Collector/network failures are represented by `REFRESH_FAILED` with safe public reason codes in a terminal evaluation, not a fabricated economic decision or a generic 500. A server-provided retry interval and bounded client polling avoid tight loops. If the process restarts, incomplete jobs are marked interrupted/failed and no partial result becomes available; clients can request a new evaluation/refresh.

The evidence state enum is `EVIDENCE_AVAILABLE`, `REFRESH_REQUIRED`, `REFRESHING`, `REFRESH_SUCCEEDED`, `REFRESH_PARTIAL`, `REFRESH_FAILED`, or `INSUFFICIENT_EVIDENCE`. `REFRESH_REQUIRED` is a durable transition, not a claim that work succeeded. `REFRESH_SUCCEEDED` records that a complete snapshot was published; a subsequent insufficient evaluation can set `INSUFFICIENT_EVIDENCE` while retaining the run outcome in its audit record. BAJO, RAZONABLE or ALTO appears only with `DECISION_READY`. Unknown interpretation and excluded facts remain visible. An expired snapshot can be described as historical/informative only through an explicit separate contract; this MVP API never labels it current or uses it for a current decision.

For distinct users with economically equivalent requirements, refresh acquisition is single-flight and reusable; their interpretation and quoted price stay separate. A fresh snapshot is checked again at the instant each evaluation completes. The API must not return a past evaluation's decision as if it were newly current after its evidence expires.

## 10. Failure model

| Event | Persisted/result behavior |
| --- | --- |
| Current compatible snapshot found | `EVIDENCE_AVAILABLE`; no refresh; run existing decision. |
| Missing, insufficient or stale snapshot | `REFRESH_REQUIRED` → `REFRESHING`; one directed job per requirement. |
| Collector/source unavailable | `REFRESH_FAILED` with source/network reason; active snapshot unchanged; no stale decision. |
| RAW acquired but reach, temporal, commercial or provider gate excludes too much | `REFRESH_PARTIAL` then `INSUFFICIENT_EVIDENCE`; preserve RAW and exclusions; no publish. |
| Snapshot validated and atomically published | `REFRESH_SUCCEEDED`; retry evidence/decision; `DECISION_READY` only if the engine's conditions hold. |
| Crash/restart during run | Unpublished run ignored by runtime; resume by a new controlled attempt, not by assuming completion. |
| No matching known public source | `INSUFFICIENT_EVIDENCE` with `SOURCE_GAP`; no open-ended crawling. |

Avoid duplicate network work with single-flight per requirement, bounded concurrency, source rate limits and request budgets. Distinguish transient source errors from permanent unsupported requirements for UX and retry. Persist internal diagnostic reason codes and expose safe, concise user explanations.

## 11. First vertical slice and pivot rule

Working hypothesis: `VISITA_TECNICA_DOMICILIO`, Buenos Aires, `PER_HOUR`, `URGENCY`; parts scope is not a required dimension for this service. The existing runtime contract requires at least five observations, three independent providers, and dispersion no greater than 2.5. The live probe did not establish this: its two urgent hourly Buenos Aires offers came from two providers, had unproven currentness/reach, and may differ in urgency terms (after-hours versus weekend/holiday). The implementation phase must first qualify current public sources against all required facts. If it cannot obtain the minimum without widening urgency or inventing reach, select another supported service/market with the shortest factual distance. The architecture and API stay generic to EvidenceRequirement; no target-specific gate exemption is permitted.

The slice proves one real public source family → acquisition event and immutable RAW → semantic observation → explicit reach and temporal facts → all existing gates → complete snapshot → new Decision API → frontend evidence/decision states. A single fully traceable offer is useful early proof of the pipeline but does not meet cohort or decision acceptance.

## 12. Test strategy and acceptance

Implementation follows TDD only after this spec is approved and an implementation plan is reviewed. Tests use fake HTTP and clock at the boundary plus real local RAW/SQLite/gate integration fixtures; no paid APIs or live network are required in the ordinary suite. At least these behaviors must be demonstrated:

| Scenario | Required assertion |
| --- | --- |
| Current compatible cache | No collector call; decision uses published snapshot. |
| Missing evidence | Exactly one directed refresh starts. |
| Equivalent queries | One shared refresh/job; separate quote-specific evaluations. |
| Incompatible requirements | Distinct keys/jobs or snapshots; no cross-cohort use. |
| RAW and provenance | Hash, URL, event time and observation lineage reproduce; identical bytes fetched twice preserve two events. |
| Missing reach | Observation excluded; provider address or REMOTE cannot imply reach. |
| Invalid/unknown freshness | Observation excluded; policy version and reason recorded. |
| Partial refresh | No catalog pointer change and no decision from partial data. |
| Collector failure | Fail closed; previous stale snapshot never used as current. |
| Successful refresh | Complete manifest and atomic pointer; runtime loads only complete snapshot. |
| Sufficient cohort | Existing engine can emit `DECISION_READY` with BAJO/RAZONABLE/ALTO and provenance. |
| Snapshot expiry | Next equivalent query requires refresh; cached admission is rechecked. |
| Restart | Incomplete runs ignored; complete published snapshot remains verifiable. |
| Race | Concurrent equivalent evaluations coalesce; older completion cannot replace newer snapshot. |

Acceptance for the architecture is a reproducible current real decision from the running machine, with source-backed reach, price unit, commercial scope, temporal admission, provider independence and a trace to RAW; any insufficient outcome must explain which gate prevented admission. Existing `/decision/pricing` and U-009 behavior remain compatible.

## 13. UX contract that can proceed in parallel

The visual work can design input, interpreted query and clarification, unsupported query, current-evidence lookup, “Buscando evidencia actual…”, refresh progress, no or insufficient verifiable evidence, refresh failure, and a decision with source/provenance, acquisition time, source-validity information, uncertainty and exclusions. Show `EVIDENCE_AVAILABLE`, `REFRESH_REQUIRED`, `REFRESHING`, `REFRESH_SUCCEEDED`, `REFRESH_PARTIAL`, `REFRESH_FAILED` and `INSUFFICIENT_EVIDENCE` honestly. `REFRESH_SUCCEEDED` may still lead to insufficient evidence. Only `DECISION_READY` may show BAJO/RAZONABLE/ALTO. UNKNOWN is a visible state, not blank or zero. Do not fabricate source detail that the response lacks or render stale evidence as a current market answer.

## 14. Decisions reserved for the founder

1. Approve numerical maximum acquisition age per supported evidence class (and any class-specific exception), and the policy version that records it. No numerical TTL is implied here.
2. Decide whether source material without an explicit price-validity period can be considered current when acquired recently, and how month-only or ambiguous periods are handled. Conflict always fails closed.
3. Approve whether stale evidence may be shown as separate historical context and, if so, with which UX/API wording; it remains inadmissible for a current decision.
4. After source qualification, approve or pivot the first vertical-slice target if its public sources cannot legitimately meet five observations/three providers/dispersion and required gates. No threshold change is proposed.

Technical limits such as request timeouts, byte caps, concurrency and polling cadence are implementation choices to set conservatively and test in the implementation plan; they do not redefine economic freshness.

## 15. Explicitly outside MVP

No scheduler, external queue, distributed worker or microservice; no generic/open crawler, LLM extraction, vector database, new database if SQLite and local artifacts suffice, simulation as real evidence, old-PC recovery, international expansion, wholesale frontend redesign, gate relaxation or synthetic cohort promotion. A future scheduled refresh can call the same bounded refresh service without changing this decision contract.

## 16. Design gate

This document is the architectural spec for founder review, not authorization to implement. After approval, the next Superpowers gate is a reviewed implementation plan. No product code, production cohorts, git staging or commit belongs to this spec-writing step.
