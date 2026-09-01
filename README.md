# Enki

> **Enki reduce la incertidumbre económica al comprar, vender o contratar tecnología.**

Enki es una plataforma de inteligencia de precios tecnológicos orientada a decisiones reales. Su objetivo principal es poder responder, con evidencia trazable y sin inventar precisión:

- **“¿Cuánto debería cobrar por este trabajo?”**
- **“¿Está bien el precio que me están cobrando?”**
- **“¿Está bien el precio de esta PC / hardware?”**

El producto debe funcionar tanto para **servicios tecnológicos** como para **productos y hardware**, priorizando evidencia local en Argentina y usando referencias internacionales en USD cuando la muestra local no sea suficiente.

---

## 1. Misión

Ayudar a personas, técnicos, freelancers, comercios y empresas a tomar mejores decisiones económicas sobre tecnología mediante precios reales, comparables, recientes y trazables.

Enki no debe limitarse a mostrar precios. Debe explicar:

- qué se está comparando;
- qué incluye y qué no;
- cuál es la muestra disponible;
- qué tan reciente es;
- de dónde proviene;
- y cuánta confianza merece la respuesta.

---

## 2. Visión

Construir una plataforma donde una persona pueda escribir en lenguaje natural:

> “Voy a cambiar Windows 10 por Windows 11, hacer backup y reinstalar programas. ¿Cuánto debería cobrar?”

o:

> “Me ofrecen una PC con Ryzen 7, 32 GB de RAM, RTX 5070 y SSD de 1 TB a $X. ¿Está bien el precio?”

y recibir una respuesta responsable basada en evidencia real:

- rango observado;
- mediana y dispersión cuando la muestra lo permita;
- cantidad de observaciones;
- cantidad de proveedores;
- ubicación;
- fecha/frescura;
- fuentes;
- dimensiones que afectan el precio;
- incertidumbre explícita.

Cuando la evidencia argentina no alcance, Enki podrá aportar **referencias internacionales en USD**, siempre separadas de la evidencia local y sin convertirlas silenciosamente en un “precio argentino”.

---

## 3. Producto principal

### Enki Decision

Es el núcleo del proyecto.

Pregunta central:

> **“Voy a cobrar/pagar X por Y. ¿Está bajo, razonable o alto?”**

Para responder, Enki necesita:

```text
objeto económico entendido
        +
evidencia de precios reales
        +
comparabilidad semántica
        +
trazabilidad
        +
frescura
        +
incertidumbre explícita
```

Dos casos prioritarios:

### Servicios

Ejemplos:

- instalación o cambio de sistema operativo;
- formateo;
- backup;
- limpieza y mantenimiento;
- diagnóstico;
- reparación;
- instalación de SSD/RAM;
- armado de PC;
- soporte remoto;
- visita técnica;
- configuración de Wi‑Fi/router.

### Productos / hardware

Ejemplos:

- PCs armadas;
- notebooks;
- CPU;
- GPU;
- RAM;
- SSD;
- motherboards;
- fuentes;
- monitores;
- routers y switches.

Para hardware, la comparación debe considerar especificaciones, condición, garantía, stock y componentes incluidos. Un nombre comercial genérico no alcanza.

---

## 4. Productos secundarios

### Enki Market

Inteligencia de mercado construida sobre el mismo corpus:

- proveedores;
- compradores;
- contratos;
- demanda;
- recurrencia;
- lenguaje de mercado;
- estructura competitiva.

Es una capacidad valiosa, pero **no reemplaza al producto principal**.

### Enki Data

Posible línea futura:

- API;
- datasets;
- research feeds;
- integraciones.

No es prioridad del MVP.

---

## 5. Norte permanente del proyecto

Antes de aprobar cualquier sprint se debe responder:

> **¿Este trabajo aumenta nuestra capacidad de decir cuánto cobrar o cuánto pagar por algo tecnológico real?**

Si la respuesta es no, va a backlog salvo que elimine un riesgo técnico que bloquee directamente esa capacidad.

La ejecución del programa está gobernada por:

docs/ENKI_ARCHIVO_RECTOR.md

Orden ejecutivo vigente:

1. ENTENDER
2. CONECTAR
3. APRENDER
4. EXPLOTAR ECONÓMICAMENTE

La adquisición y explotación económica no deben adelantarse a las etapas anteriores ni usarse para fabricar readiness.

---

## 6. Estado actual

El estado técnico no se fija mediante SHA o conteos de tests escritos a mano. Se verifica contra el repositorio actual.

Desde la raíz:

    git rev-parse HEAD
    git status --short
    python -m pytest -q

Frontend:

    cd frontend
    pnpm exec tsc --noEmit
    pnpm test -- --run
    pnpm build

Runtime público actual:

- API FastAPI;
- endpoint POST /decision/pricing;
- contrato explícito DecisionPricingResponse;
- interpretación semántica, resolución de mercado, readiness y evidence probe;
- evidencia económica fail-closed cuando no existe soporte admisible.


### Integridad técnica cerrada

Ya están protegidos:

- `PrecioValor` conserva valor, moneda y período;
- `Oferta.precio` usa el contrato de dominio correcto;
- persistencia comercial idempotente;
- una adquisición repetida no fabrica nuevas observaciones;
- schemas SQLite legacy incompatibles fallan antes de mutar datos;
- política única de ruta para la DB runtime de ofertas;
- migraciones brownfield compatibles preservadas.

### Dataset Argentina Procurement

Activo local reproducible, no versionado en Git:

```text
enki_argentina_procurement_sprint4.db
```

Estado validado:

| Dataset | Registros |
|---|---:|
| SIByS | 212.742 |
| Adjudicaciones | 205.299 |
| Convocatorias | 128.951 |
| SIPRO | 73.785 |
| **Total aceptado** | **620.777** |

Además:

- 621.462 filas examinadas;
- 685 filas SIPRO rechazadas por falta de identidad estable;
- 4 documentos raw oficiales preservados;
- 181.568.107 bytes raw;
- 14.941 adjudicaciones con rubro tecnológico `INFORMATICA;`;
- 5.190 procesos únicos;
- join determinístico 14.941/14.941 con Convocatorias.

### Qué aprendimos de procurement

El corpus sirve muy bien para:

- lenguaje de mercado;
- vocabulario;
- demanda;
- categorías observadas;
- proveedores;
- contexto contractual.

Pero no ha demostrado ser una fuente suficiente de **precios comparables de servicios**.

Máxima vigente:

> **El corpus enseña el lenguaje; la evidencia comparable enseña el precio.**

---

## 7. Hallazgos de Lenguaje Enki

La investigación local produjo una primera radiografía del corpus tecnológico.

Shortlist observada:

### Servicios

- instalación;
- configuración;
- reparación;
- soporte técnico.

### Productos

- monitores;
- notebooks;
- impresoras;
- cartuchos de tóner;
- switches;
- routers.

El análisis de “instalación” mostró que, sobre 276 observaciones:

- 159 eran `PRODUCT_PLUS_INSTALLATION`;
- 81 eran `PROJECT_OR_SOLUTION`;
- 29 eran ambiguas;
- sólo 7 eran `LABOR_DOMINANT`.

Conclusión:

**seguir clasificando procurement no es la prioridad inmediata.**

Estos resultados quedan como insumo para normalización y comprensión de lenguaje, pero el siguiente trabajo debe validar la disponibilidad de evidencia económica en la web.

---

## 8. Estado de evidencia comercial

Enki ya contiene integración o investigación previa sobre fuentes comerciales como:

- CiroWhite;
- DMR;
- REED;
- Informática Paraná;
- Vida Informática;
- BairesCloud;
- Venex;
- CompraGamer.

Los resultados históricos muestran que el problema no es encontrar páginas: el problema es encontrar **observaciones económicas comparables**.

Una URL no cuenta como dato económico sólo porque contiene un símbolo `$`.

Para ser útil, una observación debe preservar como mínimo:

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

Cuando falten datos, deben mantenerse como `unknown`/`indeterminate`; nunca inferirse silenciosamente.

---

## 9. Política de moneda y geografía

Prioridad de evidencia:

1. **Argentina en ARS**, cuando exista.
2. **Argentina en USD**, cuando el proveedor publique en USD.
3. **Referencia internacional en USD**, si la muestra local es insuficiente.
4. Conversión monetaria sólo como capa de interpretación explícita.

Nunca mezclar una referencia internacional con evidencia local como si fueran equivalentes.

Ejemplo correcto:

```text
Evidencia local Argentina
ARS ...
N = ...

Referencia internacional
USD ...
N = ...
```

---

## 10. Arquitectura actual

Pipeline comercial principal:

```text
Scraper
  ↓
Parser
  ↓
OfertaDTO
  ↓
Procesador
  ↓
Normalizadores
  ↓
OfertaFactory
  ↓
Dominio
  ↓
Repositorio (Protocol)
  ↓
SQLite
```

Separadamente existe un pipeline de evidencia/raw y procurement.

Regla:

> **Not everything is an Oferta.**

Contratos públicos, documentos raw, awards, órdenes de compra y otros tipos de evidencia deben conservar su identidad semántica y no convertirse artificialmente en ofertas comerciales.

Estructura principal:

```text
src/
├── dominio/
├── aplicacion/
├── infraestructura/
├── normalizadores/
├── api/
└── configuracion_runtime.py

frontend/
├── src/app/
├── src/components/
└── src/features/

tests/
scripts/
docs/
.tmp_analysis/       # análisis local, no producto
```

---

## 11. Metodología de ingeniería

Todo cambio productivo sigue:

```text
RED → GREEN → REFACTOR
```

Y el ciclo de trabajo:

```text
CEO define una incertidumbre concreta
        ↓
Codex diagnostica brownfield
        ↓
se aprueba un único cambio causal
        ↓
RED
        ↓
implementación mínima
        ↓
GREEN
        ↓
refactor sólo si hace falta
        ↓
commit pequeño
        ↓
STOP
```

Principios:

- brownfield-first;
- cambios pequeños y causales;
- un sprint elimina una incertidumbre concreta;
- no refactorizar por estética;
- no ampliar dominio sin evidencia;
- no continuar automáticamente al sprint siguiente.

---

## 12. Máximas y guardarrails

### Datos

> **DATA FIRST.**

> **Raw first.**

> **The source is truth; extraction is interpretation.**

> **Not everything is an Oferta.**

> **Preserve provenance.**

> **Evidence types stay separate.**

> **Imports must be idempotent.**

> **100 real records beat 10,000 fabricated rows.**

> **If it is not a traceable importable record, it does not count as acquired data.**

### Comparabilidad

> **Data quality > volume.**

> **Comparability > scraping.**

> **No comparemos precios hasta comparar lo que incluyen.**

> **Price only becomes comparable when we understand what is being purchased.**

> **Granularidad sin semántica sigue siendo evidencia incompleta.**

### Adquisición

Orden preferido:

```text
official API
→ official feed/dataset
→ HTTP
→ structured page
→ browser
→ BLOCKED
```

Nunca:

- bypass anti-bot;
- CAPTCHA solving;
- stealth evasion;
- proxies para eludir protecciones;
- datos inventados.

### Dominio

> **Preserve raw + canonical.**

> **No semantic invention.**

> **El dominio crece siguiendo evidencia real, no hipótesis de taxonomía.**

### UX

> **La complejidad vive en Enki para que no tenga que vivir en la UX.**

> **La interfaz no debe mostrar todo lo que Enki sabe; primero debe mostrar lo que el usuario necesita para decidir.**

> **Diseñar la incertidumbre, no ocultarla.**

> **Si una decisión no se entiende en mobile, todavía no está suficientemente simplificada.**

### Producto

> **A single observation should feed both a simple answer and deep research.**

> **Useful Free → Valuable Premium.**

> **Nunca cobrar por corregir una frustración que nosotros mismos creamos.**

---

## 13. Lo que NO es prioridad ahora

Queda en backlog salvo bloqueo real:

- taxonomía exhaustiva;
- normalizadores genéricos;
- ampliar procurement sin pregunta económica;
- Provider Graph como fin en sí mismo;
- dashboards;
- frontend avanzado;
- IA/LLMs dentro del pipeline;
- embeddings;
- PostgreSQL;
- Kafka;
- microservicios;
- Kubernetes;
- refactors puramente cosméticos.

SQLite continúa hasta que exista un cuello de botella demostrado.

---

## 14. HISTORICAL - Project recovery - Sprint 0

> **Historical note:** this section preserves decisions from an earlier project stage. It does not define current governance, priority or next sprint. Current authority is `docs/ENKI_ARCHIVO_RECTOR.md`.


El proyecto entra en una nueva etapa de recuperación y reorganización.

### Objetivo del Sprint 0

Dejar un baseline pequeño, comprensible y reproducible antes de continuar adquisición económica.

Orden:

1. **README como fuente de orientación del proyecto.**
2. Auditoría de archivos root y artefactos legacy.
3. Separación explícita entre:
   - código;
   - datos locales;
   - research temporal;
   - logs/artefactos generados.
4. Limpiar archivos obsoletos sólo después de comprobar referencias.
5. Revisar `ARCHITECTURE.md` y manifiesto para alinearlos con la misión actual.
6. Resolver ruido de line endings/EOL sin cambios semánticos.
7. Ejecutar backend + frontend completos.
8. Commit de baseline limpio.
9. STOP.

No se mezcla este sprint con nuevas features.

---

## 15. HISTORICAL - What followed Sprint 0

### Economic Evidence Viability Gauntlet

La siguiente fase debe investigar transversalmente la red para responder:

> **¿Qué tipos de servicios tecnológicos tienen realmente precio público adquirible en Internet?**

Y también:

> **¿Qué productos/hardware tienen suficiente información pública para determinar si un precio es razonable?**

La investigación debe medir por objeto:

- fuentes descubiertas;
- proveedores independientes;
- precio público;
- precio exacto;
- moneda;
- scope;
- unidad económica;
- accesibilidad;
- trazabilidad;
- comparabilidad potencial;
- geografía;
- frescura.

Resultado esperado:

```text
SERVICE / PRODUCT
        ↓
economic evidence density
        ↓
GO / CONDITIONAL_GO / NO_GO
        ↓
primeros mercados del MVP
```

No se eligen categorías por intuición ni por frecuencia en procurement.

Se eligen por **evidencia económica adquirible**.

---

## 16. Métricas que importan

### Acquisition Yield

```text
registros aceptados / operaciones de adquisición
```

### Economic Density

```text
observaciones con semántica económica útil / registros adquiridos
```

### Useful Observation Yield

```text
observaciones comparables útiles / fuentes verificadas
```

### Technology Yield

```text
registros tecnológicos relevantes / registros adquiridos
```

El objetivo no es maximizar scraping.

El objetivo es maximizar **evidencia útil por unidad de esfuerzo**.

---

## 17. Desarrollo local

### Backend

Requisitos de referencia:

- Python 3.14.x
- pytest 9.x
- FastAPI
- SQLite

Crear entorno:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell bloquea `Activate.ps1`, puede usarse directamente:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests:

```powershell
python -m pytest -q
```

Validación vigente: ejecutar los comandos anteriores contra el checkout actual; no mantener conteos de tests manuales en esta documentación.

---

## 18. Datos locales

Las bases `.db` no se versionan.

Dataset principal de investigación actual:

```text
enki_argentina_procurement_sprint4.db
```

Debe ser reproducible desde fuentes oficiales.

Los outputs de research viven temporalmente en:

```text
.tmp_analysis/
```

Estos artefactos no son automáticamente producto ni fuente de verdad operacional.

---

## 19. Roles

### Founder

Define visión, restricciones y decisiones finales.

### CEO

Responsable de:

- foco;
- estrategia;
- priorización;
- misión;
- modelo de negocio;
- decisión de qué incertidumbre eliminar en cada sprint.

### Codex / CTO

Responsable de:

- diagnóstico brownfield;
- arquitectura;
- implementación;
- TDD;
- calidad;
- deuda técnica;
- commits pequeños.

No redefine la estrategia de negocio.

### Research agents

Generan señales e hipótesis.

No convierten una señal en verdad operacional sin evidencia verificable.

---

## 20. Regla final

Enki no se vuelve útil acumulando código.

Se vuelve útil acumulando evidencia que pueda entender **sin inventar**.

El proyecto debe avanzar siempre hacia una capacidad concreta:

> **que una persona pueda preguntar cuánto cobrar o cuánto pagar por algo tecnológico y recibir una respuesta responsable, verificable y económicamente útil.**
