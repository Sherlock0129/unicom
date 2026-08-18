[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$webRoot = Join-Path $projectRoot "web-demo"
$logRoot = Join-Path $projectRoot "runtime\logs"
$demoUrl = "http://localhost:3000/"

function Get-DemoStatus {
    try {
        $response = Invoke-WebRequest -Uri $demoUrl -UseBasicParsing -TimeoutSec 2
        return [pscustomobject]@{
            Ready = $response.StatusCode -eq 200 -and $response.Content.Contains("demo_result.mp4")
            PortInUse = $true
        }
    }
    catch {
        return [pscustomobject]@{
            Ready = $false
            PortInUse = $false
        }
    }
}

if (-not (Test-Path -LiteralPath $webRoot -PathType Container)) {
    throw "Web project was not found: $webRoot"
}

$status = Get-DemoStatus
if (-not $status.Ready) {
    if ($status.PortInUse) {
        throw "Port 3000 is already used by another web application."
    }

    $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($null -eq $npmCommand) {
        throw "npm.cmd was not found. Install Node.js 22.13 or newer first."
    }

    if (-not (Test-Path -LiteralPath (Join-Path $webRoot "node_modules") -PathType Container)) {
        Write-Host "Installing web dependencies for the first run..."
        & $npmCommand.Source install --prefix $webRoot
        if ($LASTEXITCODE -ne 0) {
            throw "npm install failed with exit code $LASTEXITCODE."
        }
    }

    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
    $stdoutLog = Join-Path $logRoot "web-demo.out.log"
    $stderrLog = Join-Path $logRoot "web-demo.err.log"

    Write-Host "Starting the safety monitoring demo..."
    $serverProcess = Start-Process `
        -FilePath $npmCommand.Source `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory $webRoot `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -WindowStyle Hidden `
        -PassThru

    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        Start-Sleep -Milliseconds 500
        if ($serverProcess.HasExited) {
            $details = if (Test-Path -LiteralPath $stderrLog) {
                (Get-Content -LiteralPath $stderrLog -Tail 20 -ErrorAction SilentlyContinue) -join [Environment]::NewLine
            }
            else {
                "No error log was generated."
            }
            throw "The web server stopped unexpectedly.$([Environment]::NewLine)$details"
        }

        if ((Get-DemoStatus).Ready) {
            $ready = $true
            break
        }
    }

    if (-not $ready) {
        throw "The web server did not become ready within 30 seconds. Check $stderrLog"
    }
}

Write-Host "Demo ready: $demoUrl"
Start-Process $demoUrl