# Script to start local PostgreSQL instance for Healthcare RAG MVP
$pgDataDir = Join-Path $PSScriptRoot "data\postgres_db"
$pgBin = "C:\Program Files\PostgreSQL\17\bin"

Write-Host "Starting Healthcare RAG PostgreSQL Server on Port 5433..." -ForegroundColor Cyan

if (-not (Test-Path $pgDataDir)) {
    Write-Host "Initializing PostgreSQL cluster..." -ForegroundColor Yellow
    & "$pgBin\initdb.exe" -D $pgDataDir -U postgres -A trust --encoding=UTF8
    Add-Content -Path (Join-Path $pgDataDir "postgresql.conf") -Value "`nport = 5433`nlisten_addresses = '*'"
}

& "$pgBin\postgres.exe" -D $pgDataDir -p 5433
