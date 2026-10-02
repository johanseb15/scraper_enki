# MVP comercial — ejecución 2026-10-02

Rama: feat/enki-mvp-demo. Base: 084251d. Git inicial limpio.

Los archivos ENKI-MVP-demo-spec.md, 2026-10-02-enki-mvp.md y AGENTS.md no
están disponibles en este checkout. Se solicitó su ruta. Autoridad provisional:
requisitos explícitos del usuario, ARCHITECTURE.md y ENKI_ARCHIVO_RECTOR.md.
Se mantiene ejecución directa, sin repetir aprobaciones.

## Registro

- Baseline Python: 1.313 tests originales aprobados con basetemp local nuevo.
  La corrida incluyó el nuevo test de centavos en RED (1 fallo adicional).
  Carpeta temporal predeterminada de Windows inaccesible: 254 errores de setup;
  no son defectos de producto. Logs: baseline-demo.log, pytest.log.
- Baseline frontend: 16/16 aprobados (pnpm test).
- RED centavos: 129950 != Decimal('1299.50'). GREEN: 17/17 normalizador,
  factory y procesador. PrecioValor ahora extiende Decimal y retiene raw.
- RED SQLite: Decimal no admitido como parámetro SQL. GREEN: 15/15 tests;
  columna aditiva precio_decimal TEXT conserva el valor exacto en bases nuevas
  y existentes; columna legacy se mantiene por compatibilidad.
- Capturas reales locales identificadas con hashes y adquisición en agosto;
  el corpus restante tiene referencias a fixtures y no se admitirá como real.
- BairesCloud y Bitz verificados por web; descarga BairesCloud HTTP 200 con
  truststore del proyecto, TLS validado. Ubicación Bitz publicada: Villa de
  Mayo (el CSV antiguo dice Córdoba y no se toma como autoridad).

## Decisiones

- Rama aislada en el checkout autorizado: evita duplicar dependencias locales.
- Servicio de aplicación comercial adicional sobre el pipeline oficial;
  no sustituye DecisionPricing ni adjudicaciones por ofertas.
- Importes JSON como strings decimales. No conversión de monedas.
- Comparabilidad exige unidad y alcance explícitos. Modalidad desconocida,
  bundles y tarifas no exactas quedan visibles con motivos de exclusión.

## Implementación y verificaciones

- Consultas deterministas y API /market/catalog, /market/query y /market/captures.
  RED endpoints ausentes; GREEN 17 tests iniciales de API, dominio y evidencia.
- Dos capturas nuevas HTTP 200 con TLS validado el 2 de octubre. Nueve
  observaciones reales, dos proveedores, dos referencias individuales remotas.
  Nunca se agrupan tarifa por hora y sesión de duración máxima.
- RED adicional para importe DTO truncado, agrupación numérica malformada,
  moneda propia contradictoria e identidades conflictivas. GREEN 32 tests.
- RED para identidad SQLite con importes grandes que REAL colapsaba, escala
  decimal y modalidad declarada en DTO. GREEN 26 tests y luego 19 tests de
  persistencia; índice exacto y transporte explícito de modalidad.
- Frontend /mercado, enlace desde navegación original. RED del recorrido y del
  alcance legible. GREEN: 21 tests frontend. Una corrida sufrió timeouts en un
  test previo y uno nuevo; repetición con los mismos límites: 21/21 aprobados.
- Lint sin errores y build de producción exitosa. Launcher iniciado dos veces
  con build real; Ctrl+C verificado: puertos 3000 y 8000 quedaron libres antes
  del segundo arranque. Regresión de contrato CLI resuelta agregando argparse
  al script nuevo, sin modificar ni omitir tests de gobernanza.
- Playwright bloqueó conexiones externas y comprobó consulta, captura local,
  comparación, cambio de alcance, filtro geográfico, vacío, restablecimiento,
  precio inválido y reintento. Sin errores de página ni overflow horizontal.
- Inspección visual real a 1440x1000 y 390x844; cuatro screenshots en docs/demo.
  Ajustados filtros móviles y alcance completo visible.
- Suite tras los cambios monetarios: 1.316/1.316. Suite con API inicial:
  1.332 aprobados y un fallo CLI corregido. Suite posterior: 1.343/1.343,
  luego 1.346/1.346. Corrida de entrega registrada en release-suite.log.
- Corrida de entrega: **1.347/1.347 aprobados, 58,60 s**. Frontend: **21/21**;
  lint sin hallazgos y build Next de producción aprobada. Navegador: recorrido
  desktop/móvil offline aprobado, sin errores de página ni overflow horizontal.
- Guía de arranque y guion de cinco minutos: docs/DEMO-COMERCIAL.md.
- Empaquetado Git comprobado: ambos hashes de las capturas coinciden con los
  bytes del índice. .gitattributes conserva HTML como bytes sin conversión de
  saltos de línea en Windows. git diff --cached --check aprobado.

## Revisión final

Revisión directa del autor contra requisitos, contratos y diff: procedencia
guardada, importes Decimal, referencia limitada a alcance seleccionado,
exclusiones visibles, fuentes públicas y capturas offline, sin inferencias de
demanda o rentabilidad. Conservados todos los tests originales. Ningún push,
publicación o cambio en otros repositorios.

## Límites pendientes

- Plan y especificación mencionados sin archivo disponible; se aplicaron los
  requisitos del mensaje y los documentos rectores locales.
- Cada grupo real admisible tiene un proveedor; queda pendiente ampliar
  ofertas equivalentes de proveedores independientes para un benchmark amplio.
- Vigencia de BairesCloud sin confirmar (tarifario febrero de 2026); Bitz no
  publica fecha efectiva. Impuestos, garantías y tareas no detalladas desconocidos.
- No hay evidencia de soporte de redes en esta muestra dirigida.
