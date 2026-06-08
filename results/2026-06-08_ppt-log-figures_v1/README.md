# Figuras de la presentación con eje K logarítmico — TP5 Sistema 2 (FHN)

Regeneración de las figuras K-dependientes de la presentación (`SdS_TP5_..._Presentación.pdf`)
con **eje K en escala logarítmica**, usando las **nuevas corridas de K chico**
(`K = 1e-4, 1e-3, 1e-2`, las 3 redes) combinadas con `output2` (`K = 0, 0.1, …, 1.0`).
El eje K queda `{0, 1e-4, 1e-3, 1e-2, 0.1, …, 1.0}`.

**Por qué log:** en escala lineal toda la transición se aplasta en `K ∈ (0, 0.1)` y no se ve.
En log se revela que la sincronización (y la divergencia de `t_sync` cerca del K crítico)
ocurre a acoples **muy chicos**, que es justo lo que el profe pidió mirar.

## Figuras (mapeo a la presentación)

| Archivo | Slide original | Qué cambia |
|---|---|---|
| `slide16_complete_stationary_vs_K_log.png` | 16 | σ_v estacionaria vs K en log. Completa sincroniza (σ_v≈0) para **todo K ≥ 1e-4**; K=0 (sin acople) ≈ 0.87. |
| `slide17_complete_tsync_vs_K_log.png` | 17 | t_sync vs K en log. Antes era plano en 0.1; ahora se ve la **divergencia**: t_sync ≈ 486 en K=1e-4. |
| `slide21_random_heatmap_sigma_p_K_log.png` | 21 | Heatmap σ_v(p, K) en **log-log**. La frontera de sincronización ahora se ve también en K chico. |
| `slide22_random_stationary_vs_p_log.png` | 22 | σ_v vs p (K=0.1) con eje p log (cosmético; no usa corridas nuevas). |
| `slide26_ring_heatmap_sigma_k_K_log.png` | 26 | Heatmap σ_v(k, K) con K en log. Más vecinos → sincroniza con menos K. |
| `slide27_ring_stationary_vs_k.png` | 27 | σ_v vs k (K=0.1). k son enteros 1–10 → eje lineal (no usa corridas nuevas). |
| `slide28_tsync_vs_K_by_topology_log.png` | 28 | t_sync vs K por topología en log. Se ve la **divergencia de t_sync** cerca del K_c de cada red. |

## Lectura

- **Completa:** sincroniza a acople ínfimo (K_c < 1e-4); cerca de ahí `t_sync` se dispara (~486 en K=1e-4).
- **Aleatoria p=0.1:** K_c entre 1e-4 y 1e-3; `t_sync ≈ 486` en K=1e-3.
- **Anillo k=10:** K_c entre 1e-3 y 1e-2; `t_sync ≈ 490` en K=1e-2.
- Patrón común: **más conectividad → K_c más chico**; cerca del K_c, sincronizar tarda casi todo el run.

## Figuras de la presentación que NO se regeneran (y por qué)

- **Timeseries vs t** (slides 14, 15, 19, 20, 24, 25): el eje es `t`, no `K` → log en K no aplica.
- **Animaciones** (slides 13, 18, 23): el profe indicó no rehacerlas.
- **Diagramas de red / retrato de fase** (slides 3, 11): no tienen eje K.

## Reproducir

```bash
python3 scripts/analysis/ppt_log_figures.py \
  --input-dir outputs/fhn-sweep-smallK-T500-dt005-init05-observables \
  --input-dir output2 \
  --output-dir results/2026-06-08_ppt-log-figures_v1
```

> Nota: el dato crudo (`outputs/…`, `output2/`) está fuera de git (gitignored). Regenerar con
> `scripts/run_fhn_sweep_smallK.sh` + el barrido principal si hiciera falta.
