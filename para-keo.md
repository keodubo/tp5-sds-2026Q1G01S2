# Auditoría de entrega — TP5 Dinámica Neuronal (FitzHugh–Nagumo)

> Respuesta a la auditoría pedida por Keo. **Es solo auditoría: no se modificó ni el código ni la presentación ni el guion.** Solo se revisó y se reporta.

## Qué se auditó

- **Enunciado**: `docs/TP5_Enunciado.pdf` (Sistema 2, FitzHugh–Nagumo).
- **Guía de formato**: `docs/Guias de Formato/GuiaPresentaciones.pdf`.
- **Presentación**: `SdS_TP5_2026Q1G01CS2_Presentación.pdf`, **36 diapositivas** (versión actual en la rama `feat/kc-smallk-log-figures`, ya con la slide 33 de condición inicial).
- **Código del motor**: `src/main/java/ar/edu/itba/sds/tp5/` (5 archivos: `Main`, `Config`, `Topology`, `FhnSimulation`, `OutputWriter`), como representante del zip a entregar.

> ⚠️ **Importante**: se auditó lo que está en el repo, no un zip físico ni el PDF final que vayas a subir. Antes de entregar, confirmá que el zip y el PDF que subís a Campus son **exactamente** estos.

---

## Resumen ejecutivo (semáforo)

| Categoría | Cantidad | Lo más urgente |
|---|---|---|
| 🔴 Crítico | 2 | Faltan links a animaciones; faltan 2 mapas 2D de tiempo de sincronización |
| 🟠 Medio | 10 | Motor calcula observables; faltan nº de realizaciones/dt; criterio de sincronización sin definir; conclusión 2 sin respaldo gráfico |
| 🟡 Leve | 7 | Texto chico en figuras; "seed" en slide 5; título interno en slide 25 |
| ✅ OK | — | Estructura de resultados, una-figura-varias-curvas, sin índice, código compacto |

---

## 🔴 CRÍTICO

### C1 — Faltan los links a las animaciones (slides 13, 18, 25)
El enunciado (punto **a**) y la guía (pág. 3, punto 2.4.8) exigen que el PDF de entrega tenga, debajo de cada fotograma, un **link explícito a YouTube/Vimeo**. Verificado: **el PDF no contiene ninguna URL**. Sin esto, las animaciones se consideran **no entregadas**.
**Acción**: subir los videos y escribir el link visible bajo cada fotograma de las slides 13 (completa), 18 (aleatoria) y 25 (anillo).

### C2 — Faltan los 2 mapas 2D de tiempo de sincronización
El enunciado pide, **para la red aleatoria y para el anillo, DOS representaciones 2D**: una de dispersión **y otra del tiempo de sincronización**.
- Red aleatoria: está la de dispersión (slide 23), **falta** la de tiempo de sincronización en función de `(p, K)`.
- Anillo: está la de dispersión (slide 30), **falta** la de tiempo de sincronización en función de `(k, K)`.

Las slides 24 y 31 **no reemplazan** estos mapas: son curvas 1D (σv vs p y σv vs k), no mapas 2D, y son de dispersión, no de tiempo. La slide 32 (comparación entre redes) tampoco los reemplaza: es una superposición de curvas para un valor fijo de p y k.
**Acción**: agregar dos heatmaps de tiempo de sincronización, `(p,K)` y `(k,K)`.

---

## 🟠 MEDIO

### M1 — El motor calcula los observables durante la simulación (repite corrección TP3-D10)
`FhnSimulation.save()` calcula `⟨v⟩` y `σv` **dentro del motor** y los vuelca a `observables.csv`; el análisis Python consume ese CSV en vez de recalcular desde el estado. En los barridos grandes no se guarda `states.csv` (es opcional con `--save-states`), así que para esas corridas **no hay forma de recalcular** los observables a partir del estado.
En el TP3 marcaron textualmente: *"Los cálculos de observables NO deben hacerse durante la simulación, deben poder hacerse posteriormente con los outputs."*
**Matiz a favor**: acá `⟨v⟩` y `σv` son promedios **instantáneos triviales del estado** (no cálculos complejos como la regresión de J o la interpolación de C_fc del TP3), y guardar 501 valores por paso solo para promediarlos después no tiene sentido computacional.
**Acción / defensa**: tener listo el argumento de que el motor solo vuelca *promedios instantáneos del estado*, y que los escalares pesados (tiempo de sincronización, σv estacionaria, K_c) sí se calculan en el post-proceso. Si querés blindarlo del todo, que el análisis pueda recalcular σv desde `states.csv` en al menos un caso testigo.

### M2 — La slide 5 (Arquitectura) describe formato de archivos y post-proceso
La guía (punto 2.2) dice que la sección Implementación debe tratar **solo el motor de simulación**, *"dejando fuera de esta descripción cómo se implementa el post-proceso, o el formato de los archivos input/output"*. La slide 5 dedica buena parte a `observables.csv`, `states.csv`, `metadata.properties`, `adjacency.csv` y a los módulos de análisis/animación.
**Acción**: recortar el detalle de formato de archivos y de post-proceso; dejar en Implementación solo cómo se traduce el modelo a código (lo del motor).

### M3 — Falta el número de realizaciones y los tiempos de simulación en Simulaciones
La guía (punto 2.3) pide *"detallar el número de repeticiones y tiempos de las simulaciones realizadas"*. En las slides de Simulaciones (9–11) no figura explícito que se usaron **15 realizaciones**, `T = 500` y `dt = 0,005`.
**Acción**: agregar esos datos (en la slide de parámetros o de observaciones).

### M4 — El criterio de sincronización y el "tiempo de sincronización" no están definidos
Se usan en las slides 15, 17, 24, 31, 32 (umbral `σv = 10⁻²`, t_sync) pero **nunca se define formalmente** qué es estar sincronizado ni cómo se mide el tiempo de sincronización. Es el mismo tipo de observación que recibieron en TP3/TP4 (observables/escalares usados sin definir).
**Acción**: una slide (o un recuadro en Observables) con la definición: *una corrida sincroniza si σv(t) ≤ 10⁻² y se mantiene hasta T; el tiempo de sincronización es el último instante en que cruza ese umbral*.

### M5 — La conclusión 2 cita valores de K_c que no se muestran en ninguna figura (repite corrección TP2)
La conclusión 2 (slide 35) afirma `K_c < 10⁻⁴` (completa), `≈ 3×10⁻⁴` (aleatoria densa), `≈ 3×10⁻³ … 0,45` (anillo). Esos valores puntuales **no aparecen en ninguna slide de resultados** (las slides muestran σv vs p, σv vs k, no K_c vs topología). En TP2 marcaron: *"para decir X deben mostrar una gráfica que lo demuestre"*.
**Acción**: o agregar una figura que muestre K_c por topología, o reformular la conclusión 2 sin números que no estén graficados.

### M6 — Barras de error faltantes en las slides 16 y 17 (red completa)
La guía (2.4.3) pide barras de error al promediar realizaciones. Las slides 24 (aleatoria) y 31 (anillo) las tienen; **las 16 (σv estacionaria vs K) y 17 (t_sync vs K) de la red completa, no**. Es exactamente el tipo de inconsistencia de desvío que marcaron en TP2 (*"el desvío informado no es correcto / está subrepresentado"*).
**Acción**: agregar desvío/barras de error sobre las 15 realizaciones en 16 y 17.

### M7 — Condiciones iniciales `[-0,5; 0,5]` difieren del enunciado escrito `[-0,05; 0,05]`
El enunciado pide `[-0,05; 0,05]`. El grupo usa `[-0,5; 0,5]` por **indicación del profesor del 2026-06-07** (registrado en `AGENTS.md`), y ahora está respaldado por la slide 33. Está bien, pero un corrector que no conozca esa indicación lo verá como desvío del enunciado.
**Acción**: tener a mano la prueba de la indicación; idealmente mencionar en la slide 33 (o al pie) que el rango se cambió por indicación de cátedra.

### M8 — No se muestra la justificación del `dt`
El enunciado pide `dt` fijo e intrínseco; en TP4 valoraron mostrar que el resultado es estable para distintos `dt`. No hay ninguna slide que justifique `dt = 0,005` (comparación con dt menores / estabilidad).
**Acción**: agregar una slide o mención de cómo se eligió el `dt` (resultado estable al reducirlo).

### M9 — Palabra "seed" en la slide 5 (repite corrección TP2)
En TP2 marcaron que **"seed"** describe el código y no el problema, y que lo correcto es **"realizaciones / repeticiones"**. La slide 5 dice *"params, seed, topología"*.
**Acción**: reemplazar "seed" por "realización" (o quitarlo si esa parte se recorta por M2).

### M10 — No se aclara la adimensionalidad / unidades (roce con corrección TP4)
En TP4 marcaron como importante las **unidades de K y de los dt**. El FHN es adimensional, así que no llevan unidades físicas, pero conviene **aclararlo explícitamente** para que no parezca un olvido.
**Acción**: una nota corta indicando que las magnitudes del modelo son adimensionales.

---

## 🟡 LEVE

- **L1 — Texto muy chico en los fotogramas de animación** (slides 13, 18, 25): `N=501`, `t=`, `sigma_v=`, `<v>=` están mucho más chicos que el resto. Repite TP2-D20 y la guía 1.8 (texto de figura de tamaño similar al de la slide, ≥20 pt).
- **L2 — Slide 5 con mucho texto**: densa en listas; la guía 1.6 pide evitar texto excesivo (relacionado con M2).
- **L3 — Fotogramas tomados en `t = 0`**: la guía (pág. 3) pide un **fotograma representativo**; en `t=0` no se ve la dinámica. Conviene uno a tiempo intermedio.
- **L4 — Título dentro de la figura en la slide 25** ("Red anillo - k=1, K=0.10 (lento, no sincroniza)"): la guía 1.7 dice que las figuras no llevan título interno; la info de configuración va al costado.
- **L5 — Ejes de heatmaps con símbolos** (`K`, `p`, `k`): la guía 1.8 prefiere palabras ("acople", "probabilidad", "vecinos").
- **L6 — Decimales excesivos en los fotogramas** (`sigma_v = 0.2750`, 4 decimales): son valores instantáneos de una corrida, pero roza la observación de TP2 sobre cifras significativas. Reducir a 2 decimales.
- **L7 — Título genérico "Observables" (slide 10)**: en TP3-D29 marcaron no usar nombres genéricos; acá está atenuado porque la slide sí define cada observable, pero el título es genérico.

---

## Cruce explícito con los errores de TP2/TP3/TP4

**¿Se está repitiendo alguno?** Sí, varios — están señalados arriba:

| Error previo | ¿Se repite en TP5? | Dónde |
|---|---|---|
| TP2 — Interpretación sin respaldo gráfico | **Sí** | M5 (K_c en conclusión 2) |
| TP2 — Palabras en inglés ("seed") | **Sí** | M9 (slide 5) |
| TP2 — Desvío/barras de error mal o ausentes | **Sí** | M6 (slides 16, 17) |
| TP2-D20 / TP4 — Texto chico en figuras | **Sí** | L1 |
| TP2 — Cifras significativas / decimales | **Parcial** | L6 (fotogramas) |
| TP3-D10 — Observables calculados en el motor | **Sí (con matiz)** | M1 |
| TP3 — Observables/escalares sin definir | **Sí** | M4 (criterio de sincronización) |
| TP4 #11 — Unidades de K y dt | **Sí (adimensional, sin aclarar)** | M10 |
| TP4 #17 — Justificación del dt | **Sí (falta)** | M8 |
| Guía 2.2 — Implementación incluye post-proceso/formato | **Sí** | M2 |

**Errores previos que esta vez SÍ evitaron (bien):**
- TP4 #14-15 — Estructura de resultados (animación → evoluciones temporales → curva resumen): **respetada** en las tres redes.
- TP2-D28 / TP3-D25-27 — Varias figuras que deberían ser una con colores: **corregido**; las evoluciones temporales usan una figura con varias curvas.
- TP3 — Índice en presentación corta: **no hay índice**, usan separadores (correcto).
- TP4 #29 / TP3 — Referenciar TPs previos por número: **no lo hacen**.
- TP4 #23 — Colorbar para variable discreta: **no aplica**; los colorbars son para potencial (continuo).

---

## ✅ Lo que está OK

- **Enunciado (funcional)**: `N = 501 > 500`; parámetros `I=0,5`, `ε=0,08`, `a=0,7`, `b=0,8`; 15 realizaciones (>10); `p` con 10 valores log en `[10⁻⁴, 10⁻¹]`; `k ∈ [1,10]`; `K ∈ [0,1]`; red completa **completa** (animación, ⟨v⟩, σv, σv estacionaria vs K, t_sync vs K); comparación de tiempos entre redes (slide 32).
- **Conclusión 3 ahora respaldada** por la slide 33 (antes era una afirmación sin figura — corregido).
- **Formato**: diapositivas numeradas; separadores de sección sin numerar; Introducción ≤ 3 slides; Conclusiones en 1 slide; cierre sin la palabra "preguntas"; observables definidos matemáticamente (slide 10); escala log donde corresponde; puntos marcados con símbolos en las curvas de resultados.
- **Arquitectura**: motor separado de análisis y de animación; salida en archivos de texto; la velocidad de animación no depende de la simulación.
- **Código (zip)**: 5 archivos del motor; **34,9 kB sin comprimir / 8,5 kB comprimido (zip)** → por debajo del límite de 20 kB. Default de condición inicial `[-0,5; 0,5]` (coincide con las slides). Nombre de archivo de presentación correcto.

---

## Checklist final antes de subir a Campus

**Bloquean la nota (hacer sí o sí):**
- [ ] Subir los videos y poner el **link visible** bajo cada fotograma (slides 13, 18, 25). *(C1)*
- [ ] Agregar los **2 heatmaps de tiempo de sincronización**: `(p,K)` y `(k,K)`. *(C2)*

**Muy recomendable (evitan repetir correcciones):**
- [ ] **Barras de error** en slides 16 y 17. *(M6)*
- [ ] Agregar **nº de realizaciones (15), T=500, dt=0,005** y la **justificación del dt**. *(M3, M8)*
- [ ] **Definir** el criterio de sincronización y el tiempo de sincronización. *(M4)*
- [ ] Sacar de la **conclusión 2** los K_c que no estén graficados, o agregar la figura. *(M5)*
- [ ] Recortar de la slide de Implementación el **formato de archivos y post-proceso**; cambiar **"seed" → "realización"**. *(M2, M9)*
- [ ] Aclarar **adimensionalidad** y tener a mano la **indicación del profesor** sobre las CI. *(M10, M7)*

**Detalle fino (si hay tiempo):**
- [ ] Agrandar texto en fotogramas; usar fotograma a tiempo intermedio; quitar título interno de la slide 25; reducir decimales. *(L1, L3, L4, L6)*

**Del zip de código:**
- [ ] Incluir **solo el motor** (`Main`, `Config`, `Topology`, `FhnSimulation`, `OutputWriter`), sin `src/test/`, `scripts/`, `outputs/`, `docs/` ni resultados.
- [ ] Verificar que el default de CI sea `[-0,5; 0,5]` (es la versión que generó las figuras).
- [ ] Nombre del archivo: `SdS_TP5_2026Q1G01CS2_Codigo`.
