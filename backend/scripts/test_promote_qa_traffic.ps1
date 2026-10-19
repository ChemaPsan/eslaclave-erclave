$ErrorActionPreference = 'Stop'
$script:serviceNames = @('admin','inventory','hr','production','sales','purchasing','maintenance','costing') | ForEach-Object { "$_-service-qa" }
$promoter = Join-Path $PSScriptRoot 'promote_qa_traffic.ps1'
$smoke = Join-Path $PSScriptRoot 'smoke_qa.ps1'
$testDirectory = Join-Path ([IO.Path]::GetTempPath()) ('erclave-traffic-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testDirectory | Out-Null
$global:qaTestSha='a'*40
$global:qaTestImages=@{}
foreach($name in $script:serviceNames){$global:qaTestImages[$name]='us-central1-docker.pkg.dev/erclave/qa/'+$name.Replace('-qa','')+'@sha256:'+('b'*64)}
function global:gcloud {
    $commandArgs = @($args);$name = $commandArgs[3];$global:LASTEXITCODE = 0
    if ($commandArgs[1] -eq 'revisions' -and $commandArgs[2] -eq 'describe') {
        # A moved tag may still carry the same approved digest and SHA.
        $serviceName=$name -replace '-(new|other)$',''
        $image=$global:qaTestImages[$serviceName];$version=$global:qaTestSha
        if($global:qaTestDrift -eq 'digest' -and $serviceName -eq $global:qaTestDriftService){$image=$image.Replace(('b'*64),('c'*64))}
        if($global:qaTestDrift -eq 'sha' -and $serviceName -eq $global:qaTestDriftService){$version='d'*40}
        return @{metadata=@{name=$name;labels=@{'serving.knative.dev/service'=$serviceName}};spec=@{containers=@(@{image=$image;env=@(@{name='ERCLAVE_VERSION';value=$version})})};status=@{imageDigest=$image}} | ConvertTo-Json -Depth 8 -Compress
    }
    $serviceName=$name
    if ($commandArgs[1] -eq 'services' -and $commandArgs[2] -eq 'describe') {
        $revision="$serviceName-new"
        if($global:qaTestDrift -eq 'tag' -and $serviceName -eq $global:qaTestDriftService){$revision="$serviceName-other"}
        $traffic = @(@{revisionName="$serviceName-old";percent=100},@{revisionName=$revision;percent=0;tag='candidate';url="https://candidate---$serviceName.run.app"})
        if ($global:qaTrafficTestActive[$serviceName] -eq 'new') { $traffic[0].percent=0; $traffic[1].percent=100 }
        if($global:qaTestDrift -eq 'stable' -and $serviceName -eq $global:qaTestDriftService -and $global:qaTrafficTestActive[$serviceName] -eq 'old'){$traffic[0].revisionName="$serviceName-other-stable"}
        return @{status=@{traffic=$traffic}} | ConvertTo-Json -Depth 5 -Compress
    }
    if ($commandArgs[2] -ne 'update-traffic') { throw 'Unexpected gcloud command in test' }
    $global:qaTestMutationCount++
    $target = $commandArgs[[array]::IndexOf($commandArgs,'--to-revisions')+1]
    if($target -like '*-old=100' -and $global:qaTestDrift -eq 'stable' -and $serviceName -eq $global:qaTestDriftService){$global:qaTestDrift=''}
    $global:qaTrafficTestActive[$serviceName] = if($target -like '*-new=100'){'new'}else{'old'}
    if ($global:qaTrafficTestFailOnce -and $serviceName -eq $global:qaTrafficTestFailService -and $target -like '*-new=100') {
        $global:qaTrafficTestFailOnce=$false;$global:LASTEXITCODE=1
    }
    if($global:qaTestMutationCount -eq 1 -and $global:qaTestScenario -like 'during_*') {
        $global:qaTestDrift=$global:qaTestScenario.Substring(7);$global:qaTestDriftService='hr-service-qa'
    }
    if($global:qaTestMutationCount -eq 8 -and $global:qaTestScenario -eq 'postflight_tag') {
        $global:qaTestDrift='tag';$global:qaTestDriftService='admin-service-qa'
    }
}
function global:Invoke-RestMethod {
    param($Method,$Uri)
    if($Uri -like '*/health'){return @{status='ok';environment='qa'}}
    if($Uri -like '*/ready'){return @{status='ready';database_configured=$true}}
    if($Uri -like '*/version'){return @{version=$global:qaTestSha;api_public_base_url='https://service.run.app'}}
    throw 'Unexpected HTTP probe in test'
}
try {
    Push-Location $testDirectory
    @($global:qaTestImages.Keys | Sort-Object | ForEach-Object {($_ -replace '-service-qa$','').ToUpperInvariant()+'_IMAGE='+$global:qaTestImages[$_]}) | Set-Content -LiteralPath images.env
    $global:qaTrafficTestActive=@{};foreach($name in $script:serviceNames){$global:qaTrafficTestActive[$name]='old'}
    $global:qaTestDrift='';$global:qaTestMutationCount=0
    & $smoke -ProjectId erclave -Region us-central1 -RevisionTag candidate -ExpectedVersion $global:qaTestSha -ImageManifestPath images.env -CandidateManifestPath certified.json | Out-Null
    $certificate=Get-Content certified.json -Raw | ConvertFrom-Json
    if($certificate.Services.Count -ne 8 -or $global:qaTestMutationCount){throw 'Smoke did not certify exactly eight services without writes.'}
    Write-Output '[OK] Smoke certifies eight immutable revision/image/SHA bindings'
    foreach ($scenario in @('success','partial_failure','costing_partial_failure','preflight_tag','preflight_digest','preflight_sha','preflight_stable','during_tag','during_digest','during_sha','during_stable','postflight_tag')) {
        $global:qaTestScenario=$scenario;$global:qaTestMutationCount=0;$global:qaTestDrift='';$global:qaTestDriftService='costing-service-qa'
        if($scenario -like 'preflight_*'){$global:qaTestDrift=$scenario.Substring(10)}
        $global:qaTrafficTestActive=@{};foreach($name in $script:serviceNames){$global:qaTrafficTestActive[$name]='old'}
        $global:qaTrafficTestFailOnce=$scenario -in @('partial_failure','costing_partial_failure');$failed=$false
        $global:qaTrafficTestFailService=if($scenario -eq 'costing_partial_failure'){'costing-service-qa'}else{'production-service-qa'}
        try { & $promoter -ProjectId erclave -Region us-central1 -RevisionTag candidate -ExpectedVersion $global:qaTestSha -ImageManifestPath images.env -CandidateManifestPath certified.json | Out-Null } catch { if($scenario -eq 'success'){throw}; $failed=$true }
        if ($scenario -eq 'success' -and ($failed -or @($global:qaTrafficTestActive.Values | Where-Object {$_ -ne 'new'}).Count)) { throw 'Successful promotion did not route every service.' }
        if ($scenario -ne 'success' -and (-not $failed -or @($global:qaTrafficTestActive.Values | Where-Object {$_ -ne 'old'}).Count)) { throw "Unsafe drift/failure handling: $scenario" }
        if($scenario -like 'preflight_*' -and $global:qaTestMutationCount -ne 0){throw 'Preflight drift mutated traffic.'}
        if($scenario -notlike 'preflight_*') {
            $record=Get-Content -LiteralPath qa-traffic-rollback.json -Raw | ConvertFrom-Json
            if ($record.Count -ne 8 -or @($record | Where-Object {$_.Previous -notlike '*-old=100'}).Count) { throw 'Rollback evidence is incomplete.' }
        }
        Write-Output "[OK] Traffic test: $scenario"
    }
} finally {
    Pop-Location
    Remove-Item Function:/gcloud
    Remove-Item Function:/Invoke-RestMethod
    foreach($file in @('qa-traffic-rollback.json','images.env','certified.json')) {Remove-Item -LiteralPath (Join-Path $testDirectory $file) -ErrorAction SilentlyContinue}
    Remove-Item -LiteralPath $testDirectory
}
