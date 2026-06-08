#!/usr/bin/env bash
set -euo pipefail

# Render the 7 circular potential animations (MP4 + GIF + PNG) for TP5 Sistema 2.
# Consumes regenerated states.csv (scripts/animation/regen_source_runs.sh).
# Runs all cases in parallel. Shared colour bar [-2, 2]; MP4 at x4 (full T=500).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

SRC="${SRC:-tmp/anim-source-runs/runs}"
OUT="${OUT:-outputs/2026-06-08_potential-animations_v1}"
PY="python3 scripts/animation/animate_potential.py"

mkdir -p "$OUT/logs"

render() {  # run_subpath  label  title
  $PY --run-dir "$SRC/$1/seed_0001" --output-dir "$OUT" --label "$2" --title "$3" \
    > "$OUT/logs/$2.log" 2>&1 && echo "OK   $2" || echo "FAIL $2 (see $OUT/logs/$2.log)"
}

# Red completa: K = 0.00 (sin acople), 0.10, 0.50
render "complete/K_0.00" "completa_K0.00" 'Red completa,  $K = 0.00$  (sin acople)' &
render "complete/K_0.10" "completa_K0.10" 'Red completa,  $K = 0.10$' &
render "complete/K_0.50" "completa_K0.50" 'Red completa,  $K = 0.50$' &
# Red aleatoria (K=0.10): rapido (p=0.10) vs lento (p=0.01)
render "random/p_0.10/K_0.10" "aleatoria_p0.10_rapido" 'Red aleatoria,  $p = 0.10,\ K = 0.10$  (rapido)' &
render "random/p_0.01/K_0.10" "aleatoria_p0.01_lento"  'Red aleatoria,  $p = 0.01,\ K = 0.10$  (lento)' &
# Red anillo (K=0.10): rapido (k=10) vs lento/no-sincroniza (k=1)
render "ring/k_10/K_0.10" "anillo_k10_rapido" 'Red anillo,  $k = 10,\ K = 0.10$  (rapido)' &
render "ring/k_01/K_0.10" "anillo_k01_lento"  'Red anillo,  $k = 1,\ K = 0.10$  (lento, no sincroniza)' &

wait
echo "ALL_RENDER_DONE"
