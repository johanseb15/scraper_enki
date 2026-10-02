param(
    [switch]$Preparar,
    [switch]$SinAbrir,
    [switch]$OmitirBuild
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonDemo = Join-Path $projectRoot '.venv/Scripts/python.exe'
$frontendRoot = Join-Path $projectRoot 'frontend'
$logRoot = Join-Path $projectRoot '.demo-runtime'
$apiProcess = $null
$frontProcess = $null

function Assert-LastExit([string]$Action) {
    if ($LASTEXITCODE -ne 0) { throw "$Action fallo (codigo $LASTEXITCODE)." }
}

function Assert-PortFree([int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $client.Connect('127.0.0.1', $Port)
        throw "El puerto $Port esta ocupado. Cierra su proceso antes de iniciar la demo."
    } catch [System.Net.Sockets.SocketException] {
        # Conexion rechazada: puerto libre.
    } finally { $client.Dispose() }
}

function Wait-Service([string]$Url, $Process) {
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        if ($Process.HasExited) { throw "Un servicio termino antes del arranque. Revisa $logRoot." }
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { return }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    throw "No respondio $Url. Revisa los logs en $logRoot."
}

Push-Location $projectRoot
try {
    if ($Preparar) {
        if (-not (Test-Path -LiteralPath $pythonDemo)) {
            & py -3.14 -m venv .venv
            Assert-LastExit 'Creacion de entorno Python 3.14'
        }
        & $pythonDemo -m pip install -r requirements.txt
        Assert-LastExit 'Instalacion de dependencias Python'
        Push-Location $frontendRoot
        try {
            & pnpm.cmd install --frozen-lockfile
            Assert-LastExit 'Instalacion frontend'
        } finally { Pop-Location }
    }
    if (-not (Test-Path -LiteralPath $pythonDemo)) { throw 'Falta .venv. Ejecuta el comando con -Preparar.' }
    if (-not (Get-Command pnpm.cmd -ErrorAction SilentlyContinue)) { throw 'Instala Node.js 22 o superior y pnpm 11.9 antes de iniciar.' }
    if (-not (Test-Path -LiteralPath (Join-Path $frontendRoot 'node_modules'))) { throw 'Faltan dependencias frontend. Ejecuta con -Preparar.' }
    Assert-PortFree 8000
    Assert-PortFree 3000
    & $pythonDemo -c 'from src.infraestructura.demo_evidence_repository import load_demo_evidence; items=load_demo_evidence(); assert items; print(len(items))'
    Assert-LastExit 'Verificacion de evidencia'
    Push-Location $frontendRoot
    try {
        if (-not $OmitirBuild) {
            & pnpm.cmd run build
            Assert-LastExit 'Build de produccion'
        } elseif (-not (Test-Path -LiteralPath '.next/BUILD_ID')) {
            throw 'Falta build. Inicia sin -OmitirBuild.'
        }
    } finally { Pop-Location }
    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
    $apiProcess = Start-Process -FilePath $pythonDemo -ArgumentList '-m','uvicorn','src.api.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'api.stdout.log') -RedirectStandardError (Join-Path $logRoot 'api.stderr.log')
    $frontProcess = Start-Process -FilePath $env:ComSpec -ArgumentList '/d','/s','/c','"pnpm.cmd exec next start --hostname 127.0.0.1 --port 3000"' -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'frontend.stdout.log') -RedirectStandardError (Join-Path $logRoot 'frontend.stderr.log')
    Wait-Service 'http://127.0.0.1:8000/market/catalog' $apiProcess
    Wait-Service 'http://127.0.0.1:3000/mercado' $frontProcess
    Write-Host ''
    Write-Host 'Enki ejecutandose: http://127.0.0.1:3000/mercado' -ForegroundColor Green
    Write-Host 'API: http://127.0.0.1:8000/docs | Evidencia: data/demo'
    Write-Host 'Para detener ambos servicios, presiona Ctrl+C en esta terminal.'
    if (-not $SinAbrir) { Start-Process 'http://127.0.0.1:3000/mercado' }
    while (-not $apiProcess.HasExited -and -not $frontProcess.HasExited) { Start-Sleep -Seconds 1 }
    throw "Un servicio se detuvo. Revisa $logRoot."
} finally {
    foreach ($ownedProcess in @($frontProcess, $apiProcess)) {
        if ($null -ne $ownedProcess -and -not $ownedProcess.HasExited) {
            & taskkill.exe /PID $ownedProcess.Id /T /F 2>$null | Out-Null
        }
    }
    Pop-Location
}
