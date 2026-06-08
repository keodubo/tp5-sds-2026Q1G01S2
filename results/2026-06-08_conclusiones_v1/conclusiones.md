# Conclusiones — TP5 Sistema 2 (FitzHugh-Nagumo)

Conclusiones revisadas, **basadas solo en resultados mostrados** (guía 2.5) y con cifras
en **potencias de 10** (guía 1.9). Cada una indica la(s) figura(s) que la respaldan.

> Corrige dos cosas del PPT actual:
> 1. La conclusión 1 decía *"σ_v colapsa de ~2×10⁻¹ a ~0"* → el valor sin acople es **≈9×10⁻¹** (0.87).
> 2. La conclusión 2 decía *"lo que manda es el acople efectivo ∝ K·grado"* → **el test de colapso lo refuta** (ver figura de acople efectivo); reemplazada por una versión correcta.

---

## Texto para la slide (4 bullets)

**1. La sincronización aparece por un umbral de acople.**
Superado un acople crítico K_c, la dispersión estacionaria colapsa de **σ_v ≈ 9×10⁻¹**
(sin acople) a **σ_v < 10⁻²** (red sincronizada).
*(figuras: completa σ_v vs K · heatmaps p–K y k–K · aleatoria σ_v vs p)*

**2. El acople crítico K_c decrece con la conectividad de la red.**
A más conexiones por neurona, menos acople hace falta:
- completa (grado 500): **K_c < 10⁻⁴**
- aleatoria: K_c cae al subir p; por debajo de **p ≈ 10⁻²** no sincroniza en T = 5×10²
- anillo: de **K_c ≈ 4×10⁻¹** (k = 1) a **≈ 3×10⁻³** (k = 10)
*(figuras: completa σ_v vs K · heatmaps · aleatoria σ_v vs p)*

**3. Cerca de K_c la sincronización es lenta; lejos, casi inmediata.**
t_sync diverge al acercarse a K_c (completa: **t_sync ≈ 5×10²** en K = 10⁻⁴) y cae al
aumentar K. A igual K, la red más global sincroniza mucho más rápido (completa ≪ anillo).
*(figuras: completa t_sync vs K · t_sync por topología)*

**4. El grado medio no alcanza para explicar la transición.**
Reescalando por el acople efectivo **K·⟨grado⟩**, las tres redes **no colapsan** en una
sola curva (completa transiciona en K_eff < 5×10⁻², anillo ≈ 10⁻¹, aleatoria ≈ 1): es la
**estructura global** de la red, y no solo el grado, lo que fija el umbral.
*(figura nueva: acople efectivo — agregarla a Resultados antes de Conclusiones)*

---

## Notas de uso

- Las conclusiones 1–3 ya están 100% respaldadas por figuras que están en el PPT.
- La conclusión 4 **requiere mostrar** `effective_coupling_collapse.png` como slide de
  Resultados (si no la agregás, omitir la conclusión 4). Está en
  `results/2026-06-08_effective-coupling_v1/`.
- Mantener una sola diapositiva de conclusiones (guía 2.5). Si querés solo 3 bullets,
  usar 1–3 y omitir 4.
