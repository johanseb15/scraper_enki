# ENKI — Archivo Rector

## Norte

Enki reduce la incertidumbre económica al comprar, vender
o contratar tecnología.

Enki no analiza sólo precios; detecta necesidades tecnológicas
y las transforma en decisiones económicas comparables.

MVP:

El usuario describe una necesidad tecnológica, con o sin precio,
y Enki determina qué decisiones económicas existen,
cuáles son comparables y cuál parece ser la alternativa más
razonable según evidencia.

## Orden ejecutivo

1. ENTENDER
2. CONECTAR
3. APRENDER
4. EXPLOTAR ECONÓMICAMENTE

### 1. ENTENDER

Todo dato que Enki recopile debe:

- preservarse;
- clasificarse;
- interpretarse;
- relacionarse cuando exista evidencia;
- reutilizarse cuando corresponda;
- o quedar explícitamente UNKNOWN / AMBIGUOUS / CANDIDATE.

Objetivo:

100% de los datos debe tener un estado epistemológico explícito.

Esto NO significa 100% canonicalización.

Nunca inventar significado para mejorar coverage.

### 2. CONECTAR

El conocimiento no debe permanecer aislado entre:

- Provider Normalization
- User Parser
- TechnicalNeed
- Procurement
- Corpus
- Historical mappings
- Evidence

El conocimiento compartido debe reutilizarse cuando el contexto
lo permita.

Pero:

Provider language != User language.
Symptom != Service.
Technical route != Semantic alias.
Semantic truth != Economic evidence.

Primero unificar lectura.
Después automatizar escritura.

### 3. APRENDER

Lifecycle:

observation
→ interpretation
→ candidate
→ evidence
→ conflict check
→ validation
→ promotion
→ runtime

Reglas:

Observation != promoted knowledge.
Candidate != alias.
Candidate != truth.

Enki no puede promocionar sus propias conclusiones sólo porque
él mismo las produjo.

Frequency != independence.

Repeticiones del mismo provider no equivalen a múltiples
fuentes independientes.

Todo conocimiento promovido debe ser:

- trazable
- versionable
- contrastable
- reversible

UNKNOWN != FALSE.

### 4. EXPLOTAR ECONÓMICAMENTE

Después de entender/conectar/aprender:

- construir evidencia comparable;
- densificar cohortes;
- aumentar RANGE_READY;
- alcanzar DECISION_READY;
- emitir decisiones económicas cuando la evidencia lo permita.

Nunca relajar thresholds para crear readiness artificial.

Principio:

No comparemos precios hasta comparar lo que incluyen.

## Data principles

DATA FIRST.
RAW first.

The source is truth;
extraction is interpretation.

The utterance is truth;
semantic mapping is interpretation.

Preservar RAW + canonical.
Provenance obligatoria.
Imports idempotentes.

100 registros reales > 10.000 fabricados.

Data quality > volume.
Comparability > scraping.

No silent bundle decomposition.
No silent currency conversion.
No province defaults.

El corpus enseña el lenguaje;
la evidencia comparable enseña el precio.

## Acquisition

Preferencia:

official API
→ feed/dataset
→ HTTP
→ structured page
→ browser
→ BLOCKED

Nunca:

CAPTCHA bypass
anti-bot evasion
stealth/proxy evasion
verify=False
TLS bypass
datos fabricados

A futuro:

gap
→ acquisition target
→ observation
→ understanding
→ knowledge/evidence
→ gap reevaluation

## Engineering

Brownfield first.
TDD.
RED → GREEN → REFACTOR.
One causal change per sprint.
No cosmetic refactors.
Tests focalizados antes de suite completa.
git diff --check.
Clean-worktree validation.
No git add .
No git add -A.
Stage exact files.
SQLite until a bottleneck proves otherwise.

## Criterio de prioridad

Un sprint debe mejorar al menos uno de:

- porcentaje de datos explícitamente entendidos;
- knowledge reuse;
- UNKNOWN explicados;
- provenance;
- knowledge candidates;
- evidencia comparable;
- decisiones económicas seguras.

Sin empeorar:

- safety;
- provenance;
- comparability;
- reversibility;
- auditability.

## Regla final

Enki nunca debe perder silenciosamente una observación
porque todavía no sabe utilizarla.

Cada dato debe terminar:

UNDERSTOOD
AMBIGUOUS
UNKNOWN
o CANDIDATE

con provenance.
