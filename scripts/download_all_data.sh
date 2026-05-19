#!/usr/bin/env bash
set -euo pipefail

START_YEAR="${1:-2002}"
END_YEAR="${2:-2013}"

# Fill-run wrapper; the updater skips source/location/year rows that already exist.
python -m wetbulb_pipeline update \
  --years "$START_YEAR" "$END_YEAR" \
  --sources dwd noaa nasa
