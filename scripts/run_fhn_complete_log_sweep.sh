#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

THREADS="${THREADS:-5}"
OUTPUT_DIR="${OUTPUT_DIR:-outputs/fhn-complete-Klog-T500-dt005-init05-observables}"
BASE_SEED="${BASE_SEED:-20260608}"

EXTRA_ARGS=()
if [[ "${OVERWRITE:-0}" == "1" ]]; then
  EXTRA_ARGS+=(--overwrite)
fi

CMD=(
  java -cp target/classes ar.edu.itba.sds.tp5.Main complete-log-sweep
  --topology complete
  --N 501
  --T 500
  --dt 0.005
  --save-interval 0.1
  --realizations 15
  --threads "$THREADS"
  --base-seed "$BASE_SEED"
  --output-dir "$OUTPUT_DIR"
  "${EXTRA_ARGS[@]}"
)

echo "TP5 FHN complete-network logarithmic K sweep"
echo "  output_dir: $OUTPUT_DIR"
echo "  threads:    $THREADS"
echo "  base_seed:  $BASE_SEED"
echo "  K grid:     K=0 reference plus 13 log-spaced values in [1e-4, 1e-1]"
echo "  initial:    v_i, w_i uniform in [-0.5, 0.5]"
echo "  mode:       observables only"
echo
echo "Compiling..."
mvn -q -DskipTests compile

echo "Command:"
printf ' %q' "${CMD[@]}"
echo
echo

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "DRY_RUN=1: not starting sweep."
  exit 0
fi

echo "Starting resumable logarithmic sweep."
"${CMD[@]}"
