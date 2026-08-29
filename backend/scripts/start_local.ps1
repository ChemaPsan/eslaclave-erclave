param(
    [string]$PostgresRoot = "C:\tmp\erclave-postgresql17",
    [int]$PostgresPort = 5434,
    [int]$FirebaseAuthPort = 9099,
    [int]$FirebaseUiPort = 4000
)

$ErrorActionPreference = "Stop"
$backendRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $backendRoot
$frontendRoot = Join-Path $repoRoot "frontend"
$pythonPath = Join-Path $backendRoot ".venv\Scripts\python.exe"
$postgresBin = Join-Path $PostgresRoot "pgsql\bin"
$postgresData = Join-Path $PostgresRoot "data"
$postgresLog = Join-Path $PostgresRoot "postgresql.log"
$localTenantId = "ten_739ee59d765d5e14818674800d"
$localActorId = "usr_595f3cd6d4325901a8dbd028e1"
$localEmail = "admin.qa@erclave.local"
$localPassword = "LocalDemo123!"

function Assert-Port-Free([int]$Port, [string]$Name) {
    if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
        throw "$Name ya escucha en $Port. Deten el proceso anterior antes del arranque canonico."
    }
}

foreach ($requiredPath in @($pythonPath, (Join-Path $postgresBin "pg_ctl.exe"))) {
    if (-not (Test-Path -LiteralPath $requiredPath)) { throw "Falta dependencia local: $requiredPath" }
}
if (-not (Get-Command firebase.cmd -ErrorAction SilentlyContinue)) { throw "Firebase CLI no esta instalado." }
if (-not (Get-Command java.exe -ErrorAction SilentlyContinue)) {
    $portableJava = Get-ChildItem -LiteralPath "C:\tmp\microsoft-jdk-21" -Recurse -Filter "java.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $portableJava) { throw "Java no esta instalado; Firebase Emulator no puede iniciar." }
    $javaBin = Split-Path -Parent $portableJava.FullName
    $env:JAVA_HOME = Split-Path -Parent $javaBin
    $env:Path = "$javaBin;$env:Path"
}

$envLine = Get-Content -LiteralPath (Join-Path $backendRoot ".env") | Where-Object { $_ -match '^ERCLAVE_INVENTORY_DATABASE_URL=' } | Select-Object -First 1
$localDbUrl = ($envLine -split '=', 2)[1]
if ($localDbUrl -notmatch "@127\.0\.0\.1:$PostgresPort/erclave_local$") {
    throw "Guardrail: la base efectiva no es 127.0.0.1:$PostgresPort/erclave_local."
}

foreach ($portSpec in @(
    @{ Port = 4173; Name = "Frontend" },
    @{ Port = 8000; Name = "Admin API" },
    @{ Port = 8002; Name = "Production API" },
    @{ Port = 8004; Name = "Inventory API" },
    @{ Port = 8006; Name = "HR API" },
    @{ Port = 8008; Name = "Sales API" },
    @{ Port = 8010; Name = "Purchasing API" },
    @{ Port = 8012; Name = "Maintenance API" },
    @{ Port = $FirebaseAuthPort; Name = "Firebase Auth Emulator" },
    @{ Port = $FirebaseUiPort; Name = "Firebase Emulator UI" }
)) { Assert-Port-Free $portSpec.Port $portSpec.Name }

if (-not (Get-NetTCPConnection -State Listen -LocalPort $PostgresPort -ErrorAction SilentlyContinue)) {
    & (Join-Path $postgresBin "pg_ctl.exe") -D $postgresData -l $postgresLog -o "-p $PostgresPort -h 127.0.0.1" -w start
}

$env:ERCLAVE_ENVIRONMENT = "local"
$env:ERCLAVE_AUTH_MODE = "firebase"
$env:ERCLAVE_FIREBASE_PROJECT_ID = "demo-erclave"
$env:FIREBASE_AUTH_EMULATOR_HOST = "127.0.0.1:$FirebaseAuthPort"
$env:ERCLAVE_DATABASE_URL = $localDbUrl
$env:ERCLAVE_INVENTORY_DATABASE_URL = $localDbUrl
$env:ERCLAVE_HR_DATABASE_URL = $localDbUrl
$env:ERCLAVE_SALES_DATABASE_URL = $localDbUrl
$env:ERCLAVE_PURCHASING_DATABASE_URL = $localDbUrl
$env:ERCLAVE_MAINTENANCE_DATABASE_URL = $localDbUrl
$env:ERCLAVE_API_PUBLIC_BASE_URL = "http://127.0.0.1:8000"
$env:ERCLAVE_APP_PUBLIC_BASE_URL = "http://127.0.0.1:4173"
$env:ERCLAVE_ADMIN_SERVICE_URL = "http://127.0.0.1:8000"
$env:ERCLAVE_HR_SERVICE_URL = "http://127.0.0.1:8006"
$env:ERCLAVE_INVENTORY_SERVICE_URL = "http://127.0.0.1:8004"
$env:ERCLAVE_PRODUCTION_SERVICE_URL = "http://127.0.0.1:8002"
$env:ERCLAVE_MAINTENANCE_SERVICE_URL = "http://127.0.0.1:8012"
$env:ERCLAVE_BACKOFFICE_ADMIN_EMAILS = $localEmail

& $pythonPath (Join-Path $PSScriptRoot "seed_admin_mvp.py")
if ($LASTEXITCODE -ne 0) { throw "No se pudo sincronizar el catalogo de permisos local." }
& $pythonPath (Join-Path $PSScriptRoot "seed_local_demo.py")
if ($LASTEXITCODE -ne 0) { throw "No se pudo preparar el tenant demo local." }

Start-Process -FilePath "firebase.cmd" -ArgumentList "emulators:start", "--only", "auth", "--project", "demo-erclave" -WorkingDirectory $repoRoot -RedirectStandardOutput (Join-Path $repoRoot "firebase-emulator.out.log") -RedirectStandardError (Join-Path $repoRoot "firebase-emulator.err.log") -WindowStyle Hidden

$emulatorReady = $false
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    Start-Sleep -Milliseconds 500
    if (Get-NetTCPConnection -State Listen -LocalPort $FirebaseAuthPort -ErrorAction SilentlyContinue) { $emulatorReady = $true; break }
}
if (-not $emulatorReady) { throw "Firebase Auth Emulator no inicio; revisa firebase-emulator.err.log." }

$signUpBody = @{ email = $localEmail; password = $localPassword; returnSecureToken = $true } | ConvertTo-Json
try {
    Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$FirebaseAuthPort/identitytoolkit.googleapis.com/v1/accounts:signUp?key=demo-api-key" -ContentType "application/json" -Body $signUpBody | Out-Null
} catch {
    if ($_.ErrorDetails.Message -notmatch "EMAIL_EXISTS") { throw }
}

$services = @(
    @{ Adapter = "services.admin_service_adapter:app"; Port = 8000; Name = "admin-local" },
    @{ Adapter = "services.production_service_adapter:app"; Port = 8002; Name = "production-local" },
    @{ Adapter = "services.inventory_service_adapter:app"; Port = 8004; Name = "inventory-local" },
    @{ Adapter = "services.hr_service_adapter:app"; Port = 8006; Name = "hr-local" },
    @{ Adapter = "services.sales_service_adapter:app"; Port = 8008; Name = "sales-local" },
    @{ Adapter = "services.purchasing_service_adapter:app"; Port = 8010; Name = "purchasing-local" },
    @{ Adapter = "services.maintenance_service_adapter:app"; Port = 8012; Name = "maintenance-local" }
)
foreach ($service in $services) {
    Start-Process -FilePath $pythonPath -ArgumentList "-m", "uvicorn", $service.Adapter, "--host", "127.0.0.1", "--port", "$($service.Port)" -WorkingDirectory $backendRoot -RedirectStandardOutput (Join-Path $backendRoot "$($service.Name).out.log") -RedirectStandardError (Join-Path $backendRoot "$($service.Name).err.log") -WindowStyle Hidden
}
Start-Process -FilePath $pythonPath -ArgumentList "-m", "http.server", "4173", "--bind", "127.0.0.1" -WorkingDirectory $frontendRoot -RedirectStandardOutput (Join-Path $frontendRoot "frontend-local.out.log") -RedirectStandardError (Join-Path $frontendRoot "frontend-local.err.log") -WindowStyle Hidden

Start-Sleep -Seconds 3
Write-Output "Ambiente: Local aislado"
Write-Output "Firebase Auth Emulator: http://127.0.0.1:$FirebaseAuthPort"
Write-Output "Firebase Emulator UI: http://127.0.0.1:$FirebaseUiPort"
Write-Output "Frontend: http://127.0.0.1:4173"
Write-Output "APIs: 8000, 8002, 8004, 8006, 8008, 8010, 8012"
Write-Output "PostgreSQL: 127.0.0.1:$PostgresPort/erclave_local"
Write-Output "Tenant: $localTenantId"
Write-Output "Actor: $localActorId ($localEmail)"
Write-Output "Clave local del emulador: $localPassword"
