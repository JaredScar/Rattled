#
# Rattled Language Installer
# Run via install.bat or: powershell -ExecutionPolicy Bypass -File install.ps1
#

$ErrorActionPreference = "Stop"

# ── Banner ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ===========================================" -ForegroundColor Cyan
Write-Host "    Rattled Language Installer" -ForegroundColor Cyan
Write-Host "  ===========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Verify Python is available ────────────────────────────────────────────
try {
    $pyver = & python --version 2>&1
    Write-Host "  [OK] Found $pyver" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found. Please install Python 3.8+ and try again." -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    exit 1
}

# ── 2. Install the package ───────────────────────────────────────────────────
Write-Host ""
Write-Host "  Installing Rattled package..." -ForegroundColor Yellow
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& python -m pip install --quiet "$repoRoot"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] pip install failed. See output above." -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    exit 1
}
Write-Host "  [OK] Package installed." -ForegroundColor Green

# ── 3. Locate the scripts directory where rattled.exe was placed ─────────────
$scriptsDir = & python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))" 2>$null
if (-not $scriptsDir) {
    $scriptsDir = & python -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>$null
}
$scriptsDir = $scriptsDir.Trim()

# Confirm rattled.exe actually exists there
$rattledExe = Join-Path $scriptsDir "rattled.exe"
if (-not (Test-Path $rattledExe)) {
    # Fallback: search the system scripts dir
    $scriptsDir = & python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
    $scriptsDir = $scriptsDir.Trim()
    $rattledExe = Join-Path $scriptsDir "rattled.exe"
}

Write-Host "  [OK] rattled.exe found at: $scriptsDir" -ForegroundColor Green

# ── 4. Add scripts directory to the user PATH if not already present ─────────
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -split ";" | Where-Object { $_.TrimEnd("\") -eq $scriptsDir.TrimEnd("\") }) {
    Write-Host "  [OK] Scripts directory is already on PATH." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  Adding to PATH: $scriptsDir" -ForegroundColor Yellow
    $newPath = ($currentPath.TrimEnd(";") + ";" + $scriptsDir)
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "  [OK] PATH updated." -ForegroundColor Green
}

# ── 5. Done ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ===========================================" -ForegroundColor Cyan
Write-Host "    Installation complete!" -ForegroundColor Cyan
Write-Host "  ===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Open a NEW terminal window, then run:" -ForegroundColor White
Write-Host ""
Write-Host "    rattled yourfile.ry" -ForegroundColor White
Write-Host "    rattled yourfile.ry --emit-python" -ForegroundColor White
Write-Host "    rattled yourfile.ry --check" -ForegroundColor White
Write-Host "    rattled                          (REPL)" -ForegroundColor White
Write-Host ""
Read-Host "  Press Enter to exit"
