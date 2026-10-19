param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [Parameter(Mandatory = $true)][string]$Region,
    [Parameter(Mandatory = $true)][string]$RevisionTag,
    [Parameter(Mandatory = $true)][string]$ExpectedVersion,
    [Parameter(Mandatory = $true)][string]$ImageManifestPath,
    [string]$CandidateManifestPath = 'qa-candidate-revisions.json'
)

$ErrorActionPreference = "Stop"

if ($ProjectId -ne "erclave") { throw "QA smoke is restricted to GCP project erclave." }
if ($RevisionTag -ne "candidate") { throw "QA smoke must target the candidate traffic tag." }
if ($ExpectedVersion -notmatch '^[0-9a-f]{40}$') { throw "ExpectedVersion must be a full commit SHA." }

. (Join-Path $PSScriptRoot 'qa_candidate_identity.ps1')
$images = Read-QaImages $ImageManifestPath
$certified = @()

foreach ($service in $qaServices) {
    $identity = Get-QaCandidateIdentity $service $images[$service] $ExpectedVersion
    $url = $identity.Url

    $health = Invoke-RestMethod -Method Get -Uri "$url/health"
    $ready = Invoke-RestMethod -Method Get -Uri "$url/ready"
    $version = Invoke-RestMethod -Method Get -Uri "$url/version"

    if ($health.status -ne "ok" -or $health.environment -ne "qa") {
        throw "$service failed environment health validation."
    }
    if ($ready.status -ne "ready" -or -not $ready.database_configured) {
        throw "$service failed database readiness validation."
    }
    if ($version.version -ne $ExpectedVersion) {
        throw "$service does not run the approved commit version."
    }
    $publicUrl = [Uri]$version.api_public_base_url
    if ($publicUrl.Scheme -ne "https" -or $publicUrl.Host -in @("localhost", "127.0.0.1")) {
        throw "$service exposes an invalid public API URL."
    }
    Write-Output "[OK] $service candidate health, readiness and version validated."
    $certified += $identity
}

# Refuse to certify tags that moved while the eight candidate probes ran.
foreach ($identity in $certified) {
    Assert-QaCandidateIdentity (Get-QaCandidateIdentity $identity.Service $images[$identity.Service] $ExpectedVersion) $identity
}
[pscustomobject]@{ ProjectId=$ProjectId; Region=$Region; SourceSha=$ExpectedVersion; RevisionTag=$RevisionTag; Services=$certified } |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $CandidateManifestPath -Encoding utf8
