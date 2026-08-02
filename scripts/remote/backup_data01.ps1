$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$backupRoot = 'C:\Workshop\backups'
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$results = New-Object System.Collections.Generic.List[object]

function Add-Result([string]$Engine, [string]$Path, [bool]$Passed, [string]$Details = '') {
    $size = if (Test-Path $Path) { (Get-Item $Path).Length } else { 0 }
    $results.Add([ordered]@{ engine=$Engine; path=$Path; size_bytes=$size; passed=($Passed -and $size -gt 0); details=$Details })
}

$sqlPath = "$backupRoot\sqlserver-$stamp.bak"
try {
    $connection = New-Object System.Data.SqlClient.SqlConnection 'Server=localhost\SQLEXPRESS;Integrated Security=true;TrustServerCertificate=true;'
    $connection.Open(); $command = $connection.CreateCommand(); $command.CommandTimeout = 600
    $escaped = $sqlPath.Replace("'", "''")
    $command.CommandText = "BACKUP DATABASE KiroWorkshop TO DISK = N'$escaped' WITH COPY_ONLY, INIT, CHECKSUM"
    [void]$command.ExecuteNonQuery(); $connection.Close()
    Add-Result 'sqlserver' $sqlPath $true
} catch { Add-Result 'sqlserver' $sqlPath $false $_.Exception.Message }

$secrets = Get-Content 'C:\Workshop\secrets\databases.json' -Raw | ConvertFrom-Json
$mysqlPath = "$backupRoot\mysql-$stamp.sql"
$defaults = "$env:TEMP\kiro-mysql-backup.cnf"
try {
    @"
[client]
user=root
password=$($secrets.mysql_root)
host=127.0.0.1
"@ | Set-Content $defaults -Encoding ASCII
    & icacls.exe $defaults /inheritance:r /grant:r 'SYSTEM:F' | Out-Null
    $dump = (Get-ChildItem 'C:\Tools\mysql-*\bin\mysqldump.exe' | Select-Object -First 1).FullName
    & $dump "--defaults-extra-file=$defaults" --single-transaction --routines --result-file=$mysqlPath kiro_workshop
    Add-Result 'mysql' $mysqlPath ($LASTEXITCODE -eq 0)
} catch { Add-Result 'mysql' $mysqlPath $false $_.Exception.Message } finally { Remove-Item $defaults -Force -ErrorAction SilentlyContinue }

$pgPath = "$backupRoot\postgresql-$stamp.dump"
try {
    $env:PGPASSWORD = $secrets.postgres
    & 'C:\Program Files\PostgreSQL\15\bin\pg_dump.exe' -h 127.0.0.1 -U postgres -Fc -f $pgPath kiro_workshop
    Add-Result 'postgresql' $pgPath ($LASTEXITCODE -eq 0)
} catch { Add-Result 'postgresql' $pgPath $false $_.Exception.Message } finally { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }

[ordered]@{
    schema_version=1; server='DATA01'; created_at=(Get-Date).ToUniversalTime().ToString('o')
    passed=(@($results | Where-Object { -not $_.passed }).Count -eq 0); backups=$results
} | ConvertTo-Json -Depth 6 -Compress
