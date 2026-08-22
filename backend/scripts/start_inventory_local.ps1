param(
    [string]$PostgresRoot = "C:\tmp\erclave-postgresql17",
    [int]$PostgresPort = 5434,
    [int]$InventoryPort = 8004
)

$ErrorActionPreference = "Stop"
$backendRoot = Split-Path -Parent $PSScriptRoot
$postgresBin = Join-Path $PostgresRoot "pgsql\bin"
$postgresData = Join-Path $PostgresRoot "data"
$postgresLog = Join-Path $PostgresRoot "postgresql.log"
$pythonPath = Join-Path $backendRoot ".venv\Scripts\python.exe"
$envFile = Join-Path $backendRoot ".env"

if (-not (Test-Path -LiteralPath (Join-Path $postgresBin "pg_ctl.exe"))) {
    throw "PostgreSQL local no existe en $PostgresRoot."
}

$databaseLine = Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^ERCLAVE_INVENTORY_DATABASE_URL=' } | Select-Object -First 1
if (-not $databaseLine) { throw "ERCLAVE_INVENTORY_DATABASE_URL no existe en backend/.env." }
$localDatabaseUrl = ($databaseLine -split '=', 2)[1]
if ($localDatabaseUrl -notmatch "@127\.0\.0\.1:$PostgresPort/erclave_local$") {
    throw "Guardrail: Inventory Local debe usar 127.0.0.1:$PostgresPort/erclave_local."
}

$env:ERCLAVE_ENVIRONMENT = "local"
$env:ERCLAVE_AUTH_MODE = "firebase"
$env:ERCLAVE_FIREBASE_PROJECT_ID = "demo-erclave"
$env:FIREBASE_AUTH_EMULATOR_HOST = "127.0.0.1:9099"
$env:ERCLAVE_DATABASE_URL = $localDatabaseUrl
$env:ERCLAVE_INVENTORY_DATABASE_URL = $localDatabaseUrl
$env:ERCLAVE_ADMIN_SERVICE_URL = "http://127.0.0.1:8000"
$env:ERCLAVE_PRODUCTION_SERVICE_URL = "http://127.0.0.1:8002"
$env:ERCLAVE_INVENTORY_SERVICE_URL = "http://127.0.0.1:$InventoryPort"
$env:ERCLAVE_APP_PUBLIC_BASE_URL = "http://127.0.0.1:4173"

if (-not (Get-NetTCPConnection -State Listen -LocalPort $PostgresPort -ErrorAction SilentlyContinue)) {
    & (Join-Path $postgresBin "pg_ctl.exe") -D $postgresData -l $postgresLog -o "-p $PostgresPort -h 127.0.0.1" -w start
}

if (-not (Get-NetTCPConnection -State Listen -LocalPort $InventoryPort -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $pythonPath -ArgumentList "-m", "uvicorn", "services.inventory_service_adapter:app", "--host", "127.0.0.1", "--port", "$InventoryPort" -WorkingDirectory $backendRoot -WindowStyle Hidden
}

Write-Output "PostgreSQL local: 127.0.0.1:$PostgresPort"
Write-Output "Inventory API: http://127.0.0.1:$InventoryPort"
