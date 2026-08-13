param(
    [Parameter(Mandatory = $true)][ValidateSet("Stage", "Promote")][string]$Mode,
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [Parameter(Mandatory = $true)][string]$Region,
    [Parameter(Mandatory = $true)][string]$AllowedEmails,
    [Parameter(Mandatory = $true)][string]$ExpectedVersion,
    [Parameter(Mandatory = $true)][string]$StatePath,
    [string]$RevisionSuffix = ""
)

$ErrorActionPreference = "Stop"
$service = "admin-service-qa"
$revisionTag = "backoffice-config"

if ($ProjectId -ne "erclave") { throw "Backoffice QA configuration is restricted to GCP project erclave." }
if ($ExpectedVersion -notmatch '^[0-9a-f]{40}$') { throw "ExpectedVersion must be a full commit SHA." }
if ($AllowedEmails.Contains("|") -or $AllowedEmails.Contains("`n") -or $AllowedEmails.Contains("`r")) {
    throw "Backoffice allowlist contains a forbidden delimiter or line break."
}

$emails = @($AllowedEmails.Split(",") | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ })
if ($emails.Count -eq 0 -or ($emails | Where-Object { $_ -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$' }).Count -gt 0) {
    throw "Backoffice allowlist must contain one or more comma-separated email addresses."
}
$normalizedEmails = ($emails | Sort-Object -Unique) -join ","

function Get-ServiceDescription {
    $json = gcloud run services describe $service `
        --project $ProjectId `
        --region $Region `
        --format json
    if ($LASTEXITCODE -ne 0) { throw "Cloud Run description failed for $service." }
    return $json | ConvertFrom-Json
}

function Get-RevisionDescription([string]$Revision) {
    $json = gcloud run revisions describe $Revision `
        --project $ProjectId `
        --region $Region `
        --format json
    if ($LASTEXITCODE -ne 0) { throw "Cloud Run revision description failed for $Revision." }
    return $json | ConvertFrom-Json
}

function Get-EnvironmentValue($RevisionDescription, [string]$Name) {
    return @($RevisionDescription.spec.containers[0].env) |
        Where-Object { $_.name -eq $Name } |
        Select-Object -ExpandProperty value -First 1
}

function Test-Revision($RevisionDescription, [string]$ExpectedImage) {
    $actualImage = $RevisionDescription.spec.containers[0].image
    $actualVersion = Get-EnvironmentValue $RevisionDescription "ERCLAVE_VERSION"
    $actualAllowlist = Get-EnvironmentValue $RevisionDescription "ERCLAVE_BACKOFFICE_ADMIN_EMAILS"
    if ($actualImage -ne $ExpectedImage) { throw "Backoffice configuration changed the certified Admin image." }
    if ($actualVersion -ne $ExpectedVersion) { throw "Backoffice configuration changed the certified Admin version." }
    if ($actualAllowlist -ne $normalizedEmails) { throw "Backoffice allowlist was not applied exactly." }
}

if ($Mode -eq "Stage") {
    if (-not $RevisionSuffix -or $RevisionSuffix -notmatch '^bo-[a-z0-9-]+$') {
        throw "Stage mode requires a safe bo-* revision suffix."
    }

    $before = Get-ServiceDescription
    $stableTraffic = @($before.status.traffic) | Where-Object { $_.percent -eq 100 -and $_.revisionName }
    if ($stableTraffic.Count -ne 1) { throw "Admin QA must have exactly one revision receiving 100 percent before staging." }
    $rollbackRevision = $stableTraffic[0].revisionName
    $rollbackDescription = Get-RevisionDescription $rollbackRevision
    $certifiedImage = $rollbackDescription.spec.containers[0].image
    $certifiedVersion = Get-EnvironmentValue $rollbackDescription "ERCLAVE_VERSION"
    if ($certifiedVersion -ne $ExpectedVersion) { throw "Active Admin QA does not run the expected certified version." }

    gcloud run services update $service `
        --project $ProjectId `
        --region $Region `
        --update-env-vars "^|^ERCLAVE_BACKOFFICE_ADMIN_EMAILS=$normalizedEmails" `
        --revision-suffix $RevisionSuffix `
        --tag $revisionTag `
        --no-traffic `
        --quiet
    if ($LASTEXITCODE -ne 0) { throw "Failed to stage the Admin QA backoffice configuration." }

    $after = Get-ServiceDescription
    $candidates = @($after.status.traffic) | Where-Object { $_.tag -eq $revisionTag -and $_.revisionName -and $_.url }
    if ($candidates.Count -ne 1) { throw "Admin QA must expose exactly one tagged backoffice configuration candidate." }
    $candidateRevision = $candidates[0].revisionName
    $candidateDescription = Get-RevisionDescription $candidateRevision
    Test-Revision $candidateDescription $certifiedImage

    $health = Invoke-RestMethod -Method Get -Uri "$($candidates[0].url)/health"
    $ready = Invoke-RestMethod -Method Get -Uri "$($candidates[0].url)/ready"
    $version = Invoke-RestMethod -Method Get -Uri "$($candidates[0].url)/version"
    if ($health.status -ne "ok" -or $health.environment -ne "qa") { throw "Admin QA candidate failed health validation." }
    if ($ready.status -ne "ready" -or -not $ready.database_configured) { throw "Admin QA candidate failed readiness validation." }
    if ($version.version -ne $ExpectedVersion) { throw "Admin QA candidate failed version validation." }

    [pscustomobject]@{
        service = $service
        candidate_revision = $candidateRevision
        rollback_revision = $rollbackRevision
        image = $certifiedImage
        version = $ExpectedVersion
    } | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding utf8
    Write-Output "[OK] Admin QA backoffice configuration staged without traffic."
    return
}

if (-not (Test-Path -LiteralPath $StatePath)) { throw "Promotion state artifact was not found." }
$state = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
if ($state.service -ne $service -or $state.version -ne $ExpectedVersion) { throw "Promotion state does not match Admin QA." }

$beforePromotion = Get-ServiceDescription
$currentStable = @($beforePromotion.status.traffic) | Where-Object { $_.percent -eq 100 -and $_.revisionName }
if ($currentStable.Count -ne 1 -or $currentStable[0].revisionName -ne $state.rollback_revision) {
    throw "Admin QA traffic changed after staging; refusing promotion."
}
$taggedCandidate = @($beforePromotion.status.traffic) |
    Where-Object { $_.tag -eq $revisionTag -and $_.revisionName -eq $state.candidate_revision }
if ($taggedCandidate.Count -ne 1) { throw "The staged backoffice candidate is no longer uniquely tagged." }

$candidateDescription = Get-RevisionDescription $state.candidate_revision
Test-Revision $candidateDescription $state.image

gcloud run services update-traffic $service `
    --project $ProjectId `
    --region $Region `
    --to-revisions "$($state.candidate_revision)=100" `
    --quiet
if ($LASTEXITCODE -ne 0) { throw "Failed to promote the Admin QA backoffice configuration." }

$afterPromotion = Get-ServiceDescription
$promoted = @($afterPromotion.status.traffic) |
    Where-Object { $_.revisionName -eq $state.candidate_revision -and $_.percent -eq 100 }
if ($promoted.Count -ne 1) { throw "Admin QA did not route 100 percent to the backoffice configuration revision." }

$stableUrl = $afterPromotion.status.url
$health = Invoke-RestMethod -Method Get -Uri "$stableUrl/health"
$ready = Invoke-RestMethod -Method Get -Uri "$stableUrl/ready"
$version = Invoke-RestMethod -Method Get -Uri "$stableUrl/version"
if ($health.status -ne "ok" -or $ready.status -ne "ready" -or $version.version -ne $ExpectedVersion) {
    throw "Stable Admin QA failed post-promotion validation."
}
Write-Output "[OK] Admin QA backoffice configuration promoted and verified."
