# Correcciones acotadas de la validación de producto

Fecha: 2026-10-02. Un solo agente. Estado: **los tres puntos acotados están
corregidos y verificados; cambios locales listos para revisión**.

## Punto de partida y alcance

- Rama `feat/enki-mvp-demo`; HEAD inicial `ccb507b6e290eed6f1543d1424708626a32d0ca4`.
- Checkout inicial limpio y sin diferencias respecto del commit validado.
- No se encontró `AGENTS.md` en el repositorio ni en los padres consultados.
- Python del entorno declarado: **3.14.7**.
- Sólo reconocimiento de soporte técnico remoto/moneda explícita, centavos en
  Cotización y motivos de abstención. No iniciar integración Mercado/Decisión,
  adquisición en vivo, política temporal ni portabilidad en esta ejecución.
- Sin reset, limpieza, push, merge ni cambios en datos comerciales o historial.
- Antecedentes leídos: integración PC del 02/10, DEMO-COMERCIAL y entrega MVP;
  parser, contrato API y componentes/tests necesarios. No se encontró el ZIP
  nombrado entre los archivos del repositorio; se reprodujeron los casos del prompt.

## RED → GREEN → REFACTOR

| Hallazgo | RED observado | Corrección y GREEN |
|---|---|---|
| Soporte técnico remoto | 1 fallo, 1 aprobado: `canonical_services == ()` | Variante opcional `tecnico` en la regla existente; 35 aprobados con tests originales del parser |
| USD antes del importe, ARS/pesos y contradicciones | 9 fallos, 5 aprobados: moneda UNKNOWN o contradicción resuelta como USD | Reconocimiento antes/después reutilizando `_component_currency`; UNKNOWN cuando las marcas discrepan; detección de varios montos; 40 tests focalizados aprobados |
| Centavos frontend | 6 fallos, 12 aprobados: `$35.001`, referencias redondeadas y `UNKNOWN` visible | Formato compartido entre flujo y BenchmarkRail, sin aritmética monetaria nueva; 18 aprobados |
| Referencias en texto backend | 2 fallos, 6 aprobados: redondeo de mediana y cuartiles | Presentación con Decimal; 14 aprobados incluyendo API |
| Motivo de abstención | 6 fallos, 18 aprobados | Estados visuales separados; descripción del backend en interpretación y resultado; evidencia no autorizada identificada como observada; 29 aprobados con UI modular |
| Confianza sin evidencia en el resultado real | 2 fallos: `Confianza: NONE` / `UNKNOWN` visibles | Confianza sólo cuando el backend autoriza rango/decisión; 26 tests del flujo aprobados |

No se exige DECISION_READY al reconocer un servicio. USD se reconoce, pero la
evaluación actual sigue restringida a ARS. La moneda sin marca sigue requiriendo
aclaración. Las marcas monetarias contradictorias permanecen UNKNOWN y bloquean
la evaluación con la aclaración de moneda existente.

El contrato actual no contiene un estado específico de incompatibilidad
comprobada: NO_EVIDENCE tampoco la demuestra. Se conserva el componente genérico
de incompatibilidad para consumidores que la conozcan, sin seleccionarlo desde
esos estados. No se incorporó un estado API inventado.

REFACTOR: las variantes amplían las reglas existentes; la detección de moneda se
comparte con composición monetaria; ambos componentes usan un único formateador.
Se conservan formatos enteros y el contrato numérico de la API.

## Verificación ejecutada

Pruebas focalizadas usadas para cada ciclo (desde la raíz salvo Vitest):

```powershell
.venv/Scripts/python.exe -m pytest tests/test_parser_remote_support_validation.py -q --tb=short -o cache_dir=.pytest_tmp_cache_correcciones
.venv/Scripts/python.exe -m pytest tests/test_parser_explicit_currency_validation.py -q --tb=short -o cache_dir=.pytest_tmp_cache_correcciones
.venv/Scripts/python.exe -m pytest tests/test_enki_pricing_response.py -q --tb=short -o cache_dir=.pytest_tmp_cache_correcciones
# Desde frontend, RED y GREEN de centavos/estados:
pnpm.cmd exec vitest run src/features/decision/__tests__/decision-flow.test.tsx
pnpm.cmd exec vitest run src/features/decision/__tests__/decision-flow.test.tsx -t 'confidence when no evidence'
```

Comandos finales:

```powershell
$parserTests = @(Get-ChildItem -LiteralPath tests -Filter 'test_parser*.py' | ForEach-Object FullName)
& .venv/Scripts/python.exe -m pytest @parserTests tests/test_enki_pricing_response.py tests/test_enki_pricing_query_service.py tests/test_decision_pricing_api.py tests/test_td013_decision_api_contract.py -q --tb=short --basetemp=.pytest_tmp_correcciones_backend_cierre -o cache_dir=.pytest_tmp_cache_correcciones
# Desde frontend:
pnpm.cmd test
pnpm.cmd run lint
pnpm.cmd run build
```

- Backend focalizado de cierre: **188 aprobados**, 1,39 s.
- Frontend completo final: **35 aprobados**, 3 archivos; incluye Mercado. Los
  26 tests del flujo también aprobaron por separado. La primera corrida completa
  tenía 33 aprobados; se repitió después del hallazgo visual de confianza NONE.
- Lint: código 0. Build de producción: código 0, rutas Cotización y Mercado generadas.
- No se ejecutó la suite backend completa en este bloque acotado.
- Incidencias de comandos: PowerShell no expandió `tests/test_parser*.py` al
  invocar pytest (0 tests); se corrigió enumerando los archivos, sin omitirlos.
  Un comando compuesto con variable de entorno no encontró vitest; la ejecución
  directa desde frontend funcionó.
- Los servicios previos ocupaban 3000/8000; el servicio 8000 todavía respondía
  UNKNOWN a USD. No se detuvieron ni se usaron para aprobar el código nuevo.
  Los intentos de iniciar allí terminaron con puerto ocupado. Next requirió
  ejecución fuera del sandbox para encontrar su ejecutable. La inspección de
  procesos por CIM fue denegada; se usaron sockets y HTTP para diagnosticar.
- Ajustes de selectores durante GREEN: cuartiles se presentan dentro de texto
  compuesto y la pregunta ahora aparece en dos lugares; se selecciona el texto
  incluido o la sección correspondiente, conservando importes y garantías.
- `git diff --check`: código 0; Git avisa conversión LF/CRLF en archivos de código.
  No se modifican capturas RAW, hashes ni configuración Git.

## API real y navegador

Se usó el build de producción corregido, frontend en 3001 y una API separada en
8001, conservando la demo anterior. El harness amplió CORS sólo en memoria para
el origen local 3001 y fijó una ruta de DB aislada; el producto no recibió cambios
de CORS. Playwright redirigió las peticiones al puerto aislado mediante
`route.continue_`, sin fabricar respuestas.

```powershell
# Terminal API, desde la raíz:
.venv/Scripts/python.exe -c "import os,uvicorn; from src.api.main import app; os.environ['ENKI_DB_PATH']='.demo-runtime/correcciones-cotizacion.db'; app.user_middleware[0].kwargs['allow_origins'].append('http://127.0.0.1:3001'); uvicorn.run(app,host='127.0.0.1',port=8001)"
# Terminal frontend, desde frontend:
pnpm.cmd exec next start --hostname 127.0.0.1 --port 3001
# Verificación, desde la raíz:
.venv/Scripts/python.exe scripts/verificar_demo_navegador.py --cotizacion-only --url http://127.0.0.1:3001 --api-url http://127.0.0.1:8001
```

Resultado final: **10 casos**, escritorio 1440×1000 y móvil 390×844; sin errores
de página ni desbordamiento horizontal. Además se comprobaron corrección del
texto, fallo de conexión y reintento en ambos tamaños. Sólo el fallo de conexión
se inyectó abortando la solicitud; todas las respuestas de precio fueron reales.

| Caso real | Resultado comercial verificado |
|---|---|
| Cobro 35000 pesos por una hora de soporte técnico remoto en Argentina | SOPORTE_REMOTO, 35000 ARS; UNSUPPORTED_QUERY por alcance territorial no confirmado, sin preguntar qué servicio es |
| USD 100 por hora por soporte remoto a todo el país | SOPORTE_REMOTO, 100 USD; UNSUPPORTED_QUERY por ARS_ONLY_V1 |
| $35.000,50 por formatear notebook en Córdoba | 35000.5 ARS; `$35.000,50` en interpretación y resultado; NO_EVIDENCE explicado sin incompatibilidad inventada |
| 100 sin moneda por hora de soporte remoto nacional | CLARIFICATION_REQUIRED; pregunta de moneda, sin UNKNOWN en pantalla ni acceso a evaluación |
| ARS 100 USD por hora de soporte remoto nacional | CLARIFICATION_REQUIRED; conserva la contradicción, sin elegir moneda silenciosamente |

Las cohortes runtime guardadas tienen sólo cabeceras. No se introdujeron
cohortes sintéticas para obtener una evaluación positiva. INSUFFICIENT_EVIDENCE,
rangos y cuartiles se cubrieron con respuestas/cohortes controladas en tests; no
se presentan como evidencia comercial ni como recorridos reales con esa muestra.

El runner nuevo detectó tres problemas de sincronización/selectores antes de
aprobar: el link incluye su descripción en el nombre accesible, el botón incluye
una flecha, y el formulario de Home comparte el label con Cotización. Se espera
la navegación y el encabezado de Cotización antes de llenar su campo. No se
cambiaron expectativas de servicio, importe ni estado para ocultar esos fallos.

Respuestas completas y capturas nuevas, sin sustituir las capturas históricas:

- [Registro de API/navegador](demo/correcciones-cotizacion/verificacion-cotizacion.json).
- [Interpretación escritorio](demo/correcciones-cotizacion/centavos-interpretacion-escritorio.png).
- [Resultado escritorio](demo/correcciones-cotizacion/centavos-resultado-escritorio.png).
- [Interpretación móvil](demo/correcciones-cotizacion/centavos-interpretacion-movil.png).
- [Resultado móvil](demo/correcciones-cotizacion/centavos-resultado-movil.png).

Se inspeccionaron visualmente capturas de escritorio y móvil. Al finalizar se
cerraron las instancias propias; 3001/8001 ya no aceptaban conexiones y los
servicios previos 3000/8000 seguían respondiendo. La DB aislada no se creó: este
recorrido sólo lee cohortes. `git diff --quiet -- data tests/fixtures
.gitattributes` devolvió 0: sin cambios en evidencia, fixtures ni su configuración.

## Archivos y estado Git de entrega

HEAD sigue en `ccb507b6e290eed6f1543d1424708626a32d0ca4`, rama
`feat/enki-mvp-demo`. Cambios sin stage ni commit. Sin push ni merge.

Archivos modificados:

- `src/aplicacion/parser_consulta_pricing.py`
- `src/aplicacion/enki_pricing_response.py`
- `frontend/src/features/decision/components/DecisionReviewFlow.tsx`
- `frontend/src/features/decision/components/BenchmarkRail.tsx`
- `frontend/src/features/decision/types.ts`
- `frontend/src/components/enki/decision-state.tsx`
- `frontend/src/features/decision/__tests__/decision-flow.test.tsx`
- `tests/test_enki_pricing_response.py`
- `scripts/verificar_demo_navegador.py`

Archivos nuevos:

- `frontend/src/features/decision/format-money.ts`
- `tests/test_parser_remote_support_validation.py`
- `tests/test_parser_explicit_currency_validation.py`
- Este informe y los cinco artefactos listados arriba en
  `docs/demo/correcciones-cotizacion/`.

No quedan fallos conocidos en las verificaciones finales de este bloque. No se
ejecutó navegador de Mercado, suite backend completa, clone Linux ni adquisición
en vivo en este bloque. Los procesos de demo ya abiertos siguen sirviendo su
versión previa hasta que su operador los reinicie.

## Límites y siguiente bloque

No se declara resuelta la integración Mercado/Decisión, la evidencia en vivo,
la temporalidad, los fallos de portabilidad Linux ni la conservación de fixtures
históricos. No se infiere cobertura nacional de la palabra Argentina: el caso
original puede seguir fuera del alcance territorial admitido tras reconocer
correctamente el servicio y el precio.

Próximo paso de producto después de revisar estas correcciones: trazar e integrar
Mercado con los controles existentes de Decisión; después investigar exclusiones
de alcance y temporalidad según la especificación aprobada, sin inventar TTL ni
relajar umbrales. Esas tareas están aplazadas por instrucción expresa.
