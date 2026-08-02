#Requires -Version 5.1
<#
.SYNOPSIS
  Deploy the Kiro Windows Server 2019-to-2025 upgrade workshop lab.
.DESCRIPTION
  Windows-native equivalent of scripts/00_deploy.sh.
  Packages the bootstrap payload, caches the XAMPP installer from the operator
  workstation, uploads both to S3, and deploys infra/lab.yaml via CloudFormation.
.PARAMETER Region
  AWS region (e.g. us-east-1).
.PARAMETER Profile
  Optional AWS CLI profile name. Omit it to use Workshop Studio environment credentials.
.PARAMETER StackName
  CloudFormation stack name (default: kiro-ws2025-lab).
#>
param(
    [Parameter(Mandatory)][string]$Region,
    [string]$Profile,
    [string]$StackName = 'kiro-ws2025-lab'
)
$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

if (-not (Get-Command 'aws' -ErrorAction SilentlyContinue)) {
    Write-Error 'aws is required but not found in PATH'; exit 1
}
if (Get-Command 'python3' -ErrorAction SilentlyContinue) {
    $PythonExe = 'python3'; $PythonPrefix = @()
} elseif (Get-Command 'python' -ErrorAction SilentlyContinue) {
    $PythonExe = 'python'; $PythonPrefix = @()
} elseif (Get-Command 'py' -ErrorAction SilentlyContinue) {
    $PythonExe = 'py'; $PythonPrefix = @('-3')
} else {
    Write-Error 'Python 3 is required. Install Python 3, reopen PowerShell, and retry.'; exit 1
}
$pythonVersion = & $PythonExe @PythonPrefix --version 2>&1
if ($LASTEXITCODE -ne 0 -or $pythonVersion -notmatch 'Python 3\.') {
    Write-Error "The selected launcher is not Python 3: $pythonVersion"; exit 1
}

$AwsContext = @('--region', $Region)
$ProfileDisplay = 'environment'
if ($Profile) {
    $AwsContext += @('--profile', $Profile)
    $ProfileDisplay = $Profile
}

$AccountId = (aws sts get-caller-identity --query Account --output text @AwsContext).Trim()
$SafeStack = ($StackName.ToLower() -replace '[^a-z0-9-]', '-')
$Bucket = "kiro-ws2025-$AccountId-$Region-$SafeStack"
$ArtifactKey = 'payload/workshop-payload.zip'
$XamppKey = 'dependencies/xampp-windows-x64-8.2.12-0-VS16-installer.exe'
$XamppSize = '157583456'
$XamppSha256 = '12e818ce5aec79fe646606df3a80b35da865ec0213646ad7c92044dcfcec7535'

$DeployDir = Join-Path $Root 'results\deployment'
New-Item -ItemType Directory -Force -Path $DeployDir | Out-Null
$XamppFile = Join-Path $DeployDir 'xampp-windows-x64-8.2.12-0-VS16-installer.exe'
$ZipFile = Join-Path $DeployDir 'workshop-payload.zip'

$ExistingStatus = (aws cloudformation describe-stacks --stack-name $StackName `
    --query 'Stacks[0].StackStatus' --output text @AwsContext 2>$null)
if ($ExistingStatus -eq 'ROLLBACK_COMPLETE') {
    Write-Error @"
Stack $StackName is ROLLBACK_COMPLETE and cannot be updated.
Review its failed events and durable S3 logs before deleting only the failed stack.
Use the same environment credentials or optional named profile used for deployment.
"@
    exit 3
}

Write-Host 'Packaging bootstrap payload...'
& $PythonExe @PythonPrefix "$Root\scripts\lib\package_payload.py" --root $Root --output $ZipFile
if ($LASTEXITCODE -ne 0) { throw 'Payload packaging failed' }

$bucketExists = $true
aws s3api head-bucket --bucket $Bucket @AwsContext 2>$null
if ($LASTEXITCODE -ne 0) { $bucketExists = $false }
if (-not $bucketExists) {
    Write-Host "Creating artifact bucket: $Bucket"
    if ($Region -eq 'us-east-1') {
        aws s3api create-bucket --bucket $Bucket @AwsContext | Out-Null
    } else {
        aws s3api create-bucket --bucket $Bucket `
            --create-bucket-configuration "LocationConstraint=$Region" @AwsContext | Out-Null
    }
    aws s3api put-public-access-block --bucket $Bucket `
        --public-access-block-configuration 'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true' `
        @AwsContext
    aws s3api put-bucket-encryption --bucket $Bucket `
        --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' `
        @AwsContext
}

Write-Host 'Clearing stale bootstrap logs...'
aws s3 rm "s3://$Bucket/logs/$StackName/" --recursive --only-show-errors @AwsContext 2>$null

$remoteXampp = (aws s3api head-object --bucket $Bucket --key $XamppKey `
    --query '[ContentLength,Metadata.sha256]' --output text @AwsContext 2>$null)
$remoteParts = if ($remoteXampp) { $remoteXampp.Trim() -split '\s+' } else { @('', '') }
if ($remoteParts[0] -ne $XamppSize -or $remoteParts[1] -ne $XamppSha256) {
    Write-Host 'Downloading and validating XAMPP installer...'
    & $PythonExe @PythonPrefix "$Root\scripts\lib\cache_dependency.py" `
        --url 'https://netix.dl.sourceforge.net/project/xampp/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe' `
        --url 'https://master.dl.sourceforge.net/project/xampp/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe' `
        --url 'https://phoenixnap.dl.sourceforge.net/project/xampp/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe' `
        --url 'https://onboardcloud.dl.sourceforge.net/project/xampp/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe' `
        --output $XamppFile --minimum-bytes 150000000 --magic MZ --sha256 $XamppSha256
    if ($LASTEXITCODE -ne 0) { throw 'XAMPP dependency cache failed' }
    aws s3 cp $XamppFile "s3://$Bucket/$XamppKey" `
        --metadata "sha256=$XamppSha256" --only-show-errors @AwsContext
} else {
    Write-Host "Reusing validated S3 dependency: s3://$Bucket/$XamppKey"
}

aws s3 cp $ZipFile "s3://$Bucket/$ArtifactKey" --only-show-errors @AwsContext

Write-Host 'Deploying CloudFormation stack...'
aws cloudformation deploy `
    --template-file "$Root\infra\lab.yaml" `
    --stack-name $StackName `
    --capabilities CAPABILITY_NAMED_IAM `
    --parameter-overrides "ArtifactBucketName=$Bucket" "ArtifactKey=$ArtifactKey" "XamppArtifactKey=$XamppKey" `
    --no-fail-on-empty-changeset @AwsContext

if ($LASTEXITCODE -ne 0) {
    Write-Host 'CloudFormation deployment failed. Failed resources:' -ForegroundColor Red
    aws cloudformation describe-stack-events --stack-name $StackName `
        --query "StackEvents[?contains(ResourceStatus, 'FAILED')].[Timestamp,LogicalResourceId,ResourceStatusReason]" `
        --output table @AwsContext
    Write-Host 'Durable bootstrap logs, if uploaded:'
    aws s3 ls "s3://$Bucket/logs/$StackName/" --recursive @AwsContext
    exit 1
}

aws cloudformation describe-stacks --stack-name $StackName `
    --output json @AwsContext | Out-File "$DeployDir\stack.json" -Encoding utf8

$stateJson = @{
    stack_name = $StackName; region = $Region; profile = $ProfileDisplay
    artifact_bucket = $Bucket; created_at = (Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json
Set-Content "$DeployDir\state.json" $stateJson -Encoding UTF8

$Dns = (aws cloudformation describe-stacks --stack-name $StackName `
    --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDns'].OutputValue | [0]" `
    --output text @AwsContext).Trim()
Write-Host "`nLab ready. ALB: http://$Dns/" -ForegroundColor Green
Write-Host "State: $DeployDir\state.json"
