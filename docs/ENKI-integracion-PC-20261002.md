# Integración del trabajo de la PC personal

Fecha: 2026-10-02. Destino: `feat/enki-mvp-demo`.

## Integración

- Checkout inicial limpio, en `9de49843594b3e57ca6dd1cabc6888b7611c9b0e`, igual a la rama publicada.
- Se ejecutó `git fetch origin`. La transferencia terminó en
  `a7042fb84753fa19c947c22452e69ff5c8cb1430`.
- `git log --left-right` y `git cherry` comprobaron que faltaban ambos commits,
  sin equivalentes: `66004e07d29a4567664d6aa71cd97f283ca14487` y `a7042fb84753fa19c947c22452e69ff5c8cb1430`.
- Merge sin conflictos, conservando los commits originales y el MVP.
- La corrección atribuye repuestos a la oferta actual, distingue repuestos
  incluidos de mano de obra y rechaza comparaciones sensibles con alcance
  desconocido o contradictorio. Se incorporan sus 22 tests.
- Se leyeron el diseño y el plan de live evidence refresh como antecedentes.
  Su implementación queda pendiente de una tarea posterior. Único ajuste al
  documento recuperado: tres saltos Markdown con espacios finales se expresan
  mediante párrafos, sin cambiar sus decisiones.
- `main` y la rama de transferencia no se modificaron.

## Verificación ejecutada

```powershell
.venv/Scripts/python.exe -m pytest tests/test_u009_parts_scope.py tests/test_normalizador_precios.py tests/test_demo_money_roundtrip.py tests/test_demo_evidence.py tests/test_demo_market.py tests/test_demo_api.py -q --tb=short --basetemp=.pytest_tmp_integration_focus_20261002 -o cache_dir=.pytest_tmp_cache_integration
.venv/Scripts/python.exe -m pytest -q --tb=short --basetemp=.pytest_tmp_integration_full_20261002 -o cache_dir=.pytest_tmp_cache_integration
```

| Verificación | Resultado |
|---|---|
| Alcance de repuestos, Decimal, evidencia y consultas/API del MVP | 57 aprobados, 0,92 s |
| Suite backend completa | 1.369 aprobados, 93,44 s; sin omisiones |
| Frontend `pnpm.cmd test` | 21 aprobados en tres archivos, 6,27 s |
| Frontend `pnpm.cmd run lint` | Código 0 |
| Frontend `pnpm.cmd run build` | Código 0; `/mercado` generado |

Los directorios temporales son exclusivos de esta ejecución para evitar
colisiones de permisos en Windows. No se debilitaron ni omitieron tests.

## Iniciador y HTTP

Se revisaron los logs anteriores y el registro de ejecución del último
iniciador: proceso de ejecución `1723`, iniciado a las 13:33:40 y terminado a
las 13:48:15, con código `-1` después de 874,75 segundos. Había anunciado
`Enki ejecutandose`, sin stderr del iniciador. Los logs mostraban Uvicorn y
Next listos, consultas HTTP 200 y ningún traceback ni error del frontend.

El diagnóstico es terminación/interrupción del proceso que mantiene abiertos
los servicios, sin evidencia de fallo de aplicación. El registro no identifica
qué originó esa interrupción. No corresponde modificar el iniciador por ese
código aislado.

Se ejecutó nuevamente:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./iniciar-demo.ps1 -SinAbrir -OmitirBuild
```

| Solicitud real | Resultado |
|---|---|
| GET `http://127.0.0.1:3000/mercado` | 200 |
| GET `http://127.0.0.1:8000/docs` | 200 |
| GET `/market/catalog` | 200 |
| POST `/market/query`, soporte técnico | 200; dos proveedores, dos grupos separados |
| POST `/market/query`, precio propio `35000,50` ARS | 200; diferencia `16.67` en el grupo compatible y `null` en el otro |
| GET `/market/captures/bairescloud` | 200; URL de fuente y SHA-256 visibles |

La evidencia sigue siendo la muestra offline del MVP, con sus límites
comerciales. Estas verificaciones no implementan adquisición de evidencia en
vivo. Al terminar se interrumpió deliberadamente el iniciador con Ctrl+C.

## Recuperar en la PC personal

Desde el repositorio de la PC personal:

```powershell
git status --short
git fetch origin
git switch feat/enki-mvp-demo
git pull --ff-only origin feat/enki-mvp-demo
git rev-parse HEAD
git rev-parse origin/feat/enki-mvp-demo
```

Si hay cambios locales, conservarlos antes de cambiar de rama. Si la rama
local no existe, `git switch` normalmente la crea desde la rama remota; también
se puede usar `git switch --track origin/feat/enki-mvp-demo` en ese caso.

El hash publicado se informa en la entrega de esta integración. La
sincronización de ambas PCs solo queda comprobada cuando el HEAD de la PC
personal coincide con ese hash. Desde este equipo no se comprobó su checkout.
