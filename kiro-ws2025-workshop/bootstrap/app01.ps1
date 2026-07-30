param([string]$PayloadRoot = 'C:\Workshop\payload')

. "$PayloadRoot\bootstrap\common.ps1"
New-Item -ItemType Directory -Force -Path 'C:\Workshop', 'C:\Installers', 'C:\Services' | Out-Null
Start-Transcript -Path 'C:\Workshop\app01-bootstrap-transcript.log' -Append
try {
    Write-Step 'Install IIS'
    Install-WindowsFeature Web-Server, Web-Static-Content, Web-Default-Doc, Web-Http-Logging | Out-Null

    $nodeVersion = '20.18.0'
    $nodeMsi = "C:\Installers\node-v$nodeVersion-x64.msi"
    Invoke-Download "https://nodejs.org/dist/v$nodeVersion/node-v$nodeVersion-x64.msi" $nodeMsi
    Install-Msi $nodeMsi

    $correttoVersion = '17.0.12.7.1'
    $javaMsi = "C:\Installers\amazon-corretto-$correttoVersion-windows-x64.msi"
    Invoke-Download "https://corretto.aws/downloads/resources/$correttoVersion/amazon-corretto-$correttoVersion-windows-x64.msi" $javaMsi
    Install-Msi $javaMsi

    $mavenVersion = '3.9.9'
    $mavenZip = "C:\Installers\apache-maven-$mavenVersion-bin.zip"
    Invoke-Download "https://archive.apache.org/dist/maven/maven-3/$mavenVersion/binaries/apache-maven-$mavenVersion-bin.zip" $mavenZip
    Expand-Archive -Path $mavenZip -DestinationPath 'C:\Tools' -Force
    [Environment]::SetEnvironmentVariable('MAVEN_HOME', "C:\Tools\apache-maven-$mavenVersion", 'Machine')
    [Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'Machine') + ";C:\Tools\apache-maven-$mavenVersion\bin", 'Machine')

    $winswVersion = '2.12.0'
    $winsw = 'C:\Installers\WinSW-x64.exe'
    Invoke-Download "https://github.com/winsw/winsw/releases/download/v$winswVersion/WinSW-x64.exe" $winsw

    $nginxVersion = '1.26.2'
    $nginxZip = "C:\Installers\nginx-$nginxVersion.zip"
    Invoke-Download "https://nginx.org/download/nginx-$nginxVersion.zip" $nginxZip
    Expand-Archive -Path $nginxZip -DestinationPath 'C:\Tools' -Force
    $nginxRoot = "C:\Tools\nginx-$nginxVersion"

    Refresh-ProcessPath
    $javaHome = (Get-ChildItem 'C:\Program Files\Amazon Corretto' -Directory | Sort-Object Name -Descending | Select-Object -First 1).FullName
    if (-not $javaHome) { throw 'Amazon Corretto installation not found' }
    [Environment]::SetEnvironmentVariable('JAVA_HOME', $javaHome, 'Machine')
    $env:JAVA_HOME = $javaHome
    $env:Path = "$javaHome\bin;$env:Path"

    Write-Step 'Deploy pre-built Angular to IIS'
    $angular = "$PayloadRoot\apps\app01\angular"
    Remove-Item 'C:\inetpub\wwwroot\*' -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item "$angular\dist\workshop-angular\*" 'C:\inetpub\wwwroot' -Recurse -Force
    Set-Content 'C:\inetpub\wwwroot\health.html' '<html><body>IIS_OK_V1</body></html>' -Encoding UTF8

    Write-Step 'Build Next.js'
    $next = "$PayloadRoot\apps\app01\next"
    Push-Location $next
    $env:NODE_OPTIONS = '--max-old-space-size=4096'
    & npm.cmd install --no-audit --no-fund --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) { throw 'Next npm install failed' }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Next build failed' }
    $env:NODE_OPTIONS = ''
    Pop-Location
    # Standalone mode requires static assets copied into the standalone directory
    $standaloneStatic = "$next\.next\standalone\.next\static"
    if (Test-Path "$next\.next\static") {
        New-Item -ItemType Directory -Force -Path $standaloneStatic | Out-Null
        Copy-Item "$next\.next\static\*" $standaloneStatic -Recurse -Force
    }

    Write-Step 'Build Spring Boot'
    $spring = "$PayloadRoot\apps\app01\spring"
    Push-Location $spring
    & "C:\Tools\apache-maven-$mavenVersion\bin\mvn.cmd" -B -DskipTests package
    if ($LASTEXITCODE -ne 0) { throw 'Maven build failed' }
    Pop-Location
    $jar = (Get-ChildItem "$spring\target\*.jar" | Where-Object Name -NotLike '*.original' | Select-Object -First 1).FullName
    if (-not $jar) { throw 'Spring Boot JAR not found' }

    Write-Step 'Configure nginx routes'
    $nginxConfig = @"
worker_processes  1;
events { worker_connections 1024; }
http {
  include mime.types;
  default_type application/octet-stream;
  access_log logs/access.log;
  error_log logs/error.log info;
  server {
    listen 8081;
    server_name _;
    location = /health { default_type application/json; return 200 '{"status":"ok","marker":"NGINX_OK_V1"}'; }
    location /spring/ { proxy_set_header Host `$host; proxy_pass http://127.0.0.1:8080/; }
    location /next { proxy_set_header Host `$host; proxy_pass http://127.0.0.1:3000; }
  }
}
"@
    Set-Content "$nginxRoot\conf\nginx.conf" $nginxConfig -Encoding ASCII

    Write-Step 'Install WinSW services'
    $services = @(
        @{ Name='KiroSpring'; Executable="$javaHome\bin\java.exe"; Arguments="-jar `"$jar`""; Working=$spring; Env=@() },
        @{ Name='KiroNext'; Executable='C:\Program Files\nodejs\node.exe'; Arguments=".next\standalone\server.js"; Working=$next; Env=@(@{name='PORT';value='3000'},@{name='HOSTNAME';value='0.0.0.0'}) },
        @{ Name='nginx'; Executable="$nginxRoot\nginx.exe"; Arguments=''; Working=$nginxRoot; Env=@() }
    )
    foreach ($service in $services) {
        $dir = "C:\Services\$($service.Name)"
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Copy-Item $winsw "$dir\$($service.Name).exe" -Force
        $envXml = ''
        foreach ($envVar in $service.Env) {
            $envXml += "`n  <env name=`"$($envVar.name)`" value=`"$($envVar.value)`" />"
        }
        $xml = @"
<service>
  <id>$($service.Name)</id>
  <name>$($service.Name)</name>
  <description>Kiro Windows upgrade workshop service</description>
  <executable>$($service.Executable)</executable>
  <arguments>$([System.Security.SecurityElement]::Escape($service.Arguments))</arguments>
  <workingdirectory>$($service.Working)</workingdirectory>
  <logpath>C:\Workshop\logs\$($service.Name)</logpath>
  <log mode="roll" />
  <startmode>Automatic</startmode>
  <onfailure action="restart" delay="10 sec" />$envXml
</service>
"@
        Set-Content "$dir\$($service.Name).xml" $xml -Encoding UTF8
        & "$dir\$($service.Name).exe" install
        if ($LASTEXITCODE -ne 0) { throw "Failed to install $($service.Name) service" }
        Start-Service $service.Name
    }

    New-NetFirewallRule -DisplayName 'Kiro workshop nginx from VPC' -Direction Inbound -Protocol TCP -LocalPort 8081 -Action Allow -RemoteAddress 10.42.0.0/16 -ErrorAction SilentlyContinue | Out-Null
    Start-Service W3SVC
    Wait-Http 'http://127.0.0.1/health.html'
    Wait-Http 'http://127.0.0.1:8080/actuator/health'
    Wait-Http 'http://127.0.0.1:3000/next/api/health'
    Wait-Http 'http://127.0.0.1:8081/health'

    [ordered]@{
        status='complete'; role='APP01'; node=$nodeVersion; java=$correttoVersion
        maven=$mavenVersion; nginx=$nginxVersion; completed_at=(Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json | Set-Content 'C:\Workshop\bootstrap-status.json' -Encoding UTF8
    Write-Step 'APP01 bootstrap complete'
} catch {
    $_ | Out-String | Set-Content 'C:\Workshop\bootstrap-error.txt'
    Write-Step "APP01 bootstrap failed: $($_.Exception.Message)"
    throw
} finally {
    Stop-Transcript
}
