# hash.ps1 — Windows (PowerShell) staleness check for a wiki page's sources.
# Same CLI contract as hash.sh; uses the built-in Get-FileHash (no dependencies).
#   hash.ps1 -File <file>                    -> prints the file's sha256 (lowercase)
#   hash.ps1 -File <file> -Recorded <hash>   -> prints FRESH | STALE | MISSING
param(
  [Parameter(Mandatory = $true)][string]$File,
  [string]$Recorded
)

if (-not (Test-Path -LiteralPath $File -PathType Leaf)) {
  if ($Recorded) { Write-Output "MISSING"; exit 0 }
  Write-Error "file not found: $File"; exit 4
}

$current = (Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLower()

if (-not $Recorded) {
  Write-Output $current
} elseif ($current -eq $Recorded.ToLower()) {
  Write-Output "FRESH"
} else {
  Write-Output "STALE"
}
