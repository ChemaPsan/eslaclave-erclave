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
    "production-service-qa"
)

$targets = @()
foreach ($service in $services) {
    $serviceJson = gcloud run services describe $service `
        --project $ProjectId `
        --region $Region `
        --format json
    if ($LASTEXITCODE -ne 0) { throw "Cloud Run description failed for $service." }

    $serviceDescription = $serviceJson | ConvertFrom-Json
    $candidates = @($serviceDescription.status.traffic) |
        Where-Object { $_.tag -eq $RevisionTag -and $_.revisionName }
    if ($candidates.Count -ne 1) {
        throw "$service must expose exactly one $RevisionTag revision before traffic promotion."
    }

    $targets += [pscustomobject]@{
        Service = $service
        Revision = $candidates[0].revisionName
    }
}

if ($targets.Count -ne $services.Count) {
    throw "QA traffic preflight did not resolve every required service."
}

foreach ($target in $targets) {
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
    $activeTraffic = @($serviceDescription.status.traffic) |
        Where-Object { $_.revisionName -eq $target.Revision -and $_.percent -eq 100 }
    if ($activeTraffic.Count -ne 1) {
        throw "$($target.Service) did not route 100 percent to $($target.Revision)."
    }
    Write-Output "[OK] $($target.Service) routes 100 percent to $($target.Revision)."
}
