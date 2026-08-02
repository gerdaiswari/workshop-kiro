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

$os = Get-CimInstance Win32_OperatingSystem
Add-Check 'os.windows-server' ($os.Caption -match 'Windows Server (2019|2025)') $os.Caption 'Windows Server 2019 or 2025'
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$free = [math]::Round($disk.FreeSpace/1GB,2)
Add-Check 'disk.c-free-gib' ($free -ge 20) $free '>=20'
foreach ($name in 'Apache2.4','MSSQL$SQLEXPRESS','MySQL80','postgresql-x64-15','AmazonSSMAgent') { Test-ServiceCheck $name }

try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8082/data/api/status.php' -TimeoutSec 15
    Add-Check 'http.php-status' ($response.StatusCode -eq 200 -and $response.Content -match 'PHP_OK_V1') $response.StatusCode '200 + PHP_OK_V1'
} catch { Add-Check 'http.php-status' $false 'request-failed' '200 + PHP_OK_V1' $true $_.Exception.Message }

try {
    $connection = New-Object System.Data.SqlClient.SqlConnection 'Server=localhost\SQLEXPRESS;Database=KiroWorkshop;Integrated Security=true;TrustServerCertificate=true;'
    $connection.Open(); $command = $connection.CreateCommand()
    $command.CommandText = "SELECT CONCAT(COUNT(*), ':', SUM(Quantity), ':', MIN(CompatibilityMarker)) FROM dbo.InventoryItems"
    $value = [string]$command.ExecuteScalar(); $connection.Close()
    Add-Check 'db.sqlserver-seed' ($value -eq '3:6:DATA_OK_V1') $value '3:6:DATA_OK_V1'
} catch { Add-Check 'db.sqlserver-seed' $false 'query-failed' '3:6:DATA_OK_V1' $true $_.Exception.Message }

$secrets = Get-Content 'C:\Workshop\secrets\databases.json' -Raw | ConvertFrom-Json
try {
    $mysql = (Get-ChildItem 'C:\Tools\mysql-*\bin\mysql.exe' | Select-Object -First 1).FullName
    $value = (& $mysql -N -B -u root "-p$($secrets.mysql_root)" -e "SELECT CONCAT(COUNT(*), ':', SUM(quantity), ':', MIN(compatibility_marker)) FROM kiro_workshop.inventory_items;" 2>$null).Trim()
    Add-Check 'db.mysql-seed' ($value -eq '3:6:DATA_OK_V1') $value '3:6:DATA_OK_V1'
} catch { Add-Check 'db.mysql-seed' $false 'query-failed' '3:6:DATA_OK_V1' $true $_.Exception.Message }

try {
    $env:PGPASSWORD = $secrets.postgres
    $psql = 'C:\Program Files\PostgreSQL\15\bin\psql.exe'
    $value = (& $psql -h 127.0.0.1 -U postgres -d kiro_workshop -t -A -c "SELECT COUNT(*) || ':' || SUM(quantity) || ':' || MIN(compatibility_marker) FROM inventory_items;" 2>$null).Trim()
    Remove-Item Env:PGPASSWORD
    Add-Check 'db.postgresql-seed' ($value -eq '3:6:DATA_OK_V1') $value '3:6:DATA_OK_V1'
} catch { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue; Add-Check 'db.postgresql-seed' $false 'query-failed' '3:6:DATA_OK_V1' $true $_.Exception.Message }

$backupFiles = @(Get-ChildItem 'C:\Workshop\backups' -File -ErrorAction SilentlyContinue)
Add-Check 'backup.files-present' $true $backupFiles.Count 'captured separately' $false 'Mandatory only in backup-data phase'

[ordered]@{
    schema_version=1; server='DATA01'; computer=$env:COMPUTERNAME
    tested_at=(Get-Date).ToUniversalTime().ToString('o')
    os_caption=$os.Caption; passed=(@($checks | Where-Object { $_.mandatory -and -not $_.passed }).Count -eq 0)
    checks=$checks
} | ConvertTo-Json -Depth 7 -Compress
