# Timeseries de la presentación con menos curvas — TP5 Sistema 2 (FHN)

Regeneración de las diapositivas de **evolución temporal** (timeseries vs *t*) mostrando
**3-4 series representativas** en vez de las 10-11 originales (ilegibles). Cumple la
guía de formato (`docs/Guias de Formato/GuiaPresentaciones.pdf`):

- **1.7** sin título dentro de la figura (el título va en la slide).
- **1.8** ejes en palabras, símbolos escalares en itálica, fuente grande (≥20).
- **1.9** notación en **potencias de 10** en las leyendas (`10⁻³`, no `0.001`/`1e-3`/`10^-3`).
- **2.4.2** se muestra una **evolución típica** → una sola realización representativa
  (`seed_0001`). Promediar entre las 15 realizaciones aplastaría la oscilación por desfase.

Datos: barrido small-K (`K=1e-3,1e-2`) + `output2` (`K=0, 0.1`).

## Figuras (mapeo a la presentación actual de 35 págs)

| Archivo | Slide | Serie mostrada |
|---|---|---|
| `slide14_complete_meanv_vs_t.png` | 14 | Completa ⟨v⟩, K = 0, 10⁻³, 10⁻², 10⁻¹ |
| `slide15_complete_sigmav_vs_t.png` | 15 | Completa σ_v, mismos K |
| `slide19_random_meanv_vs_t_by_p.png` | 19 | Aleatoria ⟨v⟩ (K=0.1), p = 10⁻⁴, 10⁻³, 10⁻², 10⁻¹ |
| `slide20_random_sigmav_vs_t_by_p.png` | 20 | Aleatoria σ_v (K=0.1), mismos p |
| `slide21_random_meanv_vs_t_by_K.png` | 21 | Aleatoria ⟨v⟩ (p=0.1), K = 0, 10⁻³, 10⁻², 10⁻¹ |
| `slide22_random_sigmav_vs_t_by_K.png` | 22 | Aleatoria σ_v (p=0.1), mismos K |
| `slide26_ring_meanv_vs_t_by_k.png` | 26 | Anillo ⟨v⟩ (K=0.1), k = 1, 2, 4, 10 |
| `slide27_ring_sigmav_vs_t_by_k.png` | 27 | Anillo σ_v (K=0.1), mismos k |
| `slide28_ring_meanv_vs_t_by_K.png` | 28 | Anillo ⟨v⟩ (k=10), K = 0, 10⁻³, 10⁻², 10⁻¹ |
| `slide29_ring_sigmav_vs_t_by_K.png` | 29 | Anillo σ_v (k=10), mismos K |

> Las figuras `σ_v(t)` incluyen la línea de umbral `σ_v = 10⁻²`. El contraste de
> sincronización se ve mejor en las `σ_v` (las `⟨v⟩` oscilan parecido y se solapan).

## Selección de series (por qué esos valores)

- **K = 0, 10⁻³, 10⁻², 10⁻¹**: cubre desde sin acople hasta el régimen ya sincronizado,
  muestreando la transición en escala log.
- **p = 10⁻⁴ … 10⁻¹** (aleatoria): no sincroniza (10⁻⁴, 10⁻³) → marginal (10⁻²) → sincroniza (10⁻¹).
- **k = 1, 2, 4, 10** (anillo): de no sincronizar a K=0.1 (k=1) a sincronizar (k=10).

## Reproducir

```bash
python3 scripts/analysis/ppt_timeseries_reduced.py \
  --input-dir outputs/fhn-sweep-smallK-T500-dt005-init05-observables \
  --input-dir output2 \
  --output-dir results/2026-06-08_ppt-timeseries-reduced_v1
```
