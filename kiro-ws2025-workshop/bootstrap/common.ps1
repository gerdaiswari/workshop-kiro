Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Write-Step {
    param([Parameter(Mandatory)][string]$Message)
    $line = "[{0:u}] {1}" -f (Get-Date), $Message
    Write-Host $line
    Add-Content -Path 'C:\Workshop\bootstrap.log' -Value $line
}

function Invoke-Download {
    param(
        [Parameter(Mandatory)][string]$Uri,
        [Parameter(Mandatory)][string]$OutFile,
        [int]$Attempts = 4
    )
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutFile) | Out-Null
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            Write-Step "Download $Uri (attempt $attempt/$Attempts)"
            Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $OutFile -MaximumRedirection 10
            if ((Get-Item $OutFile).Length -lt 1024) { throw "Downloaded file is unexpectedly small" }
            return
        } catch {
            if ($attempt -eq $Attempts) { throw }
            Start-Sleep -Seconds (10 * $attempt)
        }
    }
}

function Invoke-CheckedProcess {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [string]$ArgumentList = '',
        [int[]]$SuccessCodes = @(0, 1641, 3010)
    )
    Write-Step "Run executable: $FilePath"
    $process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -Wait -PassThru -NoNewWindow
    if ($process.ExitCode -notin $SuccessCodes) {
        throw "$FilePath failed with exit code $($process.ExitCode)"
    }
    return $process.ExitCode
}

function Install-Msi {
    param([string]$Path, [string]$Arguments = '')
    $allArguments = "/i `"$Path`" /qn /norestart $Arguments"
    Invoke-CheckedProcess -FilePath 'msiexec.exe' -ArgumentList $allArguments | Out-Null
}

function Wait-Http {
    param([string]$Uri, [int]$TimeoutSeconds = 180)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 10
            if ($response.StatusCode -eq 200) { return }
        } catch { Start-Sleep -Seconds 5 }
    } while ((Get-Date) -lt $deadline)
    throw "Timed out waiting for $Uri"
}

function Refresh-ProcessPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Set-RestrictedSecretFile {
    param([string]$Path, [string]$Content)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path) | Out-Null
    Set-Content -Path $Path -Value $Content -Encoding UTF8
    & icacls.exe $Path /inheritance:r /grant:r 'SYSTEM:F' 'Administrators:F' | Out-Null
}
