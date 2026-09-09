$ErrorActionPreference = 'Stop'
$script:serviceNames = @('admin','inventory','hr','production','sales','purchasing','maintenance') | ForEach-Object { "$_-service-qa" }
$promoter = Join-Path $PSScriptRoot 'promote_qa_traffic.ps1'
$testDirectory = Join-Path ([IO.Path]::GetTempPath()) ('erclave-traffic-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testDirectory | Out-Null
function global:gcloud {
    $commandArgs = @($args)
    $serviceName = $commandArgs[3]
    $global:LASTEXITCODE = 0
    if ($commandArgs[2] -eq 'describe') {
        $traffic = @(@{revisionName="$serviceName-old";percent=100},@{revisionName="$serviceName-new";percent=0;tag='candidate'})
        if ($global:qaTrafficTestActive[$serviceName] -eq 'new') { $traffic[0].percent=0; $traffic[1].percent=100 }
        return @{status=@{traffic=$traffic}} | ConvertTo-Json -Depth 5 -Compress
    }
    if ($commandArgs[2] -ne 'update-traffic') { throw 'Unexpected gcloud command in test' }
    $target = $commandArgs[[array]::IndexOf($commandArgs,'--to-revisions')+1]
    $global:qaTrafficTestActive[$serviceName] = if($target -like '*-new=100'){'new'}else{'old'}
    # Simulate a failure response after the provider already changed traffic.
    if ($global:qaTrafficTestFailOnce -and $serviceName -eq 'production-service-qa' -and $target -like '*-new=100') {
        $global:qaTrafficTestFailOnce=$false;$global:LASTEXITCODE=1
    }
}
try {
    Push-Location $testDirectory
    foreach ($scenario in @('success','partial_failure')) {
        $global:qaTrafficTestActive=@{};foreach($serviceName in $script:serviceNames){$global:qaTrafficTestActive[$serviceName]='old'}
        $global:qaTrafficTestFailOnce=$scenario -eq 'partial_failure';$failed=$false
        try { & $promoter -ProjectId erclave -Region us-central1 -RevisionTag candidate | Out-Null } catch { if($scenario -eq 'success'){throw}; $failed=$true }
        if ($scenario -eq 'success' -and ($failed -or @($global:qaTrafficTestActive.Values | Where-Object {$_ -ne 'new'}).Count)) { throw 'Successful promotion did not route every service.' }
        if ($scenario -eq 'partial_failure' -and (-not $failed -or @($global:qaTrafficTestActive.Values | Where-Object {$_ -ne 'old'}).Count)) { throw 'Partial promotion was not fully compensated.' }
        $record=Get-Content -LiteralPath qa-traffic-rollback.json -Raw | ConvertFrom-Json
        if ($record.Count -ne 7 -or @($record | Where-Object {$_.Previous -notlike '*-old=100'}).Count) { throw 'Rollback evidence is incomplete.' }
        Write-Output "[OK] Traffic test: $scenario"
    }
} finally {
    Pop-Location
    Remove-Item Function:/gcloud
    Remove-Item -LiteralPath (Join-Path $testDirectory 'qa-traffic-rollback.json') -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $testDirectory
}
