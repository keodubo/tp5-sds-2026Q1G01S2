#!/usr/bin/env bash
set -euo pipefail

# Pre-final sample grid for TP5 Sistema 2 (FitzHugh-Nagumo).
# This is intentionally smaller than the final enunciado grid: it is meant to
# generate professor-review figures quickly before spending time on the full run.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OUTPUT_DIR="${OUTPUT_DIR:-outputs/fhn-v2-professor-samples-init05-2026-06-07}"
BASE_SEED="${BASE_SEED:-20260607}"
N="${N:-501}"
T="${T:-200}"
DT="${DT:-0.005}"
SAVE_INTERVAL="${SAVE_INTERVAL:-0.5}"
REALIZATIONS="${REALIZATIONS:-3}"

COMPLETE_K_VALUES=(${COMPLETE_K_VALUES:-0.00 0.10 0.50 1.00})
RANDOM_P_VALUES=(${RANDOM_P_VALUES:-0.0001 0.001 0.01 0.1})
RANDOM_K_VALUES=(${RANDOM_K_VALUES:-0.00 0.10 0.50 1.00})
RING_K_VALUES=(${RING_K_VALUES:-1 2 5 10})
RING_COUPLING_VALUES=(${RING_COUPLING_VALUES:-0.00 0.10 0.50 1.00})

EXTRA_ARGS=()
if [[ "${OVERWRITE:-0}" == "1" ]]; then
  EXTRA_ARGS+=(--overwrite)
fi

echo "TP5 FHN professor sample v2"
echo "  output_dir:     $OUTPUT_DIR"
echo "  N:              $N"
echo "  T:              $T"
echo "  dt:             $DT"
echo "  save_interval:  $SAVE_INTERVAL"
echo "  realizations:   $REALIZATIONS"
echo "  base_seed:      $BASE_SEED"
echo "  initial:        v_i, w_i uniform in [-0.5, 0.5]"
echo "  seeds:          distinct runSeed per parameter combination and realization"
echo "  mode:           observables only"
echo

echo "Compiling..."
mvn -q -DskipTests compile

run_single() {
  local topology="$1"
  local realization="$2"
  shift 2

  local cmd=(
    java -cp target/classes ar.edu.itba.sds.tp5.Main single
    --topology "$topology"
    --N "$N"
    --T "$T"
    --dt "$DT"
    --save-interval "$SAVE_INTERVAL"
    --base-seed "$BASE_SEED"
    --realization "$realization"
    --output-dir "$OUTPUT_DIR"
    "${EXTRA_ARGS[@]}"
    "$@"
  )

  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    printf 'DRY_RUN:'
    printf ' %q' "${cmd[@]}"
    echo
  else
    "${cmd[@]}"
  fi
}

total=$(( (${#COMPLETE_K_VALUES[@]} + ${#RANDOM_P_VALUES[@]} * ${#RANDOM_K_VALUES[@]} + ${#RING_K_VALUES[@]} * ${#RING_COUPLING_VALUES[@]}) * REALIZATIONS ))
current=0

for realization in $(seq 1 "$REALIZATIONS"); do
  for coupling in "${COMPLETE_K_VALUES[@]}"; do
    current=$((current + 1))
    echo "[$current/$total] complete K=$coupling rep=$realization"
    run_single complete "$realization" --K "$coupling"
  done

  for probability in "${RANDOM_P_VALUES[@]}"; do
    for coupling in "${RANDOM_K_VALUES[@]}"; do
      current=$((current + 1))
      echo "[$current/$total] random p=$probability K=$coupling rep=$realization"
      run_single random "$realization" --p "$probability" --K "$coupling"
    done
  done

  for ring_k in "${RING_K_VALUES[@]}"; do
    for coupling in "${RING_COUPLING_VALUES[@]}"; do
      current=$((current + 1))
      echo "[$current/$total] ring k=$ring_k K=$coupling rep=$realization"
      run_single ring "$realization" --k "$ring_k" --K "$coupling"
    done
  done
done

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo
  echo "DRY_RUN=1: no runs started."
else
  echo
  echo "OK v2 sample outputs: $OUTPUT_DIR"
fi
