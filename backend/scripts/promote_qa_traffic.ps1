param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [Parameter(Mandatory = $true)][string]$Region,
    [Parameter(Mandatory = $true)][string]$RevisionTag
)

$ErrorActionPreference = "Stop"

if ($ProjectId -ne "erclave") { throw "QA traffic promotion is restricted to GCP project erclave." }
if ($RevisionTag -ne "candidate") { throw "QA traffic promotion requires the candidate revision tag." }

$services = @(
    "admin-service-qa",
    "inventory-service-qa",
    "hr-service-qa",
    "production-service-qa",
    "sales-service-qa",
    "purchasing-service-qa",
    "maintenance-service-qa"
)

$targets = @()
foreach ($service in $services) {
    $serviceJson = gcloud run services describe $service `
        --project $ProjectId `
        --region $Region `
        --format json
    if ($LASTEXITCODE -ne 0) { throw "Cloud Run description failed for $service." }

    $serviceDescription = $serviceJson | ConvertFrom-Json
    $candidates = @($serviceDescription.status.traffic |
        Where-Object { $_.tag -eq $RevisionTag -and $_.revisionName })
    if ($candidates.Count -ne 1) {
        throw "$service must expose exactly one $RevisionTag revision before traffic promotion."
    }

    $targets += [pscustomobject]@{
        Service = $service
        Revision = $candidates[0].revisionName
        Previous = @($serviceDescription.status.traffic | Where-Object { $_.percent -gt 0 } | ForEach-Object { "$($_.revisionName)=$($_.percent)" }) -join ','
    }
}

if ($targets.Count -ne $services.Count) {
    throw "QA traffic preflight did not resolve every required service."
}

$targets | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "qa-traffic-rollback.json" -Encoding utf8
Write-Output ($targets | ConvertTo-Json -Compress)
if (@($targets | Where-Object { -not $_.Previous }).Count) { throw "Every existing service requires recorded rollback traffic." }

$changed = @()
try {
foreach ($target in $targets) {
    $current = gcloud run services describe $target.Service --project $ProjectId --region $Region --format json
    if ($LASTEXITCODE -ne 0) { throw "Traffic drift check failed for $($target.Service)." }
    $currentTraffic = @((($current | ConvertFrom-Json).status.traffic) | Where-Object { $_.percent -gt 0 } | ForEach-Object { "$($_.revisionName)=$($_.percent)" }) -join ','
    if ($currentTraffic -ne $target.Previous) { throw "Stable traffic drift detected for $($target.Service)." }
    # Include the attempted service: an unsuccessful response can still have applied traffic.
    $changed += $target
    gcloud run services update-traffic $target.Service `
        --project $ProjectId `
        --region $Region `
        --to-revisions "$($target.Revision)=100" `
        --quiet
    if ($LASTEXITCODE -ne 0) { throw "Traffic promotion failed for $($target.Service)." }
}

foreach ($target in $targets) {
    $serviceJson = gcloud run services describe $target.Service `
        --project $ProjectId `
        --region $Region `
        --format json
    if ($LASTEXITCODE -ne 0) { throw "Post-promotion description failed for $($target.Service)." }

    $serviceDescription = $serviceJson | ConvertFrom-Json
    $activeTraffic = @($serviceDescription.status.traffic |
        Where-Object { $_.revisionName -eq $target.Revision -and $_.percent -eq 100 })
    if ($activeTraffic.Count -ne 1) {
        throw "$($target.Service) did not route 100 percent to $($target.Revision)."
    }
    Write-Output "[OK] $($target.Service) routes 100 percent to $($target.Revision)."
}
} catch {
    $promotionError = $_
    $rollbackFailures = @()
    [array]::Reverse($changed)
    foreach ($target in $changed) {
        gcloud run services update-traffic $target.Service --project $ProjectId --region $Region --to-revisions $target.Previous --quiet
        if ($LASTEXITCODE -ne 0) { $rollbackFailures += $target.Service; continue }
        $restored = gcloud run services describe $target.Service --project $ProjectId --region $Region --format json
        if ($LASTEXITCODE -ne 0) { $rollbackFailures += $target.Service; continue }
        $restoredTraffic = @((($restored | ConvertFrom-Json).status.traffic) | Where-Object { $_.percent -gt 0 } | ForEach-Object { "$($_.revisionName)=$($_.percent)" }) -join ','
        if ($restoredTraffic -ne $target.Previous) { $rollbackFailures += $target.Service }
    }
    if ($rollbackFailures.Count) { throw "Promotion failed; manual rollback required for $($rollbackFailures -join ','). See qa-traffic-rollback.json. Original failure: $promotionError" }
    throw "Promotion failed; all attempted services restored to recorded traffic. Original failure: $promotionError"
}
