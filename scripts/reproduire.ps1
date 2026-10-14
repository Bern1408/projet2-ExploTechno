param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    if (-not (Test-Path -LiteralPath '.env')) {
        throw 'Créer .env avec COUCHDB_USER et COUCHDB_PASSWORD (voir README).'
    }
    Get-Content -LiteralPath '.env' -Encoding utf8 | ForEach-Object {
        if ($_ -match '^([A-Z_]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
        }
    }
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { throw 'Échec de Docker Compose' }
    $taskReady = $false
    for ($taskAttempt = 0; $taskAttempt -lt 30; $taskAttempt++) {
        try {
            $null = Invoke-RestMethod -Uri 'http://127.0.0.1:5984/' -TimeoutSec 2
            $taskReady = $true
            break
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $taskReady) { throw 'CouchDB ne répond pas; consulter docker compose logs' }
    & $Python scripts/transform_communes.py
    if ($LASTEXITCODE -ne 0) { throw 'Échec du nettoyage' }
    & $Python scripts/couchdb_pipeline.py
    if ($LASTEXITCODE -ne 0) { throw "Échec de l'importation ou des vérifications" }
} finally { Pop-Location }
