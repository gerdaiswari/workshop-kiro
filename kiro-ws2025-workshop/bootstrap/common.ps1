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

function Assert-FileIntegrity {
    param(
        [Parameter(Mandatory)][string]$Path,
        [long]$MinimumBytes = 1024,
        [string]$ExpectedMagic = '',
        [string]$ExpectedSha256 = ''
    )
    if (-not (Test-Path $Path -PathType Leaf)) { throw "File does not exist: $Path" }
    $file = Get-Item $Path
    if ($file.Length -lt $MinimumBytes) { throw "File is too small: $($file.Length) bytes; expected at least $MinimumBytes" }
    if ($ExpectedMagic) {
        $stream = [IO.File]::OpenRead($Path)
        try {
            $bytes = New-Object byte[] $ExpectedMagic.Length
            [void]$stream.Read($bytes, 0, $bytes.Length)
            $actualMagic = [Text.Encoding]::ASCII.GetString($bytes)
        } finally { $stream.Dispose() }
        if ($actualMagic -ne $ExpectedMagic) { throw "File signature '$actualMagic' does not match expected '$ExpectedMagic'" }
    }
    if ($ExpectedSha256) {
        $actualSha256 = (Get-FileHash -Path $Path -Algorithm SHA256).Hash
        if ($actualSha256 -ne $ExpectedSha256) { throw "File SHA-256 '$actualSha256' does not match expected '$ExpectedSha256'" }
    }
}

function Invoke-Download {
    param(
        [Parameter(Mandatory)][string]$Uri,
        [Parameter(Mandatory)][string]$OutFile,
        [int]$Attempts = 4,
        [long]$MinimumBytes = 1024,
        [string]$ExpectedMagic = ''
    )
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutFile) | Out-Null
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            Remove-Item $OutFile -Force -ErrorAction SilentlyContinue
            Write-Step "Download $Uri (attempt $attempt/$Attempts)"
            Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $OutFile -MaximumRedirection 10
            $file = Get-Item $OutFile
            if ($file.Length -lt $MinimumBytes) { throw "Downloaded file is too small: $($file.Length) bytes; expected at least $MinimumBytes" }
            if ($ExpectedMagic) {
                $stream = [IO.File]::OpenRead($OutFile)
                try {
                    $bytes = New-Object byte[] $ExpectedMagic.Length
                    [void]$stream.Read($bytes, 0, $bytes.Length)
                    $actualMagic = [Text.Encoding]::ASCII.GetString($bytes)
                } finally { $stream.Dispose() }
                if ($actualMagic -ne $ExpectedMagic) { throw "Downloaded file signature '$actualMagic' does not match expected '$ExpectedMagic'" }
            }
            return
        } catch {
            Remove-Item $OutFile -Force -ErrorAction SilentlyContinue
            Write-Step "Download rejected: $($_.Exception.Message)"
            if ($attempt -eq $Attempts) { throw }
            Start-Sleep -Seconds (10 * $attempt)
        }
    }
}

function Invoke-DownloadWithFallback {
    param(
        [Parameter(Mandatory)][string[]]$Uris,
        [Parameter(Mandatory)][string]$OutFile,
        [long]$MinimumBytes = 1024,
        [string]$ExpectedMagic = ''
    )
    $failures = @()
    foreach ($uri in $Uris) {
        try {
            Invoke-Download -Uri $uri -OutFile $OutFile -Attempts 2 -MinimumBytes $MinimumBytes -ExpectedMagic $ExpectedMagic
            return
        } catch { $failures += "$uri => $($_.Exception.Message)" }
    }
    throw "All download mirrors failed: $($failures -join ' | ')"
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
