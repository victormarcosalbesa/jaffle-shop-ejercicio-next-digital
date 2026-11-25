param(
    [ValidateRange(1, 86400)]
    [int]$IntervalSeconds = 60,
    [switch]$Continuous
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$dbtExecutable = Join-Path $projectRoot '.venv/Scripts/dbt.exe'
if (-not (Test-Path -LiteralPath $dbtExecutable)) {
    $dbtExecutable = (Get-Command dbt -ErrorAction Stop).Source
}

Push-Location -LiteralPath $projectRoot
try {
    do {
        # Los CSV son las fuentes de datos de este taller.
        # Construir el proyecto incluye clientes, necesarios para validar relaciones.
        & $dbtExecutable build --profiles-dir $projectRoot
        if ($LASTEXITCODE -ne 0) {
            throw 'La actualizacion no ha superado la construccion o los tests. Revisa la salida de dbt.'
        }
        if ($Continuous) {
            Write-Host "Actualizacion validada. Proxima ejecucion en $IntervalSeconds segundos. Ctrl+C para detener."
            Start-Sleep -Seconds $IntervalSeconds
        }
    } while ($Continuous)
}
finally {
    Pop-Location
}
