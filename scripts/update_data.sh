#!/usr/bin/env bash
set -euo pipefail

START_YEAR="${1:-2002}"
END_YEAR="${2:-2013}"

# Incremental update wrapper; only missing source/location/year rows are downloaded.
python -m wetbulb_pipeline update \
  --years "$START_YEAR" "$END_YEAR" \
  --sources dwd noaa nasa
