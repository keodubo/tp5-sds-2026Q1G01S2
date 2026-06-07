#!/usr/bin/env bash
set -euo pipefail

# Full production sweep for TP5 Sistema 2 (FitzHugh-Nagumo).
# It writes only metadata.properties and observables.csv per run.
# Do not add --save-states or --save-adjacency here: those outputs are too large
# for the full sweep and should be generated only for selected animations.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

THREADS="${THREADS:-5}"
OUTPUT_DIR="${OUTPUT_DIR:-outputs/fhn-sweep-T500-dt005-init05-observables}"
BASE_SEED="${BASE_SEED:-20260607}"

EXTRA_ARGS=()
if [[ "${OVERWRITE:-0}" == "1" ]]; then
  EXTRA_ARGS+=(--overwrite)
fi

CMD=(
  java -cp target/classes ar.edu.itba.sds.tp5.Main sweep
  --topology all
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

echo "TP5 FHN sweep"
echo "  output_dir: $OUTPUT_DIR"
echo "  threads:    $THREADS"
echo "  base_seed:  $BASE_SEED"
echo "  initial:    v_i, w_i uniform in [-0.5, 0.5]"
echo "  seeds:      distinct runSeed per parameter combination and realization"
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

echo "Starting sweep. This is resumable; existing complete runs are skipped unless OVERWRITE=1."
"${CMD[@]}"
