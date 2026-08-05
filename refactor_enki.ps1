# Script de refactorizacion y limpieza para scraper_enki

$basePath = "src"
$targetScraperPath = Join-Path $basePath "infraestructura\scrapers"
$legacyScraperPath = Join-Path $basePath "scrapers"

Write-Host ""
Write-Host "=== Inicio de Refactorizacion scraper_enki ===" -ForegroundColor Cyan

# 1. Crear directorio destino si no existe
if (-not (Test-Path $targetScraperPath)) {
    New-Item -ItemType Directory -Path $targetScraperPath -Force | Out-Null
    Write-Host "[+] Creada la carpeta: $targetScraperPath" -ForegroundColor Green
}

# 2. Mover scrapers desde src/scrapers a src/infraestructura/scrapers
if (Test-Path $legacyScraperPath) {
    $scrapers = Get-ChildItem -Path $legacyScraperPath -Filter "*.py"
    if ($scrapers.Count -gt 0) {
        foreach ($file in $scrapers) {
            Move-Item -Path $file.FullName -Destination $targetScraperPath -Force
            Write-Host "[->] Movido: $($file.Name) -> src/infraestructura/scrapers/" -ForegroundColor Cyan
        }
    }
    # Eliminar la carpeta original si quedo vacia
    if ((Get-ChildItem -Path $legacyScraperPath).Count -eq 0) {
        Remove-Item -Path $legacyScraperPath -Force
        Write-Host "[-] Carpeta obsoleta eliminada: $legacyScraperPath" -ForegroundColor Yellow
    }
} else {
    Write-Host "[i] No se encontro la carpeta src/scrapers (ya fue migrada o no existe)." -ForegroundColor Gray
}

# 3. Eliminar directorios __pycache__ recursivamente
Write-Host ""
Write-Host "[+] Limpiando __pycache__..." -ForegroundColor Green
$pycaches = Get-ChildItem -Path $basePath -Recurse -Filter "__pycache__" -Directory
if ($pycaches.Count -gt 0) {
    foreach ($cache in $pycaches) {
        Remove-Item -Path $cache.FullName -Recurse -Force
        Write-Host "[-] Eliminado: $($cache.FullName)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "[i] No se encontraron carpetas __pycache__." -ForegroundColor Gray
}

# 4. Auditoria de archivos legacy sueltos en la raiz de src/
$legacyCandidates = @(
    "downloader.py",
    "extractor.py",
    "normalizacion.py",
    "pipeline.py",
    "main.py",
    "repositorio.py",
    "repositorio_ofertas.py",
    "metricas.py",
    "estadisticas.py",
    "presentacion.py",
    "reporte.py"
)

Write-Host ""
Write-Host "[!] Archivos legacy en src/ (pendientes de revisar / borrar):" -ForegroundColor Yellow
$foundLegacy = 0
foreach ($file in $legacyCandidates) {
    $filePath = Join-Path $basePath $file
    if (Test-Path $filePath) {
        Write-Host "    [!] $filePath" -ForegroundColor Red
        $foundLegacy++
    }
}

if ($foundLegacy -eq 0) {
    Write-Host "    [OK] La raiz de src/ esta limpia de archivos legacy conocidos." -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Proceso completado exitosamente ===" -ForegroundColor Cyan