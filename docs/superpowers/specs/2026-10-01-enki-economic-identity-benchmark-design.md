# ENKI — Economic Identity + Benchmark Presentation Design

Status: DRAFT_FOR_REVIEW
Date: 2026-10-01
Scope: Frontend semantic boundary for economic identity and benchmark visualization

## 1. Authority

This design is subordinate to:

1. `docs/ENKI_ARCHIVO_RECTOR.md`
2. `docs/ENKI_DESIGN_RECTOR.md`
3. `docs/superpowers/specs/2026-10-01-enki-design-rector-design.md`

It must preserve:

- REAL != SYNTHETIC
- UNKNOWN != GUESSED
- MISSING != ZERO
- PRICE != COMPARABLE_PRICE
- RANGE_READY != DECISION_READY
- visual confidence must not exceed epistemic confidence
- accessibility is part of correctness
- undemonstrated claims remain undemonstrated

## 2. Objective

Prevent ENKI from visually or semantically comparing a user's price against an evidence cohort unless that comparison is demonstrated to be valid.

Target flow:

validated decision payload
→ economic identity / comparability projection
→ BenchmarkPresentation
→ renderer

React must render already-authorized benchmark semantics rather than reconstruct comparability from loose transport fields.

## 3. Brownfield problem

The current frontend:

- permits benchmark display for RANGE_READY and DECISION_READY;
- requires MIN/Q1/median/Q3/MAX;
- uses an EXACT ARS user price when available;
- computes benchmark geometry inside `BenchmarkRail`;
- clamps user prices to the [MIN, MAX] visual range.

Therefore:

- a user price below MIN can appear at MIN;
- a user price above MAX can appear at MAX.

This creates false visual equivalence between an observed endpoint and a value outside the observed distribution.

The current contract also places:

- queried amount/currency in `parsed.price`;
- cohort scope in `evidence.price_scope`.

Cohort scope is not automatically proof of the queried price's own scope.

## 4. Economic identity invariant

A comparable price must preserve the material identity needed for comparison:

- amount;
- currency;
- unit / cadence / scope;
- commercial context when material;
- approximation status.

Rules:

1. UNKNOWN is not compatibility.
2. Missing scope is not inferred scope.
3. Evidence scope is not automatically user-price scope.
4. No implicit currency conversion.
5. No implicit unit conversion.
6. No silent commercial-context normalization.
7. Approximate input must not silently become exact.
8. Failure to demonstrate comparability removes the graphical user-price marker, not necessarily the valid cohort distribution.

## 5. Benchmark authorization

A benchmark may be considered only when the validated presentation contract authorizes it.

MVP eligibility:

- RANGE_READY → eligible
- DECISION_READY → eligible
- all other states → ineligible

Eligibility does not itself authorize a rail.

## 6. Distribution validity

A graphical distribution requires finite numeric values for:

- MIN
- Q1
- median
- Q3
- MAX

with:

`MIN <= Q1 <= median <= Q3 <= MAX`

and:

`MAX > MIN`

Invalid, non-finite or degenerate distributions must not render a rail.

The frontend must never reorder, repair, synthesize or guess the distribution.

## 7. Currency compatibility

A user's price may be plotted only when currency compatibility with the cohort is demonstrated.

This plan performs no currency conversion.

Unknown or incompatible currency means no graphical user-price comparison.

## 8. Scope / unit compatibility

`evidence.price_scope` describes the cohort.

It is not sufficient on its own to prove the queried price uses the same unit, cadence or scope.

A user-price marker requires demonstrated compatible scope.

If the current response does not provide enough information to prove that compatibility, the frontend must abstain from plotting the user price.

This plan does not authorize a backend change.

## 9. Commercial context

Commercial context must not be silently normalized.

If context materially affects comparability and equivalence is not demonstrated, the frontend must not infer equivalence.

## 10. BenchmarkPresentation

Benchmark semantics must be projected into a closed presentation model before rendering.

Conceptual form:

```ts
type BenchmarkPresentation =
  | {
      kind: "rail";
      min: number;
      q1: number;
      median: number;
      q3: number;
      max: number;
      userPrice: number | null;
      userPosition:
        | "BELOW_RANGE"
        | "WITHIN_RANGE"
        | "ABOVE_RANGE"
        | null;
    }
  | {
      kind: "text_only";
      reason:
        | "INVALID_DISTRIBUTION"
        | "NON_COMPARABLE_PRICE";
    }
  | {
      kind: "unavailable";
    };
```

Exact names are implementation details.

Normative rule:

`BenchmarkRail` must not decide economic comparability.

It renders a presentation model already authorized by the semantic boundary.

## 11. User-price position

### Below range

When:

`userPrice < MIN`

the UI must communicate that the price lies below the observed range.

It must not clamp the marker to MIN.

### Within range

When:

`MIN <= userPrice <= MAX`

the price may be positioned proportionally.

Its relation to Q1–Q3 may be described as:

- below the central observed interval;
- within the central observed interval;
- above the central observed interval.

These are descriptive statistical statements, not economic decisions.

### Above range

When:

`userPrice > MAX`

the UI must communicate that the price lies above the observed range.

It must not clamp the marker to MAX.

## 12. RANGE_READY vs DECISION_READY

Benchmark geometry does not grant decision authority.

RANGE_READY may show descriptive evidence.

It must never derive:

- BAJO
- RAZONABLE
- ALTO

from:

- quartiles;
- median;
- user position;
- distance;
- visual geometry.

DECISION_READY classification remains controlled exclusively by the validated decision presentation contract.

## 13. Approximation

`parsed.price.is_approximate` must not be discarded semantically.

Approximate input must not be presented as exact.

This plan does not add new normalization or approximation heuristics.

## 14. Renderer responsibilities

`BenchmarkRail` may:

- render MIN and MAX;
- render Q1–Q3 as the central observed interval;
- render the median;
- render an authorized user price;
- show an exterior out-of-range representation;
- expose an accessible textual equivalent.

It must not:

- infer comparability;
- infer unit or scope;
- convert currencies;
- normalize commercial context;
- derive BAJO / RAZONABLE / ALTO;
- clamp out-of-range user prices into the observed range.

## 15. Accessibility

WCAG 2.2 AA remains the minimum.

The visualization must not depend on color alone.

A textual equivalent must communicate, when applicable:

- MIN;
- Q1;
- median;
- Q3;
- MAX;
- user price;
- whether the user price is below, within or above the observed range.

Desktop and mobile may use different geometry but must preserve identical semantics.

## 16. TDD requirements

Implementation begins RED → GREEN → REFACTOR.

Minimum cases:

1. valid distribution + comparable internal price → rail;
2. price below MIN → exterior, not clamped;
3. price above MAX → exterior, not clamped;
4. MIN === MAX → no rail;
5. unordered quantiles → no rail;
6. NaN / Infinity → no rail;
7. unauthorized state → no benchmark;
8. incompatible currency → no user-price comparison;
9. unknown/incompatible scope → no user-price comparison;
10. RANGE_READY never derives BAJO / RAZONABLE / ALTO;
11. accessible text preserves distribution and price position;
12. desktop/mobile preserve equivalent semantics.

## 17. Non-goals

This plan does not implement:

- backend changes;
- currency conversion;
- unit conversion;
- price normalization;
- new thresholds;
- cohort construction;
- evidence refresh;
- provenance redesign;
- temporal redesign;
- request-race handling;
- navigation;
- global visual redesign;
- V2 experiments.

## 18. Stop conditions

Implementation must stop if satisfying comparability requires:

- a backend contract change;
- a new inferred field;
- an undocumented normalization rule;
- a new pricing threshold;
- a new comparability heuristic.

Those require a separate design decision.

## 19. Acceptance criterion

Plan 2 succeeds when the frontend distinguishes:

- valid observed distribution;
- comparable queried price;
- non-comparable queried price;
- below-range price;
- within-range price;
- above-range price;
- invalid/degenerate distribution;

without allowing chart geometry to overstate what ENKI knows.

Core invariant:

**No graphical user-price comparison without demonstrated comparability, and no out-of-range value represented as an observed endpoint.**

