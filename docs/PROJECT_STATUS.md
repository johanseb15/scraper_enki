# Enki Project Status

Este documento captura el estado operativo actual de Enki antes de iniciar la expansión nacional de fuentes comerciales. `README.md` sigue siendo la fuente estratégica superior; este archivo resume el baseline técnico, las capacidades validadas, los activos de datos y el punto exacto del MVP.

## 1. Producto y norte

Enki reduce la incertidumbre económica al comprar, vender o contratar tecnología.

Producto principal:

> **Enki Decision** — responder: “Voy a cobrar/pagar X por Y. ¿Está bajo, razonable o alto?”

Jerarquía:

1. Enki Decision — prioridad del MVP.
2. Enki Market — inteligencia de mercado sobre el mismo corpus.
3. Enki Data — posible API/datasets/integraciones futuras.

Pregunta de control de cada sprint:

> **¿Este trabajo aumenta nuestra capacidad de decir cuánto cobrar o cuánto pagar por algo tecnológico real?**

## 2. Punto actual del MVP

Estimación funcional de producto:

```text
Producto / norte             100%
Arquitectura                  90%
Persistencia / raw            90%
Adquisición                   80%
Cobertura de fuentes          20%
Normalización                 40%
Comparabilidad                30%
Pricing engine                20%
API Decision                  10%
UX final                      10%

MVP funcional aproximado: 50–55%
```

La estimación mide capacidad de entregar valor al usuario, no cantidad de código.

## 3. Baseline técnico validado

FACT:

```text
branch: main
HEAD: 3b127d40a08f627aa25883bc4fc388b150427ed5
commit: feat(pricing): add generic batch acquisition engine
backend: 288 tests GREEN
warnings: 1 StarletteDeprecationWarning
failures: 0
```

## 4. Arquitectura activa

### A. Commercial Pricing Pipeline

```text
Scraper -> Parser -> OfertaDTO -> Procesador -> Normalizadores -> OfertaFactory -> Dominio -> Repositorio -> SQLite
```

### B. Raw / Evidence Pipeline

```text
Fuente -> Documento RAW -> Hash / provenance -> Extracción -> Observación tipada -> SQLite
```

> **RAW = verdad original. Extracción = interpretación.**

### C. Procurement / Market Intelligence

```text
Datasets / documentos públicos -> RAW -> observaciones de mercado -> análisis
```

Procurement se usa para lenguaje, demanda, proveedores y contexto. No se convierte automáticamente en precio comercial comparable.

> **Not everything is an Oferta.**

## 5. Motor de adquisición masiva

Estado: VALIDADO EN INTERNET REAL.

Componentes actuales:

```text
data/pricing_sources.csv
scripts/collect_pricing_sources.py
src/aplicacion/colector_precios_batch.py
src/aplicacion/pricing_source_registry.py
src/infraestructura/scrapers/generic_price_extractor.py
```

Flujo:

```text
Source Registry
-> Batch Collector
-> Downloader HTTP
-> RAW preservation
-> Generic Price Extractor v2
-> Commercial Price Observation
-> SQLite
```

Regla de escala: no escribir un scraper específico por cada fuente.

## 6. Smoke real del Generic Extractor v2

Primera ejecución:

```text
Sources attempted:       7
Sources succeeded:       7
Sources failed:          0
Raw docs acquired:       7
Raw docs duplicate:      0
Observations extracted:  112
Observations duplicate:  0
Exact prices detected:   112
```

Segunda ejecución:

```text
Sources attempted:       7
Sources succeeded:       7
Sources failed:          0
Raw docs acquired:       1
Raw docs duplicate:      6
Observations extracted:  0
Observations duplicate:  112
Exact prices detected:   112
```

Interpretación:

- adquisición HTTP funcional;
- cambios web generan RAW nuevo;
- no se fabrican nuevas observaciones económicas si la economía no cambia;
- idempotencia económica verificada en condiciones reales.

## 7. Source Registry actual

Fuentes iniciales:

```text
Jadetech
Bitz
BairesCloud
Vida Informatica
REED Technology
CiroWhite Informatica
DMR
```

Cobertura inicial:

```text
Buenos Aires
Córdoba
Tucumán
Mendoza
```

Objetivo:

```text
24 jurisdicciones argentinas
x
mínimo 10 candidatos por jurisdicción
=
>= 240 fuentes candidatas
```

Los 240 son candidatos de discovery/acquisition; no se asume que todos tengan precio público ni que todos sean comparables.

## 8. Embudo de adquisición

```text
DISCOVERED
-> VERIFIED
-> ACQUISITION_ATTEMPTED
-> RAW_ACQUIRED
-> PRICE_DETECTED
-> ECONOMIC_OBSERVATION
-> QUALITY_ACCEPTED
-> COMPARABLE
```

No fijar por anticipado una tasa esperada de conversión.

> **If it is not exported, traceable and importable, it does not count.**

## 9. Generic Price Extractor v2

Responsabilidad actual:

```text
source
provider_raw
source_url
retrieved_at
economic_object_raw
price_raw
price_value
currency_raw
raw_document_id
extractor_version
```

No debe inventar semántica.

Ejemplos reales:

```text
$ 42.120,00 -> 42120 ARS
$40,000     -> 40000 ARS
$110,000    -> 110000 ARS
```

Valores sospechosos publicados por la fuente se preservan; quality/outlier detection pertenece a una capa posterior.

## 10. Scrapers específicos existentes

Se preserva trabajo anterior sobre:

```text
Jadetech
Bitz
BairesCloud
Vida Informatica
CiroWhite
DMR
REED
Venex
CompraGamer
```

Rol futuro: fallback/override cuando la extracción genérica no alcance.

## 11. Dataset Argentina Procurement

Activo local reproducible:

```text
enki_argentina_procurement_sprint4.db
```

Counts históricos validados:

| Recurso | Filas aceptadas |
|---|---:|
| SIByS | 212742 |
| Adjudicaciones | 205299 |
| Convocatorias | 128951 |
| SIPRO | 73785 |
| **Total** | **620777** |

Además:

- 621462 filas examinadas.
- 685 SIPRO rechazadas por falta de identidad estable.
- 4 documentos raw oficiales preservados.
- 181568107 bytes raw.
- 14941 adjudicaciones con `INFORMATICA;`.
- 5190 procesos únicos.
- join Adjudicaciones -> Convocatorias: 14941/14941.

## 12. Rol actual de Procurement

Sirve para lenguaje, vocabulario, demanda, categorías, proveedores y contexto contractual.

No ha demostrado ser fuente suficiente de precios comparables de servicios.

> **El corpus enseña el lenguaje; la evidencia comparable enseña el precio.**

## 13. Human Language Evidence

Research paralelo útil para normalización futura, vocabulario espontáneo, intención de compra/venta y scopes.

No bloquea Mass Acquisition.

Cualquier dataset debe ser exportable, traceable e importable antes de contarse como activo.

## 14. Normalización

Hay normalizadores existentes para servicios, precios, empresas y ubicaciones.

No representan todavía la taxonomía definitiva de Enki.

```text
adquirir corpus real
-> observar lenguaje de mercado
-> derivar objetos canónicos
-> conservar raw + canonical
```

## 15. Comparabilidad

Estado: PARCIAL / NO CERRADO.

La comparabilidad futura debe considerar dimensiones como:

```text
objeto
dispositivo
sistema operativo
backup
drivers
programas
licencia
modalidad
ubicación
included/excluded semantics
```

## 16. Pricing Engine

Estado: NO CERRADO PARA MVP.

Debe producir:

```text
rango observado
mediana
dispersión
N observaciones
N proveedores
geografía
frescura
fuentes
confidence
```

y finalmente clasificar:

```text
LOW
REASONABLE
HIGH
```

## 17. API Decision

Todavía no existe el endpoint final.

Objetivo conceptual:

```text
POST /decision
```

Entrada: descripción, precio, moneda, ubicación.

Salida: decisión, rango, mediana, muestra, proveedores, confidence, fuentes y explicación.

## 18. Frontend

Existe frontend modular, pero no es cuello de botella actual.

La UX MVP debe ser simple:

```text
describir qué se quiere evaluar
+ precio
+ ubicación
-> analizar
-> resultado
-> evidencia
```

## 19. Testing

Baseline:

```text
288 passed
1 warning
0 failed
```

Metodología:

> **RED -> GREEN -> REFACTOR**

## 20. Guardarrails activos

> DATA FIRST.

> Raw first.

> The source is truth; extraction is interpretation.

> Preserve provenance.

> Evidence types stay separate.

> Imports must be idempotent.

> Data quality > volume.

> Comparability > scraping.

> Preserve raw + canonical.

> No semantic invention.

Adquisición:

```text
official API
-> official feed/dataset
-> HTTP
-> structured page
-> browser
-> BLOCKED
```

Nunca anti-bot bypass, CAPTCHA solving, stealth evasion, proxies para eludir protecciones ni datos inventados.

## 21. Roadmap congelado hacia MVP

```text
FASE 1 — MASS ACQUISITION
  >=240 candidatos
  24 jurisdicciones
  corpus nacional

FASE 2 — CORPUS AUDIT
  fuentes
  proveedores
  objetos
  precios
  ruido
  calidad

FASE 3 — LANGUAGE NORMALIZATION
  raw -> canonical

FASE 4 — COMPARABILITY
  scopes comparables
  cohortes

FASE 5 — PRICING ENGINE
  rango
  mediana
  muestra
  confidence

FASE 6 — ENKI DECISION
  X por Y -> LOW / REASONABLE / HIGH

FASE 7 — MVP UI
  input simple
  resultado
  evidencia
```

## 22. No prioridad antes del MVP

```text
PostgreSQL
Kafka
Redis
microservices
Kubernetes
embeddings
vector DB
AI classification productiva
provider graph complejo
dashboard avanzado
app mobile
pricing internacional completo
taxonomía exhaustiva
refactors cosméticos
```

SQLite continúa hasta un cuello de botella demostrado.

## 23. Sprint activo

### Sprint 2.0C — Mass Acquisition / Argentina Source Discovery

Objetivo:

> construir una red nacional de fuentes candidatas de precios tecnológicos y medir empíricamente la densidad de evidencia económica pública adquirible.

Primera tanda:

```text
CABA
Buenos Aires
Córdoba
Santa Fe
```

Objetivo por jurisdicción:

```text
>=10 candidatos reales y verificables
```

Después:

```text
Source Registry v2
-> discovery
-> acquisition
-> raw preservation
-> price extraction
-> funnel measurement
```

## 24. Punto de control

```text
MVP funcional estimado: 50–55%

Motor de adquisición base: READY
Generic Extractor v2: READY
SQLite/provenance: READY
Idempotencia live: VERIFIED
Suite: 288 GREEN
Cobertura nacional: NOT YET
Normalización final: NOT YET
Comparabilidad final: NOT YET
Pricing Engine: NOT YET
Decision API: NOT YET
MVP UI: NOT YET
```

Cuello de botella inmediato:

> **Cobertura y densidad de evidencia económica comercial real.**
