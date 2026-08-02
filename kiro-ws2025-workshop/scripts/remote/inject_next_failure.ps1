$ErrorActionPreference = 'Stop'
Stop-Service KiroNext -Force
Start-Sleep -Seconds 3
[ordered]@{
  action='inject'; service='KiroNext'; status=(Get-Service KiroNext).Status.ToString()
  at=(Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json -Compress
