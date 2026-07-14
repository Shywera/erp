<#
driver.ps1 - launch, smoke-test, and screenshot the ERP/MES/WMS FastAPI app.

Runs against an ISOLATED copy of dev.db on a throwaway port, so it never
touches your working database and never collides with a dev server on :8000.

Usage (paths resolve relative to the repo root automatically):
  powershell -ExecutionPolicy Bypass -File .claude\skills\run-erp-mes-wms\driver.ps1
  powershell -ExecutionPolicy Bypass -File .claude\skills\run-erp-mes-wms\driver.ps1 -Port 8799 -Screenshot /reklamacije
  powershell -ExecutionPolicy Bypass -File .claude\skills\run-erp-mes-wms\driver.ps1 -KeepRunning

Exit code 0 = all endpoint checks passed; non-zero = at least one failed.

ASCII-only on purpose: Windows PowerShell 5.1 misparses non-ASCII (em-dashes,
etc.) in scripts saved without a BOM.
#>
[CmdletBinding()]
param(
    [int]$Port = 8799,
    [string]$Screenshot = "/materijali",
    [switch]$KeepRunning
)

$ErrorActionPreference = "Stop"

# repo root = three levels up from this script (.claude/skills/run-erp-mes-wms)
$ROOT = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
Set-Location $ROOT

$uvicorn = Join-Path $ROOT ".venv\Scripts\uvicorn.exe"
$testDb  = Join-Path $ROOT "test_driver.db"
$logErr  = Join-Path $ROOT "driver_err.log"
$logOut  = Join-Path $ROOT "driver_out.log"
$shotPng = Join-Path $ROOT "driver_screenshot.png"
$base    = "http://localhost:$Port"

if (-not (Test-Path $uvicorn)) { throw "uvicorn not found at $uvicorn. Create the venv first (see SKILL.md Prerequisites)." }

function Stop-OnPort([int]$p) {
    Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

# Stop-Process is async; uvicorn may still hold dev-copy/log handles for a moment.
# Retry removal so teardown actually leaves nothing behind.
function Remove-WithRetry($paths) {
    foreach ($f in $paths) {
        for ($k = 0; $k -lt 12; $k++) {
            if (-not (Test-Path $f)) { break }
            try { Remove-Item $f -Force -ErrorAction Stop; break } catch { Start-Sleep -Milliseconds 300 }
        }
    }
}

Write-Host "== ERP/MES/WMS driver ==" -ForegroundColor Cyan
Write-Host "root: $ROOT"
Write-Host "port: $Port  (isolated db: test_driver.db)"

Stop-OnPort $Port

if (Test-Path (Join-Path $ROOT "dev.db")) {
    Copy-Item (Join-Path $ROOT "dev.db") $testDb -Force
} else {
    Write-Host "dev.db not found - running against a fresh DB (run alembic upgrade head for full data)." -ForegroundColor Yellow
}
$env:DATABASE_URL = "sqlite:///./test_driver.db"

# Launch uvicorn (no --reload: single process, clean shutdown by PID)
$proc = Start-Process -FilePath $uvicorn `
    -ArgumentList "app.main:app","--port","$Port" `
    -RedirectStandardError $logErr -RedirectStandardOutput $logOut `
    -PassThru -WindowStyle Hidden

# Wait for readiness (poll the materijali page)
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    try { Invoke-WebRequest "$base/materijali" -UseBasicParsing -TimeoutSec 3 | Out-Null; $ready = $true; break } catch {}
}
if (-not $ready) {
    Write-Host "SERVER DID NOT START - last 30 lines of error log:" -ForegroundColor Red
    if (Test-Path $logErr) { Get-Content $logErr -Tail 30 }
    Stop-OnPort $Port
    try { if ($proc -and -not $proc.HasExited) { $proc | Wait-Process -Timeout 5 -ErrorAction SilentlyContinue } } catch {}
    Remove-WithRetry @($testDb, $logErr, $logOut)
    exit 2
}
$secs = [math]::Round($i * 0.5, 1)
Write-Host "server up after ~$secs s (pid $($proc.Id))" -ForegroundColor Green

# Smoke checks: every module landing + a couple of HTMX partials
$checks = @(
    @{ p = "/";                     name = "root redirect" }
    @{ p = "/materijali";           name = "materijali list";   has = "Materijali" }
    @{ p = "/materijali/search";    name = "materijali search (HTMX)" }
    @{ p = "/pantoni";              name = "pantoni" }
    @{ p = "/strojevi";             name = "strojevi" }
    @{ p = "/kupci";                name = "kupci/dobavljaci" }
    @{ p = "/kupci/search";         name = "kupci search (HTMX)" }
    @{ p = "/normativi/kalkulator"; name = "normativ kalkulator" }
    @{ p = "/normativi/montaza";    name = "montaza etiketa" }
    @{ p = "/normativi/parametri";  name = "parametri strojeva" }
    @{ p = "/tehnoloski-postupci";  name = "tehnoloski postupci WIP" }
    @{ p = "/reklamacije";          name = "reklamacije dashboard" }
    @{ p = "/reklamacije/lista";    name = "reklamacije lista" }
    # skladiste rute su ZAKLJUCANE (preseljeno u vanjski WMS-app) -> vracaju lock stranicu (423); ne testiraju se.
    @{ p = "/planiranje";           name = "planiranje tiska"; has = "Planiranje tiska" }
    @{ p = "/planiranje/raspored";  name = "planiranje raspored"; has = "Raspored tiska" }
)

Write-Host "`n-- endpoint checks --"
$fail = 0
foreach ($c in $checks) {
    $status = 0; $ok = $false; $note = ""
    try {
        $r = Invoke-WebRequest "$base$($c.p)" -UseBasicParsing -TimeoutSec 10
        $status = $r.StatusCode
        $ok = ($status -eq 200)
        if ($ok -and $c.has -and ($r.Content -notmatch [regex]::Escape($c.has))) { $ok = $false; $note = "missing '$($c.has)'" }
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        $note = $_.Exception.Message.Split("`n")[0]
    }
    if ($ok) {
        "{0,-6} {1,-30} {2}" -f "OK", $c.name, $c.p | Write-Host -ForegroundColor Green
    } else {
        $fail++
        "{0,-6} {1,-30} {2}  [{3}] {4}" -f "FAIL", $c.name, $c.p, $status, $note | Write-Host -ForegroundColor Red
    }
}

# Scan startup log for tracebacks
$tb = $false
if (Test-Path $logErr) {
    $logTxt = Get-Content $logErr -Raw
    if ($logTxt -and ($logTxt -match "Traceback \(most recent call last\)")) {
        $tb = $true
        Write-Host "`nTRACEBACK in server log:" -ForegroundColor Red
        Get-Content $logErr -Tail 25
    }
}

# Screenshot the rendered UI via headless Edge (real browser render)
if ($Screenshot) {
    $edge = @(
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($edge) {
        Remove-Item $shotPng -Force -ErrorAction SilentlyContinue
        $udd     = Join-Path $env:TEMP "erp_edge_shot"
        $edgeOut = Join-Path $ROOT "driver_edge_out.log"
        $edgeErr = Join-Path $ROOT "driver_edge_err.log"
        # Start-Process keeps Edge's noisy stderr out of PowerShell's error stream
        # (a bare native call trips NativeCommandError under ErrorActionPreference=Stop).
        try {
            Start-Process -FilePath $edge -Wait -WindowStyle Hidden `
                -ArgumentList "--headless=new","--disable-gpu","--hide-scrollbars","--no-first-run",
                              "--user-data-dir=$udd","--window-size=1400,1000",
                              "--screenshot=$shotPng","$base$Screenshot" `
                -RedirectStandardOutput $edgeOut -RedirectStandardError $edgeErr
        } catch {}
        Remove-Item $edgeOut,$edgeErr -Force -ErrorAction SilentlyContinue
        for ($j = 0; $j -lt 20 -and -not (Test-Path $shotPng); $j++) { Start-Sleep -Milliseconds 300 }
        if (Test-Path $shotPng) {
            $kb = [math]::Round((Get-Item $shotPng).Length / 1KB)
            Write-Host "`nscreenshot: $shotPng  ($kb KB) of $Screenshot" -ForegroundColor Green
        } else {
            Write-Host "`nscreenshot FAILED (Edge produced no file)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`nEdge not found - skipping screenshot" -ForegroundColor Yellow
    }
}

# Summary
$total = $checks.Count
$pass  = $total - $fail
$color = if ($fail -or $tb) { "Red" } else { "Green" }
Write-Host "`n== $pass/$total endpoints OK ==" -ForegroundColor $color

if ($KeepRunning) {
    Write-Host "server LEFT RUNNING on $base (pid $($proc.Id)). Stop with:" -ForegroundColor Cyan
    Write-Host ('  Get-NetTCPConnection -LocalPort {0} -State Listen | %{{ Stop-Process -Id $_.OwningProcess -Force }}' -f $Port)
} else {
    Stop-OnPort $Port
    try { if ($proc -and -not $proc.HasExited) { $proc | Wait-Process -Timeout 5 -ErrorAction SilentlyContinue } } catch {}
    Remove-WithRetry @($testDb, $logErr, $logOut)
    Write-Host "cleaned up (server stopped, test db + logs removed; screenshot kept)" -ForegroundColor DarkGray
}

if ($fail -or $tb) { exit 1 } else { exit 0 }
