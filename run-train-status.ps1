param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"

function Resolve-PythonExe {
    param([string]$RequestedPython)

    if ($RequestedPython -and (Test-Path $RequestedPython)) {
        return (Resolve-Path $RequestedPython).Path
    }

    $candidates = @(
        (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
        (Join-Path $BackendDir "venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }

    throw "No Python executable found. Set -PythonExe or create a .venv/venv environment."
}

function Invoke-JsonRequest {
    param(
        [ValidateSet("Get", "Post")]
        [string]$Method,
        [string]$Uri,
        [int]$TimeoutSec = 30
    )

    try {
        return Invoke-RestMethod -Method $Method -Uri $Uri -TimeoutSec $TimeoutSec
    } catch {
        $body = $_.ErrorDetails.Message
        if ($body) {
            try {
                return $body | ConvertFrom-Json
            } catch {
                return [pscustomobject]@{ error = $body }
            }
        }

        throw
    }
}

$PythonExe = Resolve-PythonExe -RequestedPython $PythonExe
$ServerLog = Join-Path $env:TEMP "sipsetu-backend.log"
$ServerErr = Join-Path $env:TEMP "sipsetu-backend.err.log"

if (Test-Path $ServerLog) { Remove-Item $ServerLog -Force }
if (Test-Path $ServerErr) { Remove-Item $ServerErr -Force }

$ServerArgs = @(
    "-c",
    "from app import create_app; app = create_app(); app.run(debug=False, use_reloader=False, port=5000)"
)

$ServerProcess = Start-Process `
    -FilePath $PythonExe `
    -ArgumentList $ServerArgs `
    -WorkingDirectory $BackendDir `
    -PassThru `
    -RedirectStandardOutput $ServerLog `
    -RedirectStandardError $ServerErr

try {
    $healthUrl = "http://127.0.0.1:5000/api/health"
    $ready = $false

    for ($attempt = 1; $attempt -le 40; $attempt++) {
        try {
            $health = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec 2
            if ($health.status -eq "healthy") {
                $ready = $true
                break
            }
        } catch {
        }

        if ($ServerProcess.HasExited) {
            break
        }

        Start-Sleep -Milliseconds 500
    }

    if (-not $ready) {
        $serverStdout = if (Test-Path $ServerLog) { Get-Content $ServerLog -Tail 40 -ErrorAction SilentlyContinue } else { @() }
        $serverStderr = if (Test-Path $ServerErr) { Get-Content $ServerErr -Tail 40 -ErrorAction SilentlyContinue } else { @() }
        throw "Backend did not become healthy. Stdout: $($serverStdout -join [Environment]::NewLine) Stderr: $($serverStderr -join [Environment]::NewLine)"
    }

    Write-Host "Backend is healthy. Training ranking model..."
    $trainResponse = Invoke-JsonRequest -Method Post -Uri "http://127.0.0.1:5000/api/ml/ranking/train" -TimeoutSec 120
    $statusResponse = Invoke-JsonRequest -Method Get -Uri "http://127.0.0.1:5000/api/ml/ranking/status" -TimeoutSec 30

    Write-Host ""
    Write-Host "Training response:"
    $trainResponse | ConvertTo-Json -Depth 10

    Write-Host ""
    Write-Host "Model status:"
    $statusResponse | ConvertTo-Json -Depth 10
}
finally {
    if ($ServerProcess -and -not $ServerProcess.HasExited) {
        Stop-Process -Id $ServerProcess.Id -Force
    }
}
