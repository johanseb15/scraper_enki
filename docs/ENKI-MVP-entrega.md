# Entrega del MVP comercial de Enki

Fecha: 2026-10-02. Rama local: `feat/enki-mvp-demo`.

Arranque, operación, caso completo y guion de cinco minutos:
[DEMO-COMERCIAL.md](DEMO-COMERCIAL.md).

## Cambios

| Área | Archivos | Resultado |
|---|---|---|
| Importe y transporte | `src/dominio/oferta.py`, `src/normalizadores/normalizador_precios.py`, `src/aplicacion/dto/oferta_dto.py`, `oferta_factory.py`, `procesador_ofertas.py`, `src/estadisticas.py` | Decimal, centavos, texto original como autoridad y modalidad declarada |
| Persistencia | `src/infraestructura/sqlite/repositorio_sqlite_ofertas.py` | Columna decimal exacta, migración compatible e identidad que conserva centavos |
| Consulta comercial | `src/dominio/market_observation.py`, `src/aplicacion/market_query_service.py` | Grupos deterministas por servicio, moneda, modalidad, unidad y alcance; exclusiones e hipótesis trazables |
| Evidencia | `src/infraestructura/demo_evidence_repository.py`, `data/demo/`, `scripts/preparar_evidencia_demo.py` | Dos capturas públicas reales, hash, URL, fechas y nueve observaciones offline |
| API | `src/api/market.py`, `src/api/main.py` | Catálogo, consulta y captura verificadas; validaciones y errores explícitos |
| Interfaz | `frontend/src/app/mercado/`, `frontend/src/features/market/`, `EnkiHeader.tsx` | Recorrido completo en español, escritorio y móvil |
| Operación | `iniciar-demo.ps1`, README, guía y registro | Un comando de arranque, preparación fijada, logs y cierre de servicios propios |
| Empaquetado | `.gitattributes`, `.gitignore` | Capturas sin conversión de saltos de línea y artefactos runtime fuera del commit |
| Validación | `tests/test_demo_*.py`, tests de normalizador y frontend, `scripts/verificar_demo_navegador.py` | TDD y recorrido real con conexiones externas bloqueadas |

## Resultados ejecutados

- Baseline original: **1.313 tests Python** y **16 frontend** aprobados.
- Suite de entrega: **1.347 tests Python aprobados**, 58,60 s, sin omisiones.
- Frontend: **21 tests aprobados**, lint sin errores, build de producción aprobada.
- Primer test en RED comprobado: `$1.299,50` se convertía en `129950`.
  GREEN conserva `Decimal('1299.50')` y texto original.
- SQLite comprobado con importes grandes, centavos diferentes, escala equivalente,
  importación repetida, desconocidos y transporte de modalidad.
- Capturas alteradas, texto inventado, fixtures, rutas fuera del directorio,
  IDs duplicados y moneda inconsistente rechazados por los tests de evidencia.
- API offline verificada: n, proveedores, precio propio, 422, 503, vacío y captura.
- Playwright real: escritorio **1440×1000** y móvil **390×844**, sin errores de
  página ni desbordamiento horizontal; fuentes/captura, precio, filtros, vacío,
  restablecimiento y recuperación de errores aprobados.
- Launcher: build real, arranque HTTP 200 de ambos servicios y cierre con Ctrl+C;
  puertos 3000 y 8000 comprobados libres antes del siguiente arranque.
- Bytes de ambas capturas comprobados también en el índice Git: SHA-256 coincide
  con el manifiesto. `git diff --cached --check` aprobado.

Los errores iniciales de pytest fueron permisos de su carpeta temporal de Windows;
usar una carpeta nueva dentro del proyecto resolvió los 254 errores de setup.
Una corrida intermedia detectó el contrato de scripts argparse: se corrigió el
entrypoint nuevo sin cambiar el test. Una corrida frontend sufrió dos timeouts;
se repitió con los mismos límites y aprobó los 21 tests.

Evidencia visual y registro automático:

- [Escritorio](demo/demo-escritorio.png)
- [Benchmark en escritorio](demo/demo-benchmark-escritorio.png)
- [Móvil](demo/demo-movil.png)
- [Benchmark en móvil](demo/demo-benchmark-movil.png)
- [Verificación del navegador](demo/verificacion-navegador.json)

## Límites comerciales pendientes

Dos proveedores observados; **cada grupo comparable tiene un único proveedor**.
La muestra no representa el mercado argentino. Para una comparación amplia se
necesitan más ofertas equivalentes de proveedores independientes y confirmación
de vigencia. BairesCloud publica febrero de 2026; la fecha efectiva de Bitz es
desconocida. Condiciones no publicadas permanecen desconocidas; no hay evidencia
de soporte de redes en la muestra. No se infiere demanda, rentabilidad o tendencia.

No hubo bloqueos para ejecutar el recorrido sobre evidencia pública guardada.
Los archivos de especificación y plan nombrados por el usuario no estaban
disponibles en el checkout: se siguieron sus requisitos explícitos y los
documentos rectores locales, como consta en el registro de ejecución.
