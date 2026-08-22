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

## Economic Evidence Dimensions

La comparabilidad económica se apoya en dimensiones tipadas y trazables. Cada
dimensión conserva su valor, la evidencia que lo sostiene, provenance y una
condición epistemológica explícita: `OBSERVED`, `INFERRED`, `UNKNOWN`,
`CONFLICTED` o `AMBIGUOUS`. Una inferencia compatible puede acompañar a una
observación, pero nunca la reemplaza ni borra su origen.

Economic Dimension Semantics v2 declara cardinalidad y compatibilidad por
dimensión. Provider, moneda, cadencia, modalidad y bundle son escalares;
hardware/materiales son booleanos; commercial context y device scope son sets;
location es estructurada; geographic reach es jerárquica pero se compara de
forma exacta y conservadora hasta disponer de reglas comerciales demostradas.
No existe una igualdad genérica correcta para todos estos contratos.

Orthogonal dimensions do not conflict merely because their values differ.
`delivery_mode=REMOTE` y `geographic_reach=NATIONAL` pueden coexistir: REMOTE
no implica NATIONAL y NATIONAL no implica REMOTE. Location (`country`,
`province`, `city`) es un tercer eje y nunca recibe provincia por default.

Multiple compatible claims are not ambiguity. `URGENCY + AFTER_HOURS` y
`URGENCY + WEEKEND_HOLIDAY` son sets válidos. `AMBIGUOUS` queda reservado para
interpretaciones escalares mutuamente excluyentes que la evidencia no permite
resolver; `CONFLICTED` preserva desacuerdos entre claims de fuentes semánticas
distintas. UNKNOWN no se transforma en conjunto vacío ni en valor estándar.

La provenance de un claim distingue `RAW_SOURCE_OBSERVATION`,
`NORMALIZED_FIELD`, `REGISTRY_CLAIM` y `DERIVED_CLAIM`. Una columna del artefacto
normalizado no se etiqueta como publicación raw aunque conserve trazabilidad
hacia su observación de origen.

La identidad independiente de provider se cuenta mediante un `provider_id`
estable derivado del nombre exacto declarado en el registro de fuentes, no por
cantidad de filas, URL ni fuzzy matching. El identificador preserva también el
nombre y `source` originales y su provenance. Si el provider no puede
demostrarse, permanece `UNKNOWN`; si registro y evidencia difieren, queda
`CONFLICTED`.

El enriquecimiento histórico vive en un sidecar versionado por
`observation_id`. Es determinístico, idempotente, regenerable y read-only: no
reescribe la normalización semántica ni la evidencia raw. Sus dimensiones
pueden ser consumidas por el bridge en shadow manteniendo compatibilidad con
entradas anteriores. El sidecar v1 permanece inmutable; v2 se genera como un
artefacto separado y un loader versionado concentra la compatibilidad de
migración sin dispersar condiciones de schema por el dominio.

La integración de dimensiones debe validarse primero en shadow. Un conflicto
reduce comparabilidad/readiness; `UNKNOWN` no se completa con defaults; remoto
no demuestra cobertura nacional; moneda no se convierte; bundles, hardware y
materiales no se estiman ni descomponen. Sólo una evaluación posterior puede
autorizar influencia sobre runtime o API pública.

La ubicación del provider no es el alcance del servicio. La modalidad remota
no es cobertura nacional. La unidad cobrada debe estar evidenciada por texto o
campo estructurado de la fuente y nunca inferirse sólo porque existe un precio.
Los claims extraídos conservan raw basis, documento, método y versión: incluso
cuando el texto fuente es explícito, el parser sigue siendo una interpretación
auditable y puede entrar en conflicto con otros claims sin borrarlos.

Antes de adquirir otra vez una fuente se reprocesa la evidencia raw existente.
Una URL sin documento reproducible no constituye lineage raw; permanece
`UNKNOWN` con razón de no linkage. La reacquisition es selectiva y posterior al
gap register, no un scraping indiscriminado para fabricar cobertura.

La adquisición se prioriza por ganancia esperada de información para la
decisión económica, con un score determinístico y explicable que sólo ordena
trabajo operativo. El valor esperado se contrasta después con el unlock real;
encontrar cero evidencia también es un outcome auditable y nunca habilita una
inferencia.

Un precio histórico y un scope observado en una versión actual no son
automáticamente evidencia comparable. Sólo pueden combinarse cuando la
identidad exacta de la oferta demuestra compatibilidad temporal; en caso
contrario se registra `TEMPORAL_MISMATCH`.

El contexto de una fuente o página no se aplica a una oferta sin atribución
inequívoca. Footer, shipping, ubicación del provider o una sección ambigua no
demuestran reach, inclusiones ni condiciones de una oferta particular.

Los gaps de comparabilidad son bilaterales, no locales a una observación. Un
claim conocido de un lado no resuelve el `UNKNOWN` del otro, y un minimal
unlock set debe enumerar cada claim requerido con su oferta de pertenencia.

El valor de adquisición se mide por unlock de pares y del cohort, no por
cantidad de campos completados. Ninguna adquisición de red se ejecuta sin
valor contrafactual positivo para una decisión, salvo una auditoría diagnóstica
explícita y trazable.

La ubicación del provider no participa como proxy de compatibilidad geográfica
cuando existe la dimensión `geographic_reach`. Para servicios onsite, reach
desconocido continúa siendo evidencia insuficiente; ubicaciones distintas no
son por sí mismas un mismatch comercial.

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
