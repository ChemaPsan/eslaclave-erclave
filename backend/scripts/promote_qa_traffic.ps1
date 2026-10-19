param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [Parameter(Mandatory = $true)][string]$Region,
    [Parameter(Mandatory = $true)][string]$RevisionTag,
    [Parameter(Mandatory = $true)][string]$ExpectedVersion,
    [Parameter(Mandatory = $true)][string]$ImageManifestPath,
    [Parameter(Mandatory = $true)][string]$CandidateManifestPath
)

$ErrorActionPreference = "Stop"

if ($ProjectId -ne "erclave") { throw "QA traffic promotion is restricted to GCP project erclave." }
if ($RevisionTag -ne "candidate") { throw "QA traffic promotion requires the candidate revision tag." }
if ($ExpectedVersion -notmatch '^[0-9a-f]{40}$') { throw 'ExpectedVersion must be a full commit SHA.' }
. (Join-Path $PSScriptRoot 'qa_candidate_identity.ps1')
$images = Read-QaImages $ImageManifestPath
$manifest = Get-Content -LiteralPath $CandidateManifestPath -Raw | ConvertFrom-Json
if ($manifest.ProjectId -cne $ProjectId -or $manifest.Region -cne $Region -or $manifest.SourceSha -cne $ExpectedVersion -or $manifest.RevisionTag -cne $RevisionTag) {
    throw 'Certified candidate manifest does not match the approved release.'
}
$certified = @{}
foreach ($identity in @($manifest.Services)) {
    if ($identity.Service -notin $qaServices -or $certified.ContainsKey($identity.Service) -or $identity.Image -cne $images[$identity.Service] -or $identity.Version -cne $ExpectedVersion) {
        throw 'Invalid, duplicate or drifted certified service binding.'
    }
    $certified[$identity.Service] = $identity
}
if ($certified.Count -ne 8) { throw 'Exactly eight certified candidate revisions are required.' }

$services = $qaServices

$targets = @()
foreach ($service in $services) {
    $identity = Get-QaCandidateIdentity $service $images[$service] $ExpectedVersion
    Assert-QaCandidateIdentity $identity $certified[$service]
    if ($identity.Previous -cne $certified[$service].Previous) { throw "Certified stable traffic drift detected for $service." }
    $targets += $identity
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
    $current = Get-QaCandidateIdentity $target.Service $images[$target.Service] $ExpectedVersion
    Assert-QaCandidateIdentity $current $certified[$target.Service]
    if ($current.Previous -ne $target.Previous) { throw "Stable traffic drift detected for $($target.Service)." }
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
    Assert-QaCandidateIdentity (Get-QaCandidateIdentity $target.Service $images[$target.Service] $ExpectedVersion) $certified[$target.Service]
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
