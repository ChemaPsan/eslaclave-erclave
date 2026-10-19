# Shared read-only identity checks for certification and traffic promotion.
$qaServices = @('admin','inventory','hr','production','sales','purchasing','maintenance','costing') | ForEach-Object { "$_-service-qa" }

function Read-QaImages([string]$Path) {
    $images = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -notmatch '^([A-Z]+)_IMAGE=(.+@sha256:[0-9a-f]{64})$') { throw 'Invalid immutable image binding.' }
        $service = $Matches[1].ToLowerInvariant() + '-service-qa'
        if ($service -notin $qaServices -or $images.ContainsKey($service)) { throw 'Unexpected or duplicate image binding.' }
        $images[$service] = $Matches[2]
    }
    if ($images.Count -ne 8) { throw 'Exactly eight immutable image bindings are required.' }
    return $images
}

function Get-QaCandidateIdentity([string]$Service, [string]$Image, [string]$Version) {
    $description = gcloud run services describe $Service --project $ProjectId --region $Region --format json
    if ($LASTEXITCODE -ne 0) { throw "Cloud Run description failed for $Service." }
    $description = $description | ConvertFrom-Json
    $tagged = @($description.status.traffic | Where-Object { $_.tag -eq $RevisionTag -and $_.revisionName })
    if ($tagged.Count -ne 1 -or -not $tagged[0].url) { throw "$Service must expose exactly one candidate revision and URL." }
    $revisionName = $tagged[0].revisionName
    $revision = gcloud run revisions describe $revisionName --project $ProjectId --region $Region --format json
    if ($LASTEXITCODE -ne 0) { throw "Cloud Run revision description failed for $Service." }
    $revision = $revision | ConvertFrom-Json
    $containers = @($revision.spec.containers)
    $versions = @($containers[0].env | Where-Object { $_.name -eq 'ERCLAVE_VERSION' })
    if ($revision.metadata.name -ne $revisionName -or $revision.metadata.labels.'serving.knative.dev/service' -ne $Service -or
        $containers.Count -ne 1 -or $containers[0].image -ne $Image -or $revision.status.imageDigest -ne $Image -or
        $versions.Count -ne 1 -or $versions[0].value -ne $Version) {
        throw "Candidate SHA or immutable image drift detected for $Service."
    }
    return [pscustomobject]@{
        Service = $Service; Revision = $revisionName; Image = $Image; Version = $Version; Url = $tagged[0].url
        Previous = @($description.status.traffic | Where-Object { $_.percent -gt 0 } | ForEach-Object { "$($_.revisionName)=$($_.percent)" }) -join ','
    }
}

function Assert-QaCandidateIdentity($Actual, $Certified) {
    foreach ($field in @('Service','Revision','Image','Version','Url')) {
        if ($Actual.$field -cne $Certified.$field) { throw "Certified candidate $field drift detected for $($Actual.Service)." }
    }
}
