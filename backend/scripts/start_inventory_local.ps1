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

if (-not (Test-Path -LiteralPath (Join-Path $postgresBin "pg_ctl.exe"))) {
    throw "PostgreSQL local no existe en $PostgresRoot."
}

if (-not (Get-NetTCPConnection -State Listen -LocalPort $PostgresPort -ErrorAction SilentlyContinue)) {
    & (Join-Path $postgresBin "pg_ctl.exe") -D $postgresData -l $postgresLog -o "-p $PostgresPort -h 127.0.0.1" -w start
}

if (-not (Get-NetTCPConnection -State Listen -LocalPort $InventoryPort -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $pythonPath -ArgumentList "-m", "uvicorn", "services.inventory_service_adapter:app", "--host", "127.0.0.1", "--port", "$InventoryPort" -WorkingDirectory $backendRoot -WindowStyle Hidden
}

Write-Output "PostgreSQL local: 127.0.0.1:$PostgresPort"
Write-Output "Inventory API: http://127.0.0.1:$InventoryPort"
