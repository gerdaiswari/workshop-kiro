#Requires -Version 5.1
<#
.SYNOPSIS
  Review or remove recorded workshop resources.
.DESCRIPTION
  Windows-native equivalent of scripts/08_cleanup.sh. Use -Plan first, review
  the output, then use -Execute only after explicit approval.
#>
[CmdletBinding(DefaultParameterSetName = 'Plan')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Plan')][switch]$Plan,
    [Parameter(Mandatory, ParameterSetName = 'Execute')][switch]$Execute,
    [Parameter(Mandatory)][string]$Region,
    [string]$Profile,
    [string]$StackName = 'kiro-ws2025-lab',
    [Parameter(ParameterSetName = 'Execute')][switch]$Yes
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

if (Get-Command 'python3' -ErrorAction SilentlyContinue) {
    $PythonExe = 'python3'; $PythonPrefix = @()
} elseif (Get-Command 'python' -ErrorAction SilentlyContinue) {
    $PythonExe = 'python'; $PythonPrefix = @()
} elseif (Get-Command 'py' -ErrorAction SilentlyContinue) {
    $PythonExe = 'py'; $PythonPrefix = @('-3')
} else {
    Write-Error 'Python 3 is required. Install Python 3, reopen PowerShell, and retry.'; exit 1
}

$modeArgument = if ($Execute) { '--execute' } else { '--plan' }
$cleanupArguments = @(
    $modeArgument,
    '--region', $Region,
    '--stack-name', $StackName
)
if ($Profile) { $cleanupArguments += @('--profile', $Profile) }
if ($Yes) { $cleanupArguments += '--yes' }

& $PythonExe @PythonPrefix "$Root\scripts\cleanup.py" @cleanupArguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
