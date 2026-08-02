$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$checks = New-Object System.Collections.Generic.List[object]

function Add-Check([string]$Id, [bool]$Passed, $Value, $Expected, [bool]$Mandatory = $true, [string]$Details = '') {
    $checks.Add([ordered]@{ id=$Id; mandatory=$Mandatory; passed=$Passed; value=$Value; expected=$Expected; details=$Details })
}
function Test-ServiceCheck([string]$Name) {
    try { $service = Get-Service $Name -ErrorAction Stop; Add-Check "service.$Name" ($service.Status -eq 'Running') $service.Status.ToString() 'Running' }
    catch { Add-Check "service.$Name" $false 'missing' 'Running' $true $_.Exception.Message }
}
function Test-HttpCheck([string]$Id, [string]$Uri, [string]$Marker) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 15
        $content = if ($response.Content -is [byte[]]) {
            [System.Text.Encoding]::UTF8.GetString([byte[]]$response.Content)
        } else {
            [string]$response.Content
        }
        $passed = $response.StatusCode -eq 200 -and $content -match [regex]::Escape($Marker)
        $details = $content.Substring(0, [math]::Min(160, $content.Length))
        Add-Check $Id $passed "$($response.StatusCode):$Marker" "200:$Marker" $true $details
    } catch { Add-Check $Id $false 'request-failed' "200:$Marker" $true $_.Exception.Message }
}

$os = Get-CimInstance Win32_OperatingSystem
Add-Check 'os.windows-server' ($os.Caption -match 'Windows Server (2019|2025)') $os.Caption 'Windows Server 2019 or 2025'
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$free = [math]::Round($disk.FreeSpace/1GB,2)
Add-Check 'disk.c-free-gib' ($free -ge 20) $free '>=20'
foreach ($name in 'W3SVC','KiroSpring','KiroNext','nginx','AmazonSSMAgent') { Test-ServiceCheck $name }
Test-HttpCheck 'http.iis-angular' 'http://127.0.0.1/' 'ANGULAR_OK_V1'
Test-HttpCheck 'http.iis-health' 'http://127.0.0.1/health.html' 'IIS_OK_V1'
Test-HttpCheck 'http.spring-health' 'http://127.0.0.1:8080/actuator/health' '"status":"UP"'
Test-HttpCheck 'http.spring-api' 'http://127.0.0.1:8080/api/info' 'SPRING_OK_V1'
Test-HttpCheck 'http.next-page' 'http://127.0.0.1:3000/next' 'NEXT_OK_V1'
Test-HttpCheck 'http.next-api' 'http://127.0.0.1:3000/next/api/health' 'NEXT_API_OK_V1'
Test-HttpCheck 'http.nginx-health' 'http://127.0.0.1:8081/health' 'NGINX_OK_V1'
Test-HttpCheck 'http.nginx-spring-proxy' 'http://127.0.0.1:8081/spring/api/info' 'SPRING_OK_V1'
Test-HttpCheck 'http.nginx-next-proxy' 'http://127.0.0.1:8081/next/api/health' 'NEXT_API_OK_V1'
$eventErrors = @(Get-WinEvent -FilterHashtable @{LogName='Application'; Level=2; StartTime=(Get-Date).AddMinutes(-30)} -ErrorAction SilentlyContinue).Count
Add-Check 'events.application-errors-30m' $true $eventErrors 'review' $false 'Informational review; not an automatic blocker'

[ordered]@{
    schema_version=1; server='APP01'; computer=$env:COMPUTERNAME
    tested_at=(Get-Date).ToUniversalTime().ToString('o')
    os_caption=$os.Caption; passed=(@($checks | Where-Object { $_.mandatory -and -not $_.passed }).Count -eq 0)
    checks=$checks
} | ConvertTo-Json -Depth 7 -Compress
