# Host prerequisite check for this repo (Windows).
# Run in PowerShell:
#   powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1

$ErrorActionPreference = "Continue"

function Ok([string]$msg) { Write-Host "OK    $msg" -ForegroundColor Green }
function Warn([string]$msg) { Write-Host "WARN  $msg" -ForegroundColor Yellow }
function Bad([string]$msg) { Write-Host "MISS $msg" -ForegroundColor Red }

$RequiredFailed = $false

Write-Host "== Host check (Windows) ==" -ForegroundColor Cyan
Write-Host ""
Write-Host "-- Required --"

# Git
try {
    $null = Get-Command git -ErrorAction Stop
    Ok ("Git: " + (git --version))
} catch {
    Bad "Git not found. Install: https://git-scm.com/download/win"
    $RequiredFailed = $true
}

# Python >= 3.11 (try Windows py launcher first, then python/python3)
function Test-Python311 {
    param([string]$Exe, [string[]]$PrefixArgs)
    try {
        $null = Get-Command $Exe -ErrorAction Stop
    } catch {
        return $false, ""
    }
    $code = "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
    $allArgs = @()
    if ($PrefixArgs.Count -gt 0) { $allArgs += $PrefixArgs }
    $allArgs += @("-c", $code)
    & $Exe @allArgs 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { return $false, "" }
    $verArgs = @()
    if ($PrefixArgs.Count -gt 0) { $verArgs += $PrefixArgs }
    $verArgs += "-V"
    $verLine = & $Exe @verArgs 2>&1
    return $true, ([string]$verLine)
}

$pyOk = $false
$pyVer = ""

$tuples = @(
    @{ Exe = "py"; Prefix = @("-3") },
    @{ Exe = "python3"; Prefix = @() },
    @{ Exe = "python"; Prefix = @() }
)

foreach ($t in $tuples) {
    $prefix = @()
    if ($t.Prefix) { $prefix = $t.Prefix }
    $ok, $ver = Test-Python311 -Exe $t.Exe -PrefixArgs $prefix
    if ($ok) {
        $pyOk = $true
        $pyVer = $ver
        Ok ("Python OK ($pyVer) via $($t.Exe)")
        break
    }
}

if (-not $pyOk) {
    Bad "Python 3.11+ not found. Install from https://www.python.org/downloads/ or: winget install Python.Python.3.12"
    $RequiredFailed = $true
}

# Docker + Compose
try {
    $null = Get-Command docker -ErrorAction Stop
    Ok ("Docker: " + (Get-Command docker).Source)
} catch {
    Bad "Docker not found. Install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/"
    $RequiredFailed = $true
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dcv = (docker compose version 2>$null | Select-Object -First 1)
        Ok "Docker Compose: $dcv"
    } elseif (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        Warn "Using legacy docker-compose"
        Ok (docker-compose --version)
    } else {
        Bad "docker compose / docker-compose not found"
        $RequiredFailed = $true
    }

    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Ok "Docker daemon is reachable"
    } else {
        Warn "Docker engine not reachable — start Docker Desktop"
    }
}

Write-Host ""
Write-Host "-- Recommended (dev) --"
try {
    $null = Get-Command pre-commit -ErrorAction Stop
    Ok ("pre-commit: " + (pre-commit --version))
} catch {
    Warn "pre-commit not in PATH (optional: pip install from requirements-dev.txt)"
}

Write-Host ""
Write-Host "-- Docker GUI (optional) --"
Warn "Running the Qt GUI inside Docker on Windows is not covered here. Typical: run db+backend in Docker, run the desktop app on Windows (PYTHONPATH=frontend, API_BASE_URL=http://127.0.0.1:8000)."

Write-Host ""
if ($RequiredFailed) {
    Write-Host "Some required checks failed." -ForegroundColor Red
    exit 1
}
Write-Host "All required checks passed." -ForegroundColor Green
exit 0
