#!/usr/bin/env bash
# V6 Phase 44 (C5a) — nightly k6 runner.
# CI invokes: DSI_BASE_URL=https://staging.dsi.internal DSI_SMOKE_TOKEN=... ./run.sh
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p reports

for scenario in scenarios/*.js; do
  name=$(basename "$scenario" .js)
  echo "=== k6 $name ==="
  k6 run --summary-export="reports/${name}.json" "$scenario"
done

echo "Reports written to reports/"
