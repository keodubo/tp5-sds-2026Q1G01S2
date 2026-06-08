# K crítico (K_c) — TP5 Sistema 2 (FitzHugh-Nagumo)

Acople mínimo **K_c** donde cada red pasa de *no sincronizar* a *sincronizar* dentro de
`T = 500`. Pedido del profe: barrer `K = 1e-4, 1e-3, 1e-2` (la zona del cambio interesante).

- **Datos:** barrido small-K (`outputs/fhn-sweep-smallK-...`, K = 1e-4/1e-3/1e-2) **combinado**
  con `output2` (K = 0, 0.1, …, 1.0). Eje resultante: `K ∈ {0, 1e-4, 1e-3, 1e-2, 0.1, …, 1.0}`.
  Mismos params: N=501, T=500, dt=0.005, 15 realizaciones, init U[-0.5, 0.5].
- **Criterio:** por corrida, sincroniza si `σ_v(t) ≤ 0.01` y se mantiene hasta T.
  **K_c = onset** donde la *fracción de las 15 realizaciones que sincronizan* cruza 0.5.
  Se reporta como **bracket** `(K_abajo, K_arriba)` por la resolución discreta de K.
- **Solo observables** (`σ_v`); no se necesitan estados por neurona ni animaciones.

## Resultado

| Red | Parámetro | K_c | Notas |
|---|---|---|---|
| **Completa** | — | **< 1e-4** | Sincroniza para todo K ≥ 1e-4. El crítico real está **por debajo** del rango pedido (σ_v cae de 0.85 en K=0 a 0.006 en K=1e-4). |
| **Aleatoria** | p = 0.1 | **≈ 3.2e-4** (1e-4–1e-3) | |
| | p = 0.046 | **≈ 3.2e-3** (1e-3–1e-2) | |
| | p = 0.022 | **≈ 3.2e-3** (1e-3–1e-2) | |
| | p = 0.01 | **≈ 0.25** (0.2–0.3) | Marginal/ruidoso (grafo apenas conectado). |
| | p ≤ 0.0046 | **no sincroniza** | Ni con K=1.0 dentro de T. Grafo demasiado disperso. |
| **Anillo** | k = 10 | **≈ 3.2e-3** (1e-3–1e-2) | |
| | k = 3…9 | **≈ 0.03** (0.01–0.1) | Bracket ancho (hueco grueso del grid). |
| | k = 2 | **≈ 0.14** (0.1–0.2) | |
| | k = 1 | **≈ 0.45** (0.4–0.5) | Solo vecinos inmediatos: necesita acople fuerte. |

## Lectura física

- **Más conectividad ⇒ K_c más chico.** En las tres redes, cuanto más conectada está cada
  neurona (red completa > anillo k grande > aleatoria p grande), menos acople hace falta para
  sincronizar. La red **completa** sincroniza con un acople ínfimo (< 1e-4).
- **Red aleatoria — umbral de conectividad.** Hay un salto abrupto de K_c entre `p = 0.01`
  (K_c ≈ 0.25) y `p = 0.022` (K_c ≈ 0.003): por debajo de p ≈ 0.01 el grafo está apenas
  conectado y sincronizar cuesta muchísimo (o no pasa); por encima, es fácil.
- **Red anillo — monótono en k.** K_c baja al sumar vecinos: de ≈0.45 (k=1) a ≈0.003 (k=10).

## Dónde fue decisivo el barrido small-K

Los K = 1e-4/1e-3/1e-2 fijaron el K_c de los casos más conectados, que caían por debajo de 0.1
(invisibles con el grid viejo): **completa** (< 1e-4), **aleatoria p ≥ 0.1** (1e-4–1e-3) y
**anillo k = 10** (1e-3–1e-2).

## Brackets anchos — refinamiento opcional

Dos casos quedan con bracket ancho por el salto grueso `0.01 → 0.1` del grid heredado:
**anillo k = 3…9** (0.01–0.1) y **aleatoria p = 0.01** (0.2–0.3). Para afinarlos:

```bash
# barrido de refinamiento en el hueco 0.01-0.1
K_VALUES=0.02,0.04,0.06,0.08 OUTPUT_DIR=outputs/fhn-sweep-refineK \
  bash scripts/run_fhn_sweep_smallK.sh
```

## Reproducir

```bash
# 1) (si hace falta) generar el barrido small-K — ~12 min en 10 hilos
bash scripts/run_fhn_sweep_smallK.sh

# 2) análisis K_c (combina small-K + output2) -> figuras + CSV + este .md
python3 scripts/analysis/critical_k.py \
  --input-dir outputs/fhn-sweep-smallK-T500-dt005-init05-observables \
  --input-dir output2 \
  --output-dir results/2026-06-08_kc-smallK_v1
```

## Archivos

- `kc_complete.png` — completa: fracción sync y σ_v estacionaria vs K.
- `kc_random_vs_p.png` — aleatoria: heatmap sync(p, K) + K_c(p).
- `kc_ring_vs_k.png` — anillo: heatmap sync(k, K) + K_c(k).
- `kc_summary.csv` — K_c (estimado, bracket) por configuración.

> Nota: el dato crudo del barrido (`outputs/…`) y `output2/` están **fuera de git** (gitignored,
> ~280 MB). Para verlos hay que regenerarlos con los scripts de arriba.
