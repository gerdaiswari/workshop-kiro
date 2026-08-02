$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Start-Service KiroNext
$deadline = (Get-Date).AddMinutes(3)
do {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:3000/next/api/health' -TimeoutSec 10
    if ($response.StatusCode -eq 200 -and $response.Content -match 'NEXT_API_OK_V1') { break }
  } catch { Start-Sleep -Seconds 5 }
} while ((Get-Date) -lt $deadline)
if ($response.StatusCode -ne 200) { throw 'Next.js did not recover' }
[ordered]@{
  action='repair'; service='KiroNext'; status=(Get-Service KiroNext).Status.ToString(); http_status=$response.StatusCode
  at=(Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json -Compress
