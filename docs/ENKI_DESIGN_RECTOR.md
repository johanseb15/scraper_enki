# ENKI Design Rector

**Status:** CANONICAL_APPROVED  
**Date:** 2026-10-01  
**Scope:** UX, interaction, content, evidence presentation, visualization, accessibility and design governance for ENKI.  
**Authority:** subordinate to `ENKI_ARCHIVO_RECTOR.md`; superior to UX/UI implementation specs and plans.

---

## 1. Purpose

The ENKI Design Rector defines what must remain true in the user experience while ENKI evolves.

It does not define backend implementation, component names, file structure, framework choices or sprint tasks.

Its purpose is to translate ENKI's domain and epistemic rules into stable product-experience constraints so that visual quality, speed, convenience or experimentation never create economic meaning that the evidence does not authorize.

The governing product sequence remains:

**REALITY → OBSERVATIONS → IDENTITY → NORMALIZATION → COMPARABILITY → PROVENANCE → TEMPORAL UNDERSTANDING → ANALYSIS → SIMULATION → DECISION**

And the executive sequence remains:

**ENTENDER → CONECTAR → APRENDER → EXPLOTAR**

---

## 2. Authority hierarchy

The design authority chain is:

1. `ENKI_ARCHIVO_RECTOR.md`
2. `ENKI_DESIGN_RECTOR.md`
3. approved product/design specifications
4. implementation plans
5. implementation

A lower layer MUST NOT weaken, reinterpret or silently bypass a higher layer.

If a lower-level decision conflicts with a higher-level rule, the higher-level rule prevails and the experience MUST fail closed until the conflict is resolved.

---

## 3. Normative language

This document uses three levels:

- **MUST / DEBE**: mandatory invariant or product contract.
- **SHOULD / DEBERÍA**: default direction; deviation requires a documented reason.
- **MAY / PUEDE**: allowed option, not prescribed.

Visual preference, trend and experimentation never override a MUST.

---

# LAYER 1 — INVARIANTS

## 4. Truth before decision

ENKI MUST preserve the path from observation to decision.

A number, chart, visual treatment or readiness status does not authorize an economic conclusion by itself.

Economic meaning may only increase when the underlying semantic, comparable, provenance and temporal conditions support it.

---

## 5. No invented certainty

The experience MUST preserve these equivalences:

- real ≠ synthetic;
- unknown ≠ assumed;
- missing ≠ zero;
- price ≠ comparable price;
- observation ≠ promoted knowledge;
- interpretation ≠ user statement;
- frequency ≠ independence.

When a material condition is unknown, ambiguous, conflicted or contradictory, ENKI MUST prefer abstention over unsafe inference.

The interface MUST NOT silently complete missing meaning for the purpose of creating a result.

---

## 6. Visual confidence cannot exceed epistemic confidence

Visual polish MUST NOT communicate more certainty than the evidence supports.

Precise numbers, confident typography, strong color, charts, badges or labels MUST NOT imply:

- representativeness not demonstrated;
- freshness not demonstrated;
- comparability not demonstrated;
- recommendation not authorized;
- runtime behavior not verified.

---

## 7. Economic identity of price

A price is not only an amount.

Where material, its economic identity includes:

- amount;
- currency;
- unit or cadence;
- scope;
- commercial context;
- bundle/material/hardware conditions;
- approximate versus exact character;
- applicable temporal context.

These dimensions MUST remain associated with the price whenever their loss could alter interpretation or comparability.

`EXACT` amount does not, by itself, establish comparability.

ENKI MUST NOT silently convert currencies, infer units, decompose bundles, assume commercial context or invent an approximation margin.

---

## 8. RANGE_READY is not DECISION_READY

`RANGE_READY` MAY authorize:

- description of comparable observations;
- distribution or interval;
- descriptive position of a user price when that position is valid.

`RANGE_READY` MUST NOT authorize:

- `BAJO`;
- `RAZONABLE`;
- `ALTO`;
- "precio justo";
- "buen precio";
- "deberías pagar/cobrar";
- equivalent recommendation language.

A statistical central band is not automatically a recommended price.

`DECISION_READY` is the only family that MAY expose a secondary economic classification, and only when its complete authorization conditions are valid.

---

## 9. Human conclusion first

The first visible conclusion MUST be a specific human sentence that explains:

1. what ENKI can conclude;
2. what that conclusion refers to;
3. any material limitation that changes its meaning.

Economic enums or classifications are secondary.

A valid classification MUST NOT replace the human explanation.

---

## 10. Material evidence accompanies the conclusion

The user MUST be able to understand the basis of a material conclusion without opening a separate evidence investigation.

Information that changes interpretation or decisional permission MUST remain visible with the result.

Detailed lineage, documents and methodological depth MAY use progressive disclosure.

Material limitations MUST NOT be hidden behind progressive disclosure.

---

## 11. Original observation and intent are preserved

ENKI MUST NOT silently lose or replace:

- the user's original wording;
- the user's economic intent;
- previously supplied material facts;
- a valid observed price;

during clarification, correction, retry, error or state transition.

An inferred interpretation is not equivalent to a confirmed user statement.

---

## 12. Natural Language First

Natural language is the primary input model.

ENKI SHOULD allow the user to describe or paste the real situation before requiring structured entry.

Structured controls MAY be introduced where they reduce ambiguity or effort.

Structured controls MUST NOT:

- force an exhaustive form before first value;
- convert a guessed option into user-declared truth;
- replace the original utterance;
- imply exhaustive knowledge when available options are incomplete.

---

## 13. Value before identity

The first useful analysis MUST NOT require account creation.

The experience MUST NOT simulate personalization that does not exist.

Names, history, saved context or personalized greetings MUST only appear when grounded in real product state.

---

## 14. Accessibility is part of correctness

WCAG 2.2 AA is ENKI's internal accessibility floor for the experience.

Accessibility is not post-MVP polish when it affects the decision path.

Critical states MUST preserve:

- visible focus;
- logical focus order;
- keyboard access;
- programmatic association of relevant errors;
- appropriate status communication;
- applicable contrast;
- non-color-only meaning;
- textual equivalents for material visualizations;
- usable reflow and text enlargement.

Claims of accessibility conformity MUST be based on executed validation, not static inspection alone.

---

## 15. Unverified remains unverified

ENKI MUST distinguish between:

- static inspection;
- unit test;
- mocked test;
- integrated test;
- accessibility test;
- responsive/device test;
- runtime behavior;
- production state.

Evidence from one level MUST NOT be silently promoted into proof of another.

Mockups, fixtures, Baseline V1 and mocked tests do not prove production capability.

---

# LAYER 2 — UX CONTRACTS

## 16. Closed semantic presentation contract

The UI MUST NOT freely interpret backend fields.

Each semantic state family MUST define the permitted:

- visible conclusion;
- economic classification;
- price presentation;
- evidence presentation;
- visualization;
- limitation;
- user action.

Unknown, contradictory or incomplete combinations MUST fail closed.

A residual branch MUST NOT produce affirmative economic wording such as "razonable".

---

## 17. Experience state families

The Design Rector defines semantic families, not internal enum names.

### 17.1 Input

The user is still expressing the situation.

ENKI MUST NOT assume material intent, geography, unit, service or commercial context merely to move forward.

### 17.2 Interpretation

ENKI presents what it understood.

Where material, the interface MUST distinguish:

- stated / explicit;
- interpreted / inferred;
- derived;
- ambiguous;
- conflicted;
- unknown.

Visual review alone MUST NOT automatically convert an inferred claim into a confirmed user fact.

### 17.3 Clarification required

A material fact is unknown, ambiguous or conflicted and can alter comparability or decision.

ENKI MUST NOT emit an economic judgment.

The experience MUST:

- preserve the original query;
- keep the clarification context understandable;
- ask for the missing material information;
- allow correction without reconstructing the full original query.

Until materiality can be classified reliably, interpretations capable of changing service, intent, currency, unit, scope, geography or commercial context SHOULD remain blocking before decision.

### 17.4 Processing

The interface MUST preserve which user request is currently authoritative.

A stale response MUST NOT replace the result of a newer request.

### 17.5 Recoverable error

The original input and relevant context MUST be preserved.

The message MUST explain recovery in human language.

Infrastructure terminology such as framework names, ports, parser internals or backend implementation details MUST NOT be exposed as primary user guidance.

### 17.6 Insufficient evidence

ENKI cannot form the requested evidence-backed result.

The interface MUST explain that limitation without inventing a different cause.

### 17.7 Unsupported request

The request lies outside the currently supported product capability.

Unsupported does not mean "non-comparable".

### 17.8 Evidence present but non-comparable

Evidence exists, but demonstrated material dimensions prevent comparison.

The interface MAY explain the demonstrated mismatch.

It MUST NOT invent a mismatch that the system did not observe.

### 17.9 RANGE_READY

ENKI may present the comparable interval/distribution and descriptive position where authorized.

It MUST explicitly preserve the distinction between statistical description and decision.

It MUST NOT emit normative classification.

### 17.10 DECISION_READY

ENKI MAY provide an economic classification only when the complete set of required invariants is valid.

The human conclusion MUST precede the classification.

---

## 18. Result hierarchy

For an economic result, the conceptual hierarchy SHOULD be:

1. human conclusion;
2. secondary classification, only when authorized;
3. user's price with complete economic identity;
4. evidence summary;
5. material limitations;
6. visualization, when valid;
7. useful next action;
8. progressive lineage and methodology detail.

A material limitation that changes decisional meaning MUST be elevated above optional detail.

---

## 19. Evidence and provenance contract

The interface MUST distinguish:

- observations;
- independent providers;
- sources/documents.

These terms are not interchangeable.

A count alone does not prove representativeness or independence.

The experience SHOULD provide a concise evidence summary first and deeper lineage progressively.

When evidence is:

- weak;
- conflicted;
- stale;
- incomplete;
- limiting;

the relevant limitation MUST be elevated with the conclusion.

---

## 20. Temporal contract

The interface MUST distinguish where available:

- query date;
- observation date;
- temporal state;
- historical/current relationship;
- temporal mismatch.

"Current" or "reproducible" MUST NOT be presented unless supported for that response.

Unknown temporal state MUST remain unknown.

Historical evidence and current scope MUST NOT be silently combined as comparable.

---

## 21. Economic visualization contract

Visualization is subordinate to evidence and state.

A chart MUST NOT create meaning the underlying data does not authorize.

For benchmark/range visualization:

- a value below observed minimum MUST remain visibly below/outside;
- a value above observed maximum MUST remain visibly above/outside;
- visual clamping MUST NOT make an exterior value appear equal to an observed endpoint;
- Q1–Q3 MUST NOT be labeled or framed as a fair/recommended range by default;
- geometry MUST NOT imply distribution density that was not measured;
- exact coordinates MUST NOT imply statistical stability.

If the visualization cannot safely represent the data, ENKI SHOULD omit the misleading graphic while preserving valid textual information.

A valid user price MUST NOT disappear only because the graph cannot render safely.

---

## 22. Clarification and correction contract

Correction MUST preserve the original observation.

A specific missing datum SHOULD have a specific correction path.

ENKI MAY use a structured control when:

- the domain options are genuinely closed or sufficiently defined;
- the control reduces user effort;
- the original text remains preserved;
- the choice is accessible.

ENKI MUST NOT convert the primary interaction into a mandatory pre-analysis questionnaire.

---

## 23. Current-request integrity

Only the currently authoritative request MAY update the visible result or error state.

If multiple requests are active, late responses MUST NOT overwrite a newer result.

The visible result SHOULD remain clearly associated with the user text it analyzes.

---

# LAYER 3 — DESIGN DIRECTION

## 24. Baseline V1

Baseline V1 remains the approved visual direction.

Preserve its qualities:

- restrained premium/editorial character;
- high legibility;
- evidence-centered hierarchy;
- warm neutral surface;
- dark ink/teal identity;
- differentiated user-price accent;
- calm and rigorous tone.

Baseline V1 is a visual reference, not automatic proof of functionality.

Its:

- illustrative numbers;
- dates;
- counts;
- navigation;
- mobile orientation;
- methodology controls;
- history controls;
- exact typography count;

MUST NOT be copied as runtime fact or functional requirement without independent support.

---

## 25. Visual hierarchy

The visual system SHOULD reinforce:

**conclusion → price/position → evidence → limitations → detail**

The interface SHOULD avoid excessive generic carding when grouping does not add semantic value.

Aesthetic hierarchy MUST remain subordinate to epistemic hierarchy.

---

## 26. Typography

The exact number of type families is not a normative MVP requirement.

The system MUST prioritize:

- legibility;
- consistent hierarchy;
- performance;
- accessibility;
- brand coherence.

One-, two- or three-family configurations MAY be evaluated without changing the Rector.

---

## 27. Color and meaning

Color MAY reinforce state.

Color MUST NOT be the sole carrier of material meaning.

Warnings, uncertainty, comparison state and decisions MUST also use words, structure or other accessible cues.

Rendered contrast MUST be measured where normative contrast applies.

---

## 28. Primary product jobs

The primary MVP job is:

> Tengo una cotización/precio → la pego → Enki me ayuda a decidir.

The secondary job is:

> Quiero saber cuánto debería costar algo → describo el servicio → Enki me orienta.

The first job SHOULD remain the primary interaction priority unless product evidence supports changing that hierarchy.

---

## 29. Navigation

The MVP does not require persistent or bottom navigation.

It MUST provide clear routes to:

- begin a new query;
- return to the current query/result;
- access actual available capabilities.

Persistent navigation SHOULD only be introduced when real destinations and repeated user need justify it.

A destination shown in a visual reference is not sufficient justification.

---

## 30. Mobile-first

Mobile-first means the main decision path MUST remain understandable and operable under constrained viewport conditions.

On mobile, ENKI MUST preserve the comprehension of:

1. conclusion;
2. material limitation;
3. essential evidence;
4. next action.

The Rector does not prescribe:

- bottom navigation;
- horizontal rail;
- floating CTA;
- keyboard-sensitive CTA movement;
- any specific native interaction pattern.

These require executed validation.

---

## 31. Content and tone

ENKI SHOULD sound:

- close;
- clear;
- nontechnical;
- rigorous;
- calm.

ENKI MUST NOT make uncertainty sound more certain merely to improve confidence or conversion.

Prefer language describing what is actually observed.

Terms such as:

- market;
- current;
- real;
- reproducible;
- confidence;

MUST only be used when their meaning is defined and supported for the response.

Internal enums and implementation jargon SHOULD be translated into human language.

---

## 32. Design conflict rule

When a design decision creates conflict between:

- speed;
- reduced friction;
- visual impact;
- novelty;

and:

- user intent;
- comparability;
- provenance;
- temporal integrity;
- epistemic safety;
- accessibility;

the second group prevails.

---

# LAYER 4 — V2 CHALLENGER / EXPERIMENTATION

## 33. Experimental boundary

Ideas without sufficient evidence MUST remain explicitly classified as:

- `V2_CHALLENGER`;
- `EXPERIMENT`;
- `VALIDATION_NEEDED`.

Trend is not evidence.

Preference is not evidence.

Popularity of a UI pattern is not evidence.

---

## 34. Current V2 hypotheses

The following remain experimental and MUST NOT silently become MVP requirements:

- adaptive checkpoint that skips review in apparently clear cases;
- bottom or persistent mobile navigation;
- final typography-family count;
- rich structured correction controls;
- alternative provenance disclosure density;
- automatic provenance expansion;
- alternative mobile benchmark presentation;
- keyboard-aware CTA behavior;
- richer temporal visualization.

---

## 35. Promotion rule

A design hypothesis may become a normative requirement only when:

1. the product question is explicit;
2. a testable hypothesis exists;
3. success criteria are defined;
4. epistemic and accessibility guardrails remain intact;
5. representative tasks/states are tested;
6. the result is reproducible;
7. benefit justifies added complexity.

---

## 36. What does not count as validation

The following are insufficient on their own:

- designer preference;
- founder preference;
- trend adoption;
- visual similarity to another product;
- single screenshot;
- mockup;
- fixture;
- isolated mocked test;
- "looks better";
- "feels more modern";
- predicted mobile behavior not executed on devices.

---

## 37. Experimental safety

An experiment is invalid if it improves its target metric by weakening a Rector invariant.

A variant MUST NOT:

- convert UNKNOWN into certainty;
- turn RANGE_READY into recommendation;
- hide a material limitation;
- lose original intent;
- reduce critical accessibility;
- create visual confidence beyond epistemic confidence.

---

# LAYER 5 — VALIDATION AND GOVERNANCE

## 38. Evidence hierarchy for validation

Product claims MUST name the level actually demonstrated.

Relevant levels include:

1. static inspection;
2. unit test;
3. mocked test;
4. integration test;
5. accessibility test;
6. responsive/device test;
7. runtime observation;
8. production observation.

A lower level MUST NOT be described as automatic proof of a higher one.

---

## 39. MVP acceptance gates

Where applicable, a change affecting the main economic path SHOULD validate:

- semantic state;
- copy permitted by state;
- price economic identity;
- provenance;
- temporal semantics;
- UNKNOWN / AMBIGUOUS / CONFLICTED behavior;
- RANGE_READY vs DECISION_READY separation;
- exterior benchmark values;
- degenerate/invalid distributions;
- clarification continuity;
- correction without intent loss;
- current-request race behavior;
- focus;
- keyboard use;
- error association;
- status communication;
- rendered contrast;
- reflow;
- text enlargement;
- graphical text alternative.

---

## 40. Accessibility claims

WCAG 2.2 AA is the internal target floor.

Static analysis may identify risks but does not constitute global conformance.

Global accessibility claims require executed validation appropriate to the claim.

---

## 41. Responsive and device claims

A responsive stylesheet or mockup does not demonstrate responsive usability.

Before making device-specific claims, representative states SHOULD be exercised for:

- narrow viewport/reflow;
- zoom or text enlargement;
- spacing;
- interactive target usability;
- relevant virtual-keyboard behavior;
- representative real devices when the claim depends on device behavior.

---

## 42. Brownfield first

ENKI design implementation follows:

**Brownfield first → TDD → RED → GREEN → REFACTOR**

Design work MUST NOT authorize broad rewrites merely for aesthetic consistency.

Implementation SHOULD:

- preserve working domain behavior;
- make one causal change at a time;
- use focused tests before broad suites;
- avoid unrelated cosmetic refactors;
- retain reversibility and auditability.

---

## 43. Reversibility and traceability

A material UX decision SHOULD be traceable to:

- the Rector rule that authorizes it;
- the evidence motivating it;
- the state family affected;
- unresolved hypotheses;
- tests validating behavior;
- a reversible implementation boundary where practical.

---

## 44. Changing the Design Rector

The Rector may evolve, but MUST NOT change implicitly through implementation.

Changing a normative invariant or UX contract requires:

1. identifying the affected rule;
2. presenting new evidence;
3. explaining why the current rule is insufficient or incorrect;
4. evaluating downstream states and contracts;
5. recording the decision;
6. updating dependent specifications and tests.

An implementation shortcut does not amend the Rector.

---

## 45. Relationship to future work

The Design Rector defines:

**what must be true.**

A product/design specification defines:

**what concrete change will be built.**

An implementation plan defines:

**how that change will be built and verified.**

A specification MUST NOT silently reopen a normative Rector decision.

If a project requires changing the Rector, that change must be explicit and reviewed first.

---

# SOURCE BASIS

This Rector draft is derived from the completed ENKI Design Council process and must be interpreted together with the governing `ENKI_ARCHIVO_RECTOR.md`.

Primary adjudicated inputs:

- `CROSS_CRITIQUE_FINDINGS.md`
- `CONTRADICTION_REGISTER.md`
- `RETRACTIONS_AND_FALSE_POSITIVES.md`
- `MVP_PRIORITIES_ADJUDICATED.md`
- `V2_CHALLENGER_HYPOTHESES.md`
- `DESIGN_RECTOR_INPUTS.md`
- `ENKI_BASELINE_V1_APPROVED.png`

Round 2 evidence handling rules remain applicable:

- consensus is not truth;
- reproducible evidence outranks preference;
- important minority findings are retained when strongly supported;
- unsupported production/runtime claims remain unverified;
- visual preference is not an epistemic or accessibility requirement.

---

# CANONICAL STATUS

This document is the canonical ENKI Design Rector approved on 2026-10-01.

It governs subsequent ENKI UX/UI specifications and implementation plans subject to `ENKI_ARCHIVO_RECTOR.md`.

It does not:

- implement product changes;
- change backend semantics;
- certify production behavior;
- certify WCAG conformance;
- promote V2 hypotheses into MVP requirements.

Any normative change to this Rector must follow the governance process defined in this document.