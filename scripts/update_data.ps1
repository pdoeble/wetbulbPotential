param(
  [int]$StartYear = 2002,
  [int]$EndYear = 2013,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Incremental update wrapper: checks source/location/year coverage and downloads only missing data.
$argsList = @(
  "-m", "wetbulb_pipeline",
  "update",
  "--years", "$StartYear", "$EndYear",
  "--sources", "dwd", "noaa", "nasa"
)

if ($DryRun) {
  $argsList += "--dry-run"
}

$startedAt = Get-Date
Write-Host ("[{0}] Starting wetbulb data update" -f $startedAt.ToString("yyyy-MM-dd HH:mm:ss"))
Write-Host ("Years: {0}-{1}; sources: dwd, noaa, nasa; dry-run: {2}" -f $StartYear, $EndYear, [bool]$DryRun)
Write-Host ("Command: python {0}" -f ($argsList -join " "))

$previousPythonUnbuffered = $env:PYTHONUNBUFFERED
$env:PYTHONUNBUFFERED = "1"
try {
  python @argsList
  $exitCode = $LASTEXITCODE
}
finally {
  if ($null -eq $previousPythonUnbuffered) {
    Remove-Item Env:\PYTHONUNBUFFERED -ErrorAction SilentlyContinue
  }
  else {
    $env:PYTHONUNBUFFERED = $previousPythonUnbuffered
  }
}

$duration = (Get-Date) - $startedAt
if ($exitCode -ne 0) {
  throw ("Python updater failed with exit code {0} after {1:hh\:mm\:ss}" -f $exitCode, $duration)
}
Write-Host ("[{0}] Finished wetbulb data update in {1:hh\:mm\:ss}" -f (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"), $duration)
