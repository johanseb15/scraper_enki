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

## Conexión semántico-económica shadow

Una conexión semántico-económica significa que una observación ya entendida
queda vinculada, de forma read-only, con filas de evidencia económica y que
cada vínculo declara si la evidencia es comparable o por qué fue excluida.
No significa que el significado semántico sea evidencia de precio, ni que el
puente recomiende un precio, promocione conocimiento o cambie las respuestas
públicas de pricing/API.

La comparabilidad se calcula conservadoramente sobre la evidencia observada.
Para servicios exige el mismo servicio canónico, alcance de mercado y
geografía compatibles, moneda publicada idéntica, cadencia explícita idéntica
y contexto comercial compatible. Para hardware exige permanecer dentro de la
frontera de hardware y de la misma familia; un sistema multicomponente no se
compara con un componente. Bundles no se descomponen. La fila objetivo se
preserva como candidata excluida, pero no cuenta como evidencia independiente
de sí misma.

La readiness económica del shadow no reutiliza `READY_FOR_PRICING`: esa señal
sólo indica que una ruta y su mercado permiten hacer una consulta. `READY`,
`PARTIAL` e `INSUFFICIENT` se calculan después del filtrado de comparabilidad y
consideran cantidad de filas, providers independientes y dispersión. Los
estados semánticos `AMBIGUOUS` y `UNKNOWN` permanecen explícitos y prevalecen;
tres precios no comparables no producen readiness.

La evidencia excluida es dato. El artefacto conserva evidence id, provider,
reasons, dimensiones faltantes, incertidumbre y ambos canales de provenance.
Esto permite que futuros ciclos de aprendizaje apunten a gaps reales sin
reescribir la fuente ni convertir ausencia de conocimiento en certeza.

Shadow precede a runtime porque primero deben observarse distribuciones,
conflictos y gaps sobre evidencia real. Sólo una validación posterior puede
autorizar que este contexto influya en decisiones públicas; el bridge actual
no tiene superficie de persistencia ni integración con el pricing público.

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
