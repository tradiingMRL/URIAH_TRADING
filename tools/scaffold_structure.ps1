# URIAH_TRADING - scaffold_structure.ps1
# Creates/verifies agreed skeleton structure (idempotent).
# Run from repo root:  .\tools\scaffold_structure.ps1

$ErrorActionPreference = "Stop"

$root = (Get-Location).Path

$dirs = @(
  "design",
  "design\daily",
  "src",
  "src\core",
  "config",
  "tests",
  "tests\_fixtures",
  "tools",
  "data",
  "logs",
  "out"
)

foreach ($d in $dirs) {
  $p = Join-Path $root $d
  if (-not (Test-Path $p)) {
    New-Item -ItemType Directory -Path $p | Out-Null
  }
}

Write-Host "[OK] Scaffold verified/created under $root"