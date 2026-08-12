# Arquitectura de Enki

`README.md` es la fuente de orientacion estrategica de mayor nivel. Esta arquitectura describe el sistema real actual y sus limites: Enki existe para ayudar a decidir cuanto cobrar o pagar por trabajos, servicios y hardware tecnologico con evidencia comparable, trazable y reciente.

El cuello de botella actual del producto es **Economic Evidence Acquisition**: descubrir y preservar observaciones economicas utiles. Procurement, normalizacion, scraping y frontend son capacidades habilitadoras, no fines en si mismas.

## Jerarquia de producto

- **Primary: Enki Decision.** Responde si un precio de trabajo, servicio, producto o hardware es bajo, razonable o alto.
- **Secondary: Enki Market.** Usa el mismo corpus para inteligencia de mercado: proveedores, compradores, demanda, recurrencia y lenguaje.
- **Future: Enki Data.** API, datasets, feeds e integraciones, cuando exista evidencia suficiente para sostenerlos.

## Pipelines actuales

### A. Commercial Pricing Pipeline

Este pipeline produce `Oferta` comercial cuando la fuente expresa una oferta de precio comparable.

```text
Scraper
  -> Parser
  -> OfertaDTO
  -> Procesador
  -> Normalizadores
  -> OfertaFactory
  -> Dominio
  -> Repositorio (Protocol)
  -> SQLite
```

Responsabilidad principal: preservar precio raw/canonico, moneda, periodo, proveedor, fuente y semantica suficiente para comparar ofertas comerciales.

### B. Raw / Evidence Pipeline

Este pipeline conserva evidencia que todavia no necesariamente es una oferta comercial.

```text
Fuente
  -> Raw document
  -> Import / extraction
  -> Typed evidence / observation
  -> Evidence repository
```

Responsabilidad principal: preservar `source_url`, `retrieved_at`, `content_hash`, `metadata`, `raw_content`, estado de extraccion y tipo de evidencia.

### C. Procurement / Market Intelligence

Este pipeline usa documentos y datasets publicos para entender lenguaje, demanda, compradores, proveedores y contexto contractual.

```text
Documentos o datasets publicos
  -> Raw preservation
  -> Market observations
  -> Analysis
```

Procurement ensena lenguaje y contexto. No debe tratarse automaticamente como precio comercial comparable.

## Principio de evidencia

> **Not everything is an Oferta.**

Una `Oferta` comercial no es lo mismo que:

- contrato;
- adjudicacion;
- orden de compra;
- raw document;
- market observation;
- provider identity.

No convertir tipos de evidencia solo para simplificar storage. Cada tipo conserva su identidad semantica, su procedencia y sus limites de comparabilidad.

## Moneda y geografia

Politica conceptual de evidencia:

1. Evidencia Argentina en ARS.
2. Evidencia Argentina en USD.
3. Referencia internacional en USD.
4. Conversion monetaria solo como interpretacion explicita.

No mezclar evidencia internacional con evidencia local como si fueran equivalentes. La conversion de moneda no esta implementada como arquitectura productiva; cuando exista, debe ser una capa explicita de interpretacion.

## Estructura real del repositorio

```text
src/
  dominio/
  aplicacion/
  infraestructura/
  normalizadores/
  api/
  configuracion_runtime.py

frontend/
  src/app/
  src/components/
  src/features/

tests/
scripts/
docs/
.tmp_analysis/       # research local temporal, no producto
```

## Guardarrails arquitectonicos

- Brownfield first: leer contratos reales antes de cambiar comportamiento.
- RED -> GREEN -> REFACTOR cuando hay cambios productivos.
- Raw first: la fuente es verdad; la extraccion es interpretacion.
- Preserve raw + canonical.
- Evidence types stay separate.
- Preserve provenance.
- Imports must be idempotent.
- Data quality > volume.
- Comparability > scraping.
- No semantic invention.
- No comparemos precios hasta comparar lo que incluyen.
- 100 registros reales valen mas que 10.000 filas fabricadas.
- No anti-bot bypass.
- SQLite continua hasta que exista un cuello de botella demostrado.

## Foco de sprint

Cada sprint debe eliminar una incertidumbre concreta del producto o una deuda que amenace esa capacidad.

Antes de aprobar un sprint:

> Este trabajo aumenta nuestra capacidad de decir cuanto cobrar o cuanto pagar por algo tecnologico real?

Si la respuesta es no, queda en backlog salvo que desbloquee directamente esa capacidad.

## Futuro explicitamente no implementado

No son arquitectura productiva actual:

- AI classification productiva;
- embeddings;
- PostgreSQL;
- microservices;
- provider graph productivo;
- pricing engine completo;
- estadisticas finales de mercado;
- international pricing pipeline.

Pueden investigarse en el futuro, pero no deben documentarse como existentes.
