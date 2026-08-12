# Enki Project Status

Este documento captura el estado estable del proyecto despues de la reorganizacion Sprint 0. La fuente estrategica superior sigue siendo `README.md`; este archivo resume conocimiento operativo y de research que no debe depender de `.tmp_analysis/`.

## 1. Donde esta el proyecto hoy

Enki esta enfocado en reducir incertidumbre economica al comprar, vender o contratar tecnologia. El producto principal es **Enki Decision**: ayudar a responder cuanto cobrar o pagar por trabajos tecnologicos, servicios, productos y hardware.

El cuello de botella actual es **Economic Evidence Acquisition**: encontrar observaciones economicas reales, trazables y comparables. El corpus de procurement sirve para lenguaje, demanda y contexto, pero no reemplaza evidencia comercial comparable.

## 2. Baseline tecnico validado

FACT:

```text
branch: main
baseline reorganizacion: 4f648323d15b0e3a7a840a16548668fa350f15de
backend: 252 tests GREEN
frontend: lint GREEN
frontend: 9 tests GREEN
frontend: build GREEN
```

## 3. Capacidades validadas

FACT:

- Pipeline comercial con `Scraper -> Parser -> OfertaDTO -> Procesador -> Normalizadores -> OfertaFactory -> Dominio -> Repositorio -> SQLite`.
- Persistencia comercial idempotente.
- `PrecioValor` preserva valor, moneda y periodo.
- `Oferta.precio` usa el contrato de dominio economico correcto.
- Repositorios SQLite rechazan schemas legacy incompatibles antes de mutar datos.
- Pipeline de raw/evidence preserva documentos y observaciones tipadas sin convertir todo en `Oferta`.
- Frontend actual valida el flujo modular de decision con 9 tests.

## 4. Dataset local disponible

FACT:

El principal data asset local es:

```text
enki_argentina_procurement_sprint4.db
```

No se versiona en Git y debe preservarse como activo local reproducible desde fuentes oficiales.

Counts validados:

| Recurso | Filas aceptadas |
|---|---:|
| SIByS | 212742 |
| Adjudicaciones | 205299 |
| Convocatorias | 128951 |
| SIPRO | 73785 |
| **Total** | **620777** |

Ademas:

- 621462 filas examinadas.
- 685 filas SIPRO rechazadas por falta de identidad estable.
- 4 raw documents oficiales preservados.
- 181568107 bytes raw.
- Integridad de hashes raw sin mismatches en la reconstruccion validada.

## 5. Universo tecnologico Argentina procurement

FACT:

- 14941 adjudicaciones contienen el token exacto `INFORMATICA;`.
- Esas adjudicaciones corresponden a 5190 procesos unicos.
- El join deterministico `Adjudicaciones.Numero_Proceso` con `Convocatorias.Numero_Proceso` cubrio 14941/14941 casos.
- `Nombre_del_Proceso` estuvo presente en 14941 casos.
- `Objeto_del_Proceso` estuvo presente en 14940 casos.

## 6. Que aprendimos

FACT:

El corpus tecnologico de procurement es util para:

- lenguaje de mercado;
- vocabulario real;
- demanda observada;
- compradores y proveedores;
- contexto contractual;
- descubrimiento de objetos economicos candidatos.

FACT:

La shortlist observada de lenguaje pricing-first fue:

Servicios:

- Instalacion
- Configuracion
- Reparacion
- Soporte tecnico

Productos:

- Monitores
- Notebooks
- Impresoras
- Cartuchos de toner
- Switches
- Routers

FACT:

El analisis temporal de observaciones con formas explicitas de instalacion uso 276 registros y produjo esta distribucion:

| Clasificacion analitica | Registros |
|---|---:|
| PRODUCT_PLUS_INSTALLATION | 159 |
| PROJECT_OR_SOLUTION | 81 |
| UNKNOWN | 29 |
| LABOR_DOMINANT | 7 |

FACT:

Bajo ese analisis, `instalacion` aparece mayormente como componente de compras con bienes/materiales o proyectos mas amplios, no como servicio laboral puro.

ANALYTIC_INFERENCE:

Procurement probablemente no sea suficiente como fuente primaria para pricing comparable de servicios. Puede orientar lenguaje y targets, pero la evidencia de precios debe buscarse en fuentes comerciales reales.

ANALYTIC_INFERENCE:

Seguir clasificando procurement no es la prioridad inmediata si la pregunta de producto es cuanto cobrar o pagar. La siguiente incertidumbre debe reducir el riesgo de adquisicion economica comparable.

## 7. Que no esta resuelto todavia

FACT:

No existe todavia un pipeline productivo completo de pricing internacional.

FACT:

No existe todavia un pricing engine final que produzca rangos confiables para usuarios finales.

FACT:

No existe todavia una taxonomia productiva definitiva para todos los servicios y productos tecnologicos.

FACT:

No se valido aun que los primeros objetos candidatos tengan suficiente precio publico comercial comparable.

TEMPORARY_HYPOTHESIS:

Algunos targets derivados de procurement, como instalacion de UPS, camaras de seguridad, red WiFi, switches o telefonos IP, pueden servir como candidatos para investigacion comercial. Esa hipotesis requiere validacion con fuentes comerciales reales antes de convertirse en producto.

## 8. Cuello de botella actual

FACT:

El cuello de botella actual es **Economic Evidence Acquisition**.

El problema no es acumular mas scraping ni mas filas. El problema es conseguir observaciones con:

```text
source_url
provider
retrieved_at
economic_object
price_raw
currency
pricing_unit
scope
location
included/excluded semantics
```

## 9. Siguiente incertidumbre de producto

La siguiente incertidumbre debe ser:

> Que objeto economico tecnologico tiene suficiente evidencia comercial publica, trazable y comparable para sostener una primera respuesta de Enki Decision?

La investigacion debe medir evidencia adquirible, no intuicion de categoria ni frecuencia en procurement.

## 10. Estado de research temporal

`.tmp_analysis/` fue usado como scratchpad local para radiografias, JSONL y rankings. Los hallazgos estables fueron promovidos aqui de forma resumida y rotulada como FACT, ANALYTIC_INFERENCE o TEMPORARY_HYPOTHESIS.

Los JSONL, rankings largos y reportes intermedios no son producto ni fuente operacional. Deben regenerarse cuando haga falta desde DBs y scripts/metodologia vigentes, no depender de ellos como documentacion estable.
