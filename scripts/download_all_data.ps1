param(
  [int]$StartYear = 2002,
  [int]$EndYear = 2013,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$argsList = @(
  "-m", "wetbulb_pipeline",
  "update",
  "--years", "$StartYear", "$EndYear",
  "--sources", "dwd", "noaa", "nasa"
)

if ($DryRun) {
  $argsList += "--dry-run"
}

python @argsList

