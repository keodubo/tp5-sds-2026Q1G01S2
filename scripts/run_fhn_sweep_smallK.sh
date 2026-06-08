#!/usr/bin/env bash
set -euo pipefail

# Small-coupling sweep for TP5 Sistema 2 (FitzHugh-Nagumo).
# Professor's request: explore K = 1e-4, 1e-3, 1e-2, where the interesting
# transition between "never synchronises" (K=0) and "synchronises instantly" (K>=0.1) lives.
#
# Same parameters as the main sweep (output2): N=501, T=500, dt=0.005, save-interval=0.1,
# 15 realizations, base-seed=20260607, init v_i,w_i ~ U[-0.5, 0.5], observables only.
# Writes to a SEPARATE output dir so output2 stays intact.
# Uses the new --k-values override (default 0.0..1.0 grid is untouched).
#
# Resumable: existing complete runs are skipped unless OVERWRITE=1.
# Runtime is dominated by the complete network (O(N^2), ~7 min/run); random/ring are ~2.4 s each.
# ~35-45 min wall on ~10 threads.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

THREADS="${THREADS:-10}"
OUTPUT_DIR="${OUTPUT_DIR:-outputs/fhn-sweep-smallK-T500-dt005-init05-observables}"
BASE_SEED="${BASE_SEED:-20260607}"
K_VALUES="${K_VALUES:-0.0001,0.001,0.01}"

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
  --k-values "$K_VALUES"
  --output-dir "$OUTPUT_DIR"
  "${EXTRA_ARGS[@]}"
)

echo "TP5 FHN small-K sweep"
echo "  output_dir: $OUTPUT_DIR"
echo "  threads:    $THREADS"
echo "  base_seed:  $BASE_SEED"
echo "  K values:   $K_VALUES"
echo "  initial:    v_i, w_i uniform in [-0.5, 0.5]"
echo "  mode:       observables only (3 topologies, full p and ring-k grids)"
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
