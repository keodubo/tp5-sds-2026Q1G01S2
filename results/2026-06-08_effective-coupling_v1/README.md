# Acople efectivo K·⟨grado⟩ — test de colapso · TP5 Sistema 2 (FHN)

Pone a prueba la hipótesis *"lo que gobierna la sincronización no es K sino el acople
efectivo K_eff = K·⟨grado⟩"*. Grado medio por topología:

- completa: `N-1 = 500`
- aleatoria p: `p·(N-1) = 500p`
- anillo k: `2k`

Si la hipótesis fuera cierta, `σ_v` estacionaria vs `K_eff` colapsaría las tres redes
en una sola curva de transición.

## Resultado: **NO colapsa**

`effective_coupling_collapse.png` muestra que cada topología transiciona en un `K_eff`
distinto, separados ~2 órdenes de magnitud:

| Red | Transición (σ_v de ≈0.87 → ~0) |
|---|---|
| completa | `K_eff < 5×10⁻²` |
| anillo | `K_eff ≈ 10⁻¹` |
| aleatoria | `K_eff ≈ 1–3` |

**Conclusión:** el grado medio captura la *dirección* (más conexiones → menos acople),
pero **no es el parámetro de control**: la **estructura global** de la red (conectividad
/ cómo se propaga el acople) importa más allá del grado. Por eso la aleatoria —que cerca
de su umbral está fragmentada (p ≈ percolación)— necesita mucho más K_eff que el anillo,
que aunque tiene grado bajo siempre está conectado.

> Esto **refuta** la conclusión 2 original del PPT ("lo que manda es K·grado"). Mostrar
> esta figura habilita la versión corregida (guía 2.5: las hipótesis deben mostrarse).

## Reproducir

```bash
python3 scripts/analysis/effective_coupling.py \
  --input-dir outputs/fhn-sweep-smallK-T500-dt005-init05-observables \
  --input-dir output2 \
  --output-dir results/2026-06-08_effective-coupling_v1
```
