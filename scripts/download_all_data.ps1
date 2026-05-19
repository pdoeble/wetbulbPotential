param(
  [int]$StartYear = 2002,
  [int]$EndYear = 2013,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Fill-run wrapper: runs all configured sources and locations.
# The Python updater is still incremental and skips years already present in the RAW DB.
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
