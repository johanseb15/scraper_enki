# Enki: demo comercial local

## Arranque en Windows

Desde la raíz del repositorio, en PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\iniciar-demo.ps1
```

Abre **http://127.0.0.1:3000/mercado**. Mantener la terminal abierta.
Ctrl+C detiene los dos servicios que inició el launcher. Los puertos 3000 y 8000
deben estar libres; el launcher informa conflictos y no detiene procesos ajenos.

En una máquina nueva: Python 3.14, Node.js 22 o superior y pnpm 11.9.0.
La primera preparación necesita Internet para instalar las dependencias fijadas:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\iniciar-demo.ps1 -Preparar
```

El arranque normal verifica las capturas y compila el frontend. Tras una build
correcta se puede usar `-OmitirBuild`. `-SinAbrir` evita abrir el navegador.
Logs de procesos en `.demo-runtime/`. FastAPI/OpenAPI: http://127.0.0.1:8000/docs.

## Qué incluye

Seleccionar una de las cinco categorías oficiales, ubicación publicada,
moneda y modalidad; consultar proveedores y precios; elegir un grupo con el
mismo alcance; ingresar el precio propio; revisar hipótesis, fuentes y fechas.
Se muestran mínimos, mediana, máximos, cantidad de ofertas y proveedores únicos.
Los importes del contrato comercial son strings decimales, con cálculo en
Decimal; SQLite conserva el importe canónico en `precio_decimal TEXT`.
La columna histórica `precio REAL` mantiene compatibilidad con consumidores
anteriores. La migración agrega precisión e identidad exacta, sin borrar filas.
Los importes originales tienen prioridad sobre números truncados por scrapers.

Las capturas y la interpretación versionada son la fuente offline de la demo.
El DTO, procesador, normalizadores, factory, dominio y repositorio oficiales se
reutilizan para importar las ofertas. La metadata de evidencia conserva unidad,
alcance, procedencia, fecha efectiva y texto original. La consulta usa sólo las
observaciones verificadas de la muestra, independiente de otras bases locales.

## Caso demostrable

**Soporte Técnico Informático → todas las ubicaciones → todas las modalidades.**

Tres observaciones, dos proveedores. Dos grupos separados:

| Grupo | Fuente | Referencia individual |
|---|---|---|
| Conexión remota por 1 hora · PC/Notebook/AIO | BairesCloud | ARS 30.000,00 |
| Problemas generales · sesión remota de hasta 1 hora | Bitz Computación | ARS 40.000,00 |

Ingresar `35.000,50` en el primer grupo: **16,67%** respecto de su mediana.
En el segundo: **−12,50%**. Se compara sólo contra el alcance seleccionado.
El precio propio conserva centavos; se redondea únicamente el porcentaje a dos
decimales. Una tarifa por hora y una sesión de hasta una hora permanecen separadas.
La visita a domicilio con precio “Consultar” queda excluida, con motivo visible.

## Evidencia y límites

Se guardaron dos respuestas HTTP 200 con TLS validado el **2 de octubre de 2026**:

- [BairesCloud: tarifario de servicio técnico](https://bairescloud.ar/servicio-tecnico.php).
  SHA-256: `f043c1c79553ce3df13c9a0984c9287c0d77fa321d2ac7b61393a3d330788b0a`.
  Publica febrero de 2026; el día y la vigencia actual no están confirmados.
- [Bitz Computación: tarifario](https://bitz.com.ar/tarifas-de-servicio-tecnico).
  SHA-256: `5b1e5f5de21a0ae263162d57f6d58fc0c45c250f1699cd0f282c5f631cfcae2c`.
  Fecha efectiva desconocida. Publica Sucre 186, Villa de Mayo. El CSV histórico
  del proyecto indicaba Córdoba; esa ubicación no se reutilizó.

`data/demo/captures.json` registra URL, captura UTC y hash. `data/demo/evidence.json`
contiene nueve interpretaciones con fragmentos verificables; las páginas HTML
completas se conservan al lado. La fecha de captura no reemplaza la fecha efectiva.
El símbolo $ de estos comercios argentinos se interpreta como ARS, sin conversión;
esa interpretación se explicita en las condiciones. Provincia desconocida en
ambos casos; ciudad de BairesCloud sin precisar. La geografía nunca se interpreta
como alcance nacional de atención.

Cada grupo admisible tiene **un solo proveedor**. Es una referencia publicada;
la muestra no representa todo el mercado argentino. Se requiere ampliar evidencia
con ofertas equivalentes de proveedores independientes y confirmar vigencia,
tareas, impuestos y garantías para sostener una comparación comercial más amplia.
No hay ofertas de soporte de redes en esta muestra: la pantalla muestra estado
vacío y no infiere ausencia de competidores. Las hipótesis proponen investigaciones;
no deducen demanda, rentabilidad o tendencias históricas.

Consultar funciona offline con las dependencias instaladas. “Abrir captura guardada”
funciona offline; “Abrir fuente pública” necesita Internet. Ningún fixture integra
la evidencia comercial. Un hash alterado, fragmento sin respaldo o moneda
inconsistente cierra la consulta con un error explícito.

## Guion de cinco minutos

1. **0:00–1:00:** abrir Mercado, explicar muestra dirigida, seleccionar Soporte
   Técnico Informático y consultar. Mostrar dos proveedores y tres observaciones.
2. **1:00–2:00:** abrir las condiciones de las dos ofertas remotas. Explicar por
   qué hora y sesión máxima son grupos diferentes y cada mediana tiene n=1.
3. **2:00–3:00:** elegir el primer grupo e ingresar `35.000,50`. Mostrar centavos
   y diferencia **16,67%**, aclarando que el precio cubre ese mismo alcance.
4. **3:00–4:00:** revisar hipótesis y su evidencia; abrir captura y fuente.
   Distinguir fecha de captura, febrero publicado y vigencia sin confirmar.
5. **4:00–5:00:** filtrar Villa de Mayo, luego soporte de redes para mostrar vacío;
   revisar lo desconocido y pulsar Restablecer caso para repetir la demostración.

## Verificaciones reproducibles

Usar una carpeta temporal **nueva** para cada corrida de pytest. La carpeta
predeterminada de Windows presentaba un problema de permisos en este equipo.

```powershell
$demoRun = Get-Date -Format yyyyMMddHHmmss
.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=".pytest_tmp_demo_$demoRun" -o cache_dir=.pytest_tmp_cache_demo
Push-Location frontend
pnpm.cmd test
pnpm.cmd run lint
pnpm.cmd run build
Pop-Location
```

Con la aplicación iniciada, Playwright verifica el recorrido completo bloqueando
conexiones externas y guarda capturas de escritorio y móvil en `docs/demo/`:

```powershell
.venv\Scripts\python.exe scripts\verificar_demo_navegador.py
```

Si faltara Chromium en una máquina nueva:
`.venv\Scripts\python.exe -m playwright install chromium` (requiere Internet una vez).
La proyección de la muestra puede regenerarse offline con
`.venv\Scripts\python.exe scripts\preparar_evidencia_demo.py`.

La especificación y el plan mencionados por el usuario no aparecieron como archivos
en este checkout; la implementación sigue sus requisitos explícitos y las
instrucciones rectoras locales. El registro de ejecución documenta esa limitación.
