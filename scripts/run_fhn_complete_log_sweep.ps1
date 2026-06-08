[CmdletBinding()]
param(
    [int]$Threads = 5,
    [string]$OutputDir = "outputs/fhn-complete-Klog-T500-dt005-init05-observables",
    [long]$BaseSeed = 20260608,
    [switch]$Overwrite,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$rootDir = Split-Path -Parent $PSScriptRoot
$buildDir = Join-Path $rootDir "target\classes"

Push-Location $rootDir
try {
    Write-Host "TP5 FHN complete-network logarithmic K sweep"
    Write-Host "  output_dir: $OutputDir"
    Write-Host "  threads:    $Threads"
    Write-Host "  base_seed:  $BaseSeed"
    Write-Host "  K grid:     K=0 reference plus 13 log-spaced values in [1e-4, 1e-1]"
    Write-Host "  initial:    v_i, w_i uniform in [-0.5, 0.5]"
    Write-Host "  mode:       observables only"
    Write-Host

    Write-Host "Compiling with javac..."
    New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
    $sources = Get-ChildItem -LiteralPath "src\main\java" -Recurse -Filter "*.java" |
        ForEach-Object { $_.FullName }
    & javac --release 21 -d $buildDir $sources
    if ($LASTEXITCODE -ne 0) {
        throw "javac failed with exit code $LASTEXITCODE"
    }

    $javaArgs = @(
        "-cp", $buildDir,
        "ar.edu.itba.sds.tp5.Main", "complete-log-sweep",
        "--topology", "complete",
        "--N", "501",
        "--T", "500",
        "--dt", "0.005",
        "--save-interval", "0.1",
        "--realizations", "15",
        "--threads", $Threads.ToString(),
        "--base-seed", $BaseSeed.ToString(),
        "--output-dir", $OutputDir
    )
    if ($Overwrite) {
        $javaArgs += "--overwrite"
    }

    Write-Host "Command:"
    Write-Host "java $($javaArgs -join ' ')"
    Write-Host

    if ($DryRun) {
        Write-Host "DryRun: sweep not started."
        return
    }

    Write-Host "Starting resumable logarithmic sweep."
    & java @javaArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Sweep failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
