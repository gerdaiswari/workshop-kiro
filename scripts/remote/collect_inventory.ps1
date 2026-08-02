$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Import-Module ServerManager

function Try-Version([string]$Command, [string[]]$Arguments = @('--version')) {
    try {
        $result = & $Command @Arguments 2>&1 | Select-Object -First 3
        return ($result -join ' ').Trim()
    } catch { return $null }
}

$os = Get-CimInstance Win32_OperatingSystem
$computer = Get-CimInstance Win32_ComputerSystem
$disks = @(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
    [ordered]@{
        device = $_.DeviceID
        size_gib = [math]::Round($_.Size / 1GB, 2)
        free_gib = [math]::Round($_.FreeSpace / 1GB, 2)
    }
})
$features = @(Get-WindowsFeature | Where-Object InstallState -eq 'Installed' | Select-Object -ExpandProperty Name | Sort-Object)
$relevantServices = 'W3SVC','WAS','KiroSpring','KiroNext','nginx','Apache2.4','MSSQL$SQLEXPRESS','MySQL80','postgresql-x64-15','AmazonSSMAgent'
$services = @(Get-Service | Where-Object Name -in $relevantServices | ForEach-Object {
    [ordered]@{ name=$_.Name; display_name=$_.DisplayName; status=$_.Status.ToString(); start_type=$_.StartType.ToString() }
})
$listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object LocalPort -in 80,3000,3306,5432,8080,8081,8082,1433 | ForEach-Object {
    [ordered]@{ address=$_.LocalAddress; port=$_.LocalPort; process_id=$_.OwningProcess }
} | Sort-Object port -Unique)
$programs = @(
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
) | ForEach-Object { Get-ItemProperty $_ -ErrorAction SilentlyContinue } | Where-Object DisplayName | ForEach-Object {
    [ordered]@{ name=$_.DisplayName; version=$_.DisplayVersion; publisher=$_.Publisher }
} | Sort-Object name -Unique

$blockers = @()
if ('AD-Domain-Services' -in $features) { $blockers += 'domain-controller-role' }
if ('Failover-Clustering' -in $features) { $blockers += 'failover-clustering' }
foreach ($feature in 'RDS-RD-Server','RDS-Connection-Broker','RDS-Virtualization','RDS-Web-Access') {
    if ($feature -in $features) { $blockers += "unsupported-role:$feature" }
}

$tls12Client = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.2\Client' -ErrorAction SilentlyContinue
$tls12Server = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.2\Server' -ErrorAction SilentlyContinue
$bootstrapStatus = if (Test-Path 'C:\Workshop\bootstrap-status.json') { Get-Content 'C:\Workshop\bootstrap-status.json' -Raw | ConvertFrom-Json } else { $null }

$result = [ordered]@{
    schema_version = 1
    collected_at = (Get-Date).ToUniversalTime().ToString('o')
    computer_name = $env:COMPUTERNAME
    os = [ordered]@{
        caption = $os.Caption
        version = $os.Version
        build = $os.BuildNumber
        architecture = $os.OSArchitecture
        install_date = $os.InstallDate.ToUniversalTime().ToString('o')
        powershell = $PSVersionTable.PSVersion.ToString()
        tls12_client_disabled = ($tls12Client.DisabledByDefault -eq 1 -or $tls12Client.Enabled -eq 0)
        tls12_server_disabled = ($tls12Server.DisabledByDefault -eq 1 -or $tls12Server.Enabled -eq 0)
    }
    hardware = [ordered]@{ manufacturer=$computer.Manufacturer; model=$computer.Model; memory_gib=[math]::Round($computer.TotalPhysicalMemory/1GB,2) }
    disks = $disks
    installed_features = $features
    installed_programs = @($programs)
    services = $services
    listeners = $listeners
    runtimes = [ordered]@{
        java = Try-Version 'java.exe' @('-version')
        node = Try-Version 'node.exe' @('--version')
        npm = Try-Version 'npm.cmd' @('--version')
        nginx = if (Test-Path 'C:\Tools') { (Get-ChildItem 'C:\Tools\nginx-*\nginx.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 | ForEach-Object { Try-Version $_.FullName @('-v') }) } else { $null }
        php = if (Test-Path 'C:\xampp\php\php.exe') { Try-Version 'C:\xampp\php\php.exe' @('-v') } else { $null }
        mysql = if (Test-Path 'C:\Tools') { (Get-ChildItem 'C:\Tools\mysql-*\bin\mysql.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 | ForEach-Object { Try-Version $_.FullName @('--version') }) } else { $null }
        postgresql = if (Test-Path 'C:\Program Files\PostgreSQL\15\bin\psql.exe') { Try-Version 'C:\Program Files\PostgreSQL\15\bin\psql.exe' @('--version') } else { $null }
    }
    blockers = $blockers
    bootstrap = $bootstrapStatus
}
$result | ConvertTo-Json -Depth 8 -Compress
