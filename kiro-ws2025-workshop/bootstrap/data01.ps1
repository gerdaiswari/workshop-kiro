param([string]$PayloadRoot = 'C:\Workshop\payload')

. "$PayloadRoot\bootstrap\common.ps1"
New-Item -ItemType Directory -Force -Path 'C:\Workshop', 'C:\Installers', 'C:\Workshop\secrets', 'C:\Workshop\backups' | Out-Null
Start-Transcript -Path 'C:\Workshop\data01-bootstrap-transcript.log' -Append
try {
    $mysqlPassword = 'My!' + [guid]::NewGuid().ToString('N')
    $postgresPassword = 'Pg!' + [guid]::NewGuid().ToString('N')
    Set-RestrictedSecretFile 'C:\Workshop\secrets\databases.json' ((@{
        mysql_root = $mysqlPassword
        postgres = $postgresPassword
    } | ConvertTo-Json))

    Write-Step 'Install XAMPP 8.2.12 for Apache and PHP'
    $xamppVersion = '8.2.12'
    $xamppInstaller = "C:\Installers\xampp-$xamppVersion.exe"
    Invoke-Download "https://sourceforge.net/projects/xampp/files/XAMPP%20Windows/$xamppVersion/xampp-windows-x64-$xamppVersion-0-VS16-installer.exe/download" $xamppInstaller
    Invoke-CheckedProcess $xamppInstaller '--mode unattended --unattendedmodeui none --disable-components xampp_mysql,xampp_filezilla,xampp_mercury,xampp_tomcat,xampp_webalizer,xampp_sendmail' @(0) | Out-Null
    if (-not (Test-Path 'C:\xampp\apache\bin\httpd.exe')) { throw 'XAMPP Apache installation not found' }
    $httpd = 'C:\xampp\apache\conf\httpd.conf'
    (Get-Content $httpd -Raw).Replace('Listen 80', 'Listen 8082').Replace('ServerName localhost:80', 'ServerName localhost:8082') | Set-Content $httpd -Encoding ASCII
    Copy-Item "$PayloadRoot\apps\data01\php\*" 'C:\xampp\htdocs' -Recurse -Force
    & 'C:\xampp\apache\bin\httpd.exe' -k install -n Apache2.4
    if ($LASTEXITCODE -ne 0) { throw 'Apache service install failed' }
    Start-Service Apache2.4

    Write-Step 'Install MySQL 8.0.40 ZIP distribution'
    $mysqlVersion = '8.0.40'
    $mysqlZip = "C:\Installers\mysql-$mysqlVersion-winx64.zip"
    Invoke-Download "https://dev.mysql.com/get/Downloads/MySQL-8.0/mysql-$mysqlVersion-winx64.zip" $mysqlZip
    Expand-Archive $mysqlZip 'C:\Tools' -Force
    $mysqlRoot = "C:\Tools\mysql-$mysqlVersion-winx64"
    $mysqlData = 'C:\ProgramData\KiroMySQL\data'
    New-Item -ItemType Directory -Force -Path $mysqlData | Out-Null
    @"
[mysqld]
basedir=$($mysqlRoot.Replace('\','/'))
datadir=$($mysqlData.Replace('\','/'))
port=3306
bind-address=127.0.0.1
character-set-server=utf8mb4
[client]
port=3306
"@ | Set-Content "$mysqlRoot\my.ini" -Encoding ASCII
    & "$mysqlRoot\bin\mysqld.exe" --defaults-file="$mysqlRoot\my.ini" --initialize-insecure --console
    if ($LASTEXITCODE -ne 0) { throw 'MySQL initialization failed' }
    & "$mysqlRoot\bin\mysqld.exe" --install MySQL80 --defaults-file="$mysqlRoot\my.ini"
    if ($LASTEXITCODE -ne 0) { throw 'MySQL service install failed' }
    Start-Service MySQL80
    Start-Sleep 10
    $mysqlSeedSql = Get-Content "$PayloadRoot\apps\data01\sql\mysql-seed.sql" -Raw
    $mysqlSetupSql = "ALTER USER 'root'@'localhost' IDENTIFIED BY '$mysqlPassword';`r`n$mysqlSeedSql"
    $mysqlSetupSql | & "$mysqlRoot\bin\mysql.exe" -u root
    if ($LASTEXITCODE -ne 0) { throw 'MySQL seed failed' }

    Write-Step 'Install PostgreSQL 15.8'
    $postgresVersion = '15.8-1'
    $postgresInstaller = "C:\Installers\postgresql-$postgresVersion.exe"
    Invoke-Download "https://get.enterprisedb.com/postgresql/postgresql-$postgresVersion-windows-x64.exe" $postgresInstaller
    $pgArgs = "--mode unattended --unattendedmodeui none --prefix `"C:\Program Files\PostgreSQL\15`" --datadir `"C:\Program Files\PostgreSQL\15\data`" --superpassword `"$postgresPassword`" --serverport 5432 --servicename postgresql-x64-15 --disable-components stackbuilder"
    Invoke-CheckedProcess $postgresInstaller $pgArgs @(0) | Out-Null
    $pgBin = 'C:\Program Files\PostgreSQL\15\bin'
    $env:PGPASSWORD = $postgresPassword
    & "$pgBin\createdb.exe" -h 127.0.0.1 -U postgres kiro_workshop
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL database creation failed' }
    & "$pgBin\psql.exe" -h 127.0.0.1 -U postgres -d kiro_workshop -v ON_ERROR_STOP=1 -f "$PayloadRoot\apps\data01\sql\postgresql-seed.sql"
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL seed failed' }
    Remove-Item Env:PGPASSWORD

    Write-Step 'Install SQL Server 2019 Express'
    $sqlBootstrap = 'C:\Installers\SQL2019-SSEI-Expr.exe'
    Invoke-Download 'https://go.microsoft.com/fwlink/?linkid=866658' $sqlBootstrap
    $sqlMedia = 'C:\Installers\SqlExpressMedia'
    Invoke-CheckedProcess $sqlBootstrap "/ACTION=Download /MEDIAPATH=`"$sqlMedia`" /MEDIATYPE=Core /QUIET" @(0) | Out-Null
    $sqlSetup = (Get-ChildItem $sqlMedia -Filter setup.exe -Recurse | Select-Object -First 1).FullName
    if (-not $sqlSetup) { throw 'SQL Server setup.exe not found after media download' }
    $sqlArgs = '/Q /ACTION=Install /FEATURES=SQLEngine /INSTANCENAME=SQLEXPRESS /SQLSVCACCOUNT="NT AUTHORITY\SYSTEM" /SQLSYSADMINACCOUNTS="BUILTIN\Administrators" /TCPENABLED=0 /NPENABLED=0 /UPDATEENABLED=0 /IACCEPTSQLSERVERLICENSETERMS'
    Invoke-CheckedProcess $sqlSetup $sqlArgs @(0, 3010) | Out-Null
    Start-Service 'MSSQL$SQLEXPRESS'
    Start-Sleep 10
    $connection = New-Object System.Data.SqlClient.SqlConnection 'Server=localhost\SQLEXPRESS;Integrated Security=true;TrustServerCertificate=true;'
    $connection.Open()
    try {
        $scriptText = Get-Content "$PayloadRoot\apps\data01\sql\sqlserver-seed.sql" -Raw
        foreach ($batch in ($scriptText -split '(?im)^\s*GO\s*$')) {
            if ($batch.Trim()) {
                $command = $connection.CreateCommand(); $command.CommandText = $batch; $command.CommandTimeout = 120
                [void]$command.ExecuteNonQuery()
            }
        }
    } finally { $connection.Close() }

    New-NetFirewallRule -DisplayName 'Kiro workshop XAMPP from VPC' -Direction Inbound -Protocol TCP -LocalPort 8082 -Action Allow -RemoteAddress 10.42.0.0/16 -ErrorAction SilentlyContinue | Out-Null
    Wait-Http 'http://127.0.0.1:8082/data/api/status.php'

    [ordered]@{
        status='complete'; role='DATA01'; xampp=$xamppVersion; mysql=$mysqlVersion
        postgresql=$postgresVersion; sqlserver='2019 Express'; completed_at=(Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json | Set-Content 'C:\Workshop\bootstrap-status.json' -Encoding UTF8
    Write-Step 'DATA01 bootstrap complete'
} catch {
    $_ | Out-String | Set-Content 'C:\Workshop\bootstrap-error.txt'
    Write-Step "DATA01 bootstrap failed: $($_.Exception.Message)"
    throw
} finally {
    Stop-Transcript
}
