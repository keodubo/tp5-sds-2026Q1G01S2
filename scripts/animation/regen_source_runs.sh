#!/usr/bin/env bash
set -euo pipefail

# Regenerate per-neuron state outputs (states.csv) for the TP5 Sistema 2 (FHN)
# potential animations, consistent with output2 (baseSeed=20260607, init [-0.5,0.5]).
# output2 only stored aggregate observables (saveStates=false); the animation needs
# per-neuron v_i(t), so we re-run the exact same configs with --save-states.
#
# Runs all 7 selected configs in parallel (each single-threaded). ~7 min wall on 11 cores.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="${OUT_DIR:-tmp/anim-source-runs}"
BASE_SEED="${BASE_SEED:-20260607}"
N="${N:-501}"
T="${T:-500}"
DT="${DT:-0.005}"
SAVE_INTERVAL="${SAVE_INTERVAL:-0.2}"

mvn -q -DskipTests compile

run() {
  java -cp target/classes ar.edu.itba.sds.tp5.Main single \
    --N "$N" --T "$T" --dt "$DT" --save-interval "$SAVE_INTERVAL" \
    --base-seed "$BASE_SEED" --realization 1 --save-states \
    --output-dir "$OUT_DIR" "$@"
}

# Complete: K = 0.00, 0.10, 0.50
run --topology complete --K 0.00 &
run --topology complete --K 0.10 &
run --topology complete --K 0.50 &
# Random K=0.10: fast (p=0.10) and slow (p=0.01)
run --topology random --K 0.10 --p 0.10 &
run --topology random --K 0.10 --p 0.01 &
# Ring K=0.10: fast (k=10) and slow/never (k=1)
run --topology ring --K 0.10 --k 10 &
run --topology ring --K 0.10 --k 1 &

wait
echo "ALL_REGEN_DONE"
