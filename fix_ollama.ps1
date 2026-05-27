param()

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "OLLAMA DIAGNOSTIC AND AUTO-FIX TOOL" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$foundIssue = $false

# Check 1: Ollama connection
Write-Host "[1/5] Checking Ollama connection..." -ForegroundColor Yellow
$ErrorActionPreference = "SilentlyContinue"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "      OK - Ollama is running" -ForegroundColor Green
}
catch {
    Write-Host "      ERROR - Ollama NOT responding" -ForegroundColor Red
    $foundIssue = $true
    Write-Host "      ACTION: Open Ollama application" -ForegroundColor Yellow
}

# Check 2: Models installed
Write-Host ""
Write-Host "[2/5] Checking installed models..." -ForegroundColor Yellow
$ErrorActionPreference = "SilentlyContinue"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    $models = $data.models
    if ($models -and $models.Count -gt 0) {
        Write-Host "      OK - Found $($models.Count) models:" -ForegroundColor Green
        foreach ($model in $models) {
            $name = $model.name
            Write-Host "        - $name" -ForegroundColor Green
        }
    }
    else {
        Write-Host "      ERROR - No models installed" -ForegroundColor Red
        Write-Host "      ACTION: Run 'ollama pull qwen2.5:7b'" -ForegroundColor Yellow
        $foundIssue = $true
    }
}
catch {
    Write-Host "      ERROR - Could not check models" -ForegroundColor Red
    $foundIssue = $true
}

# Check 3: Backend running
Write-Host ""
Write-Host "[3/5] Checking backend..." -ForegroundColor Yellow
$ErrorActionPreference = "SilentlyContinue"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    if ($data.backend -eq "ok") {
        Write-Host "      OK - Backend is running" -ForegroundColor Green
        Write-Host "      Ollama status: $($data.ollama)" -ForegroundColor Green
    }
    else {
        Write-Host "      ERROR - Backend not responding correctly" -ForegroundColor Red
        $foundIssue = $true
    }
}
catch {
    Write-Host "      ERROR - Backend NOT running" -ForegroundColor Red
    Write-Host "      ACTION: Run '.\run_windows.bat' in project folder" -ForegroundColor Yellow
    $foundIssue = $true
}

# Check 4: Port availability
Write-Host ""
Write-Host "[4/5] Checking port availability..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port11434 = Get-NetTCPConnection -LocalPort 11434 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "      OK - Port 8000 (Backend): In use" -ForegroundColor Green
}
else {
    Write-Host "      WARNING - Port 8000 (Backend): Not in use" -ForegroundColor Yellow
}

if ($port11434) {
    Write-Host "      OK - Port 11434 (Ollama): In use" -ForegroundColor Green
}
else {
    Write-Host "      WARNING - Port 11434 (Ollama): Not in use" -ForegroundColor Yellow
    $foundIssue = $true
}

# Check 5: System resources
Write-Host ""
Write-Host "[5/5] Checking system resources..." -ForegroundColor Yellow
$mem = Get-WmiObject win32_operatingsystem
$freeMem = [math]::Round($mem.FreePhysicalMemory / 1MB)
Write-Host "      Free RAM: $freeMem MB" -ForegroundColor Green

if ($freeMem -lt 2000) {
    Write-Host "      WARNING - Low memory. Ollama needs 4GB+" -ForegroundColor Yellow
    $foundIssue = $true
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

if ($foundIssue -eq $false) {
    Write-Host "SUCCESS - ALL SYSTEMS OK" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your setup is ready to use!"
    Write-Host "Open browser: http://localhost:8000"
    Write-Host "============================================================" -ForegroundColor Cyan
}
else {
    Write-Host "ISSUES DETECTED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Follow the ACTIONS above, then restart this diagnostic" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
}

Write-Host ""
