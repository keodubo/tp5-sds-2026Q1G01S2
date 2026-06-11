# Conclusiones respaldadas — TP5 Sistema 2 (FitzHugh-Nagumo)

Versión para reemplazar la slide de conclusiones. Está armada solo con resultados ya generados:

- barrido principal `output2/` (`K = 0, 0.1, ..., 1.0`);
- barrido small-K `outputs/fhn-sweep-smallK-T500-dt005-init05-observables/` (`K = 10^-4, 10^-3, 10^-2`);
- análisis `results/2026-06-08_kc-smallK_v1/` y figuras logarítmicas de `results/2026-06-08_ppt-log-figures_v1/`.
- tabla de chequeo `metricas_respaldo.csv` en esta carpeta.

Parámetros comunes: `N = 501`, `T = 500`, `dt = 0.005`, 15 realizaciones, condiciones iniciales actuales `v_i(0), w_i(0) ~ U[-0.5, 0.5]`.

---

## Texto recomendado para la slide

**1. La sincronización tiene un umbral de acople y, lejos de ese umbral, aparece muy rápido.**
En red completa, `K_c < 10^-4`: con `K = 10^-4` la sincronización recién aparece al final (`t_sync = 486.9`), pero con `K = 10^-3` baja a `t_sync = 24.2` y con `K = 0.1` es prácticamente inmediata (`t_sync = 0.1`).

**2. El acople crítico no es único: depende fuertemente de la conectividad.**
La red completa sincroniza con `K_c < 10^-4`; la aleatoria densa (`p = 0.1`) tiene `K_c ≈ 3.2×10^-4`; el anillo pasa de `K_c ≈ 4.5×10^-1` para `k = 1` a `K_c ≈ 3.2×10^-3` para `k = 10`. En redes aleatorias muy dispersas (`p <= 4.6×10^-3`) no hubo sincronización dentro de `T = 500` ni con `K = 1`.

**3. Cambiar las condiciones iniciales era necesario para no forzar una sincronización artificial.**
Con el rango angosto `U[-0.05, 0.05]`, las neuronas arrancaban casi iguales: en la red completa sin acople (`K = 0`) se obtenía `sigma_v(0) ≈ 2.9×10^-2` y el criterio marcaba sincronización en `15/15` corridas. Con `U[-0.5, 0.5]`, el mismo caso arranca con `sigma_v(0) ≈ 2.8×10^-1`, no sincroniza (`0/15`) y queda con `sigma_v` estacionaria ≈ `8.6×10^-1`, que es lo esperable cuando no hay acople.

---

## Respaldo numérico

| Afirmación | Dato medido | Fuente |
|---|---:|---|
| Criterio de sincronización | una corrida sincroniza si `sigma_v(t) <= 0.01` y se mantiene hasta `T` | `scripts/analysis/fhn.py`, `scripts/analysis/critical_k.py` |
| Definición de `K_c` | primer `K` donde sincroniza al menos el 50% de las 15 realizaciones | `results/2026-06-08_kc-smallK_v1/kc_summary.md` |
| Red completa | `K_c < 10^-4`; `sigma_v` cae de ≈ `0.865` en `K=0` a ≈ `0.0064` en `K=10^-4` | `kc_summary.csv`, `kc_complete.png` |
| Red completa: rapidez lejos de `K_c` | `t_sync = 486.9` (`K=10^-4`), `24.2` (`K=10^-3`), `0.1` (`K=0.1`) | recalculado desde `observables.csv`; figura `slide17_complete_tsync_vs_K_log.png` |
| Aleatoria densa | `p=0.1`: `K_c ≈ 3.2×10^-4` con bracket `(10^-4, 10^-3)` | `kc_summary.csv`, `kc_random_vs_p.png` |
| Aleatoria dispersa | `p <= 4.6×10^-3`: no sincroniza dentro de `T=500` hasta `K=1` | `kc_summary.csv`, `kc_random_vs_p.png` |
| Anillo local | `k=1`: `K_c ≈ 4.5×10^-1`; `k=10`: `K_c ≈ 3.2×10^-3` | `kc_summary.csv`, `kc_ring_vs_k.png` |
| Condición inicial angosta | red completa, `K=0`: `sigma_v(0)=0.0289±0.0004`, sincroniza `15/15` | `output/fhn-sweep-T500-dt005-observables/` |
| Condición inicial actual | red completa, `K=0`: `sigma_v(0)=0.284±0.006`, sincroniza `0/15`, `sigma_tail=0.865±0.032` | `output2/` |
| Cambio de rango implementado | commit `b283647`: reemplaza `-0.05 + 0.1*rand` por `INITIAL_STATE_MIN=-0.5`, `INITIAL_STATE_MAX=0.5` y agrega metadata del rango inicial | `git show b283647 -- FhnSimulation.java OutputWriter.java` |

---

## Explicación para decir oralmente

El FitzHugh-Nagumo sin acople ya tiene una dinámica oscilatoria propia. Si todas las neuronas arrancan en un entorno demasiado chico alrededor del mismo punto, siguen trayectorias casi iguales aunque `K = 0`; por eso las corridas con `[-0.05, 0.05]` casi no se distinguían entre realizaciones y podían parecer sincronizadas sin que la red estuviera produciendo esa sincronización.

Al usar `[-0.5, 0.5]`, la dispersión inicial esperada sube diez veces: para una uniforme `U[-a,a]`, `std = a/sqrt(3)`, por lo que pasa de `0.05/sqrt(3) = 0.0289` a `0.5/sqrt(3) = 0.2887`. Eso separa mejor las trayectorias no acopladas y permite que la reducción de `sigma_v` se atribuya al acople y a la topología, no a haber inicializado todas las neuronas casi iguales.

---

## Qué quitar o dejar como opcional

Quitaría de la slide final la conclusión sobre `K·<grado>` salvo que agreguen antes la figura `results/2026-06-08_effective-coupling_v1/effective_coupling_collapse.png` como resultado. La idea está bien sustentada, pero si no se muestra esa figura antes de conclusiones queda como afirmación nueva.

---

## Caveats

- Los `K_c` puntuales son estimaciones por media geométrica dentro de brackets discretos, no barridos continuos.
- Para la red completa solo se puede afirmar `K_c < 10^-4`; el valor exacto queda por debajo del menor `K` no nulo probado.
- En anillo `k=3..9` el bracket es ancho (`0.01` a `0.1`), así que conviene no sobredetallar esos casos en la slide.
- La corrida vieja no guardaba `initialStateMin/Max` en `metadata.properties`; el rango `[-0.05, 0.05]` queda respaldado por el diseño/código histórico y por `sigma_v(0) ≈ 0.029`, consistente con ese rango.
