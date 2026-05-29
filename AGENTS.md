# AGENTS.md - TP5 SDS 2026Q1 G01 CS2

## Reglas Operativas

- Usar el skill/plugin de Superpowers cuando aplique. Como minimo, revisar skills antes de empezar tareas no triviales.
- Leer este archivo al inicio de cada tarea. Si se agrega `CLAUDE.md`, leerlo tambien.
- Trabajar en espanol salvo que el usuario pida otro idioma.
- Mostrar un plan antes de hacer trabajo no trivial. Para tareas chicas, asumir lo razonable y explicitar la asuncion.
- Ser accionable: terminar con el siguiente paso claro o con una lista corta de verificacion cuando haya ejecucion.
- Dar siempre un resumen tipo diff de cambios cuando se editen documentos, codigo o configuracion.
- No borrar archivos ni hacer acciones irreversibles sin confirmacion explicita.
- No modificar archivos fuera del alcance pedido. Por defecto, tratar `docs/` como material fuente de solo lectura.
- No pegar secretos, tokens, credenciales ni URLs privadas. Redactar logs sensibles.

## Prioridad de Fuentes

1. Pedido directo del usuario.
2. `docs/TP5_Enunciado.pdf` (enunciado actualizado por Campus el 2026-05-29; reemplaza la version del 2026-05-22).
3. `docs/Guias de Formato/GuiaPresentaciones.pdf` y `docs/Guias de Formato/GuiaInformes.pdf`.
4. Teoricas en `docs/Teoricas/`, especialmente `Teorica5a.pdf` y `Teorica5b.pdf` para TP5.
5. Bibliografia en `docs/bibliografia/`, especialmente `docs/bibliografia/BiblioTP5/EL12286.pdf` para materia activa.

Si hay conflicto, seguir el enunciado y marcar explicitamente la inconsistencia.

## Contrato del TP5

- Tema: comportamiento colectivo.
- Fecha limite de entrega: 2026-06-12 a las 10:00 por Campus.
- Entregables oficiales:
  - Presentacion PDF con links explicitos a animaciones en YouTube, Vimeo o similar. No entregar archivos de animacion.
  - Codigo fuente solo del motor de simulacion, ultima version, sin outputs, documentos ni artefactos auxiliares. Objetivo de tamano: menor a 20 kB.
- Nombres oficiales segun enunciado:
  - `SdS_TP5_2026Q1G01CS2_Presentación`
  - `SdS_TP5_2026Q1G01CS2_Codigo`
- La simulacion debe generar output en archivos de texto.
- El analisis y el modulo de animacion deben ejecutarse de forma independiente tomando esos archivos de texto como input.
- La velocidad de animacion y postproceso no debe depender de la velocidad de simulacion.
- El `dt` es fijo e intrinseco de la simulacion. Para sistemas no conservativos, justificarlo reduciendo `dt` hasta que los resultados cambien menos que un error aceptable.
- Alcance actual confirmado por el usuario: implementar el Sistema 2, FitzHugh-Nagumo. No implementar Sistema 1 ni Sistema 3 salvo pedido explicito.
- El PDF actualizado del 2026-05-29 ya no contiene la regla previa que obligaba a mostrar Sistema 1 antes del sistema principal. Si se trabaja en slides o entrega final, seguir el enunciado actualizado y confirmar alcance; para codigo/motor, el alcance por defecto sigue siendo Sistema 2.

## Sistemas del Enunciado

### Sistema 1 - Kuramoto en redes neuronales

- N debe ser mayor a 500.
- Fases iniciales uniformes en `[0, 2*pi)`.
- Frecuencias naturales aleatorias normales con media 1 y desvio 0.1.
- Observable principal: parametro de orden global `r(t)`.
- Redes:
  - Totalmente conectada: estudiar `K` en `[0, 1]`, varias realizaciones independientes, curva estacionaria `r(K)`, valor critico y tiempo de sincronizacion.
  - Aleatoria: `Aij = 1` con probabilidad `p`, minimo 10 valores de `p` en `[10^-4, 10^-1]` distribuidos logaritmicamente; para el estudio inicial usar `K = 0.1`; luego mapas 2D de sincronizacion y tiempo vs `p, K`.
  - Anillo: vecindad `v` en `[1, 10]` con indices periodicos; para el estudio inicial usar `K = 0.1`; luego mapas 2D de sincronizacion y tiempo vs `v, K`.

### Sistema 2 - FitzHugh-Nagumo

- Este es el sistema principal del repo.
- N debe ser mayor a 500.
- Variables por neurona: potencial `v_i` y recuperacion `w_i`.
- Parametros del enunciado: `I = 0.5`, `epsilon = 0.08`, `a = 0.7`, `b = 0.8`.
- Condiciones iniciales uniformes para `v_i` y `w_i` en `[-0.05, 0.05]`.
- Observables: potencial promedio `<v(t)>` y dispersion espacial `sigma_v(t)`.
- Definir un umbral de dispersion para sincronizacion.
- El motor debe cubrir las tres topologias pedidas para Sistema 2: red totalmente conectada, red aleatoria y red anillo.
- Las salidas de texto deben permitir reconstruir analisis y animaciones sin rerun: tiempos, estado por neurona o variables suficientes, parametros, topologia, seed y observables directos cuando corresponda.
- Redes:
  - Totalmente conectada: estudiar comportamiento temporal, dispersion promediada en mas de 10 realizaciones, tiempo de sincronizacion y `sigma_v` estacionaria vs `K`.
  - Aleatoria: minimo 10 valores de `p` en `[10^-4, 10^-1]` distribuidos logaritmicamente; para el estudio inicial usar `K = 0.1`; luego mapas 2D de dispersion y tiempo vs `p, K`.
  - Anillo: `k`/vecindad en `[1, 10]`; para el estudio inicial usar `K = 0.1`; luego mapas 2D de dispersion y tiempo vs vecindad y `K`.
- Comparar tiempos de sincronizacion o llegada al estacionario entre tipos de red.

### Sistema 3 - Materia activa y presion

- Particulas circulares en recinto circular.
- Parametros del enunciado: `r_p = 1.6 cm`, `R = 10 cm`, `v0 = 0.825 cm/s`, `kappa = 50 1/s`, ruido gaussiano de media 0 y desvio 0.05.
- Simular `N = 20..27` agentes y alcanzar `Tf = 10000 s`.
- Determinar y justificar un `dt` apropiado.
- Movimiento quiral: `sigma_i = 1` fijo.
- Movimiento aleatorio: `sigma_i` toma `+/-1` aleatorio cada 1 s.
- Entregar animaciones representativas para distintos `N`.
- Para dos valores representativos de `N`, reportar velocidad promedio vs tiempo, presion sobre paredes vs tiempo y velocidad promedio vs presion.
- Reportar velocidad promedio estacionaria y presion promedio sobre paredes vs `N`.
- Definir umbral de velocidad promedio para distinguir estado fluido y atascado.
- Identificar periodos atascados, calcular fraccion de tiempo atascado y graficar vs `N`.
- Comparar movimiento quiral contra movimiento aleatorio.

## Flujo de Trabajo Recomendado

1. Releer el enunciado y confirmar si la tarea actual es motor, analisis, animacion o presentacion. Para implementacion de motor, asumir Sistema 2.
2. Escribir una mini-especificacion del motor: parametros, seeds, formato de input/output, observables directos y criterio de estacionario/sincronizacion.
3. Implementar el motor separado del analisis y de la animacion.
4. Generar outputs de texto reproducibles, con semillas registradas.
5. Hacer scripts de analisis/figuras que consuman outputs existentes; no mezclar postproceso dentro del motor.
6. Hacer scripts de animacion que consuman los mismos outputs.
7. Para barridos largos, usar corridas resumibles y logs de progreso. No reiniciar barridos caros si ya hay salidas validas.
8. Antes de entregar, auditar el paquete final contra el enunciado: nombres, peso, contenido, reproducibilidad y ausencia de outputs/documentos dentro del codigo.

## Testing y Verificacion

- Tests que Codex implemente: unit-level, blackbox y behavior-only salvo instruccion contraria explicita.
- Probar contratos publicos: parseo de parametros, generacion de output, determinismo con seed fija, validacion de rangos, calculo de observables y errores esperados.
- No testear metodos privados, orden exacto de llamadas, strings internos, estructura privada ni detalles de framework.
- Preferir pocos tests valiosos a cobertura artificial.
- Para el motor, agregar al menos un smoke test de CLI o comando reproducible con parametros chicos.
- Para modelos estocasticos, verificar estabilidad estadistica con seeds controladas y tolerancias razonables.
- Para `dt`, comparar contra `dt` menores y reportar el criterio usado.

## Resultados, Figuras y Presentacion

- La presentacion debe ser autocontenida y responder todos los puntos pedidos.
- Las figuras deben tener ejes con nombres, unidades cuando correspondan, tamanos legibles y puntos promedio claramente identificados.
- Usar barras de error o desvio estandar cuando se promedian realizaciones.
- Usar cifras significativas coherentes con el error.
- No interpolar con polinomios, splines ni funciones arbitrarias sin modelo teorico.
- Usar escala log o semilog si los datos varian en varios ordenes de magnitud.
- En PDF de entrega: usar un fotograma representativo y un link visible para cada animacion; no embeber ni adjuntar videos.
- En presentacion oral: las animaciones deben estar embebidas en la diapositiva correspondiente.
- Las conclusiones deben basarse solo en resultados mostrados.
- No incluir bibliografia formal en la presentacion; si hace falta, usar cita abreviada en la diapositiva.

## Higiene del Repo

- `docs/` contiene material fuente. No editarlo salvo pedido explicito.
- Mantener outputs, videos, caches, renders temporales y barridos grandes fuera de Git.
- Antes de generar resultados masivos, revisar o actualizar `.gitignore` con rutas como `outputs/`, `tmp/`, `runs/`, `*.mp4`, `*.avi`, `*.gif` y archivos de cache.
- Separar claramente:
  - motor de simulacion,
  - scripts de analisis,
  - scripts de animacion,
  - material de presentacion,
  - artefactos finales de entrega.
- No asumir lenguaje de programacion hasta que el usuario lo confirme. Si pide avanzar sin preferencia, elegir la opcion mas simple que mantenga el motor compacto y verificable.
- Usar `rg`/`rg --files` para busquedas.

## Cierre de Tareas

- Antes de decir que algo esta listo, ejecutar verificaciones relevantes y reportar las que no se pudieron correr.
- Resumen final esperado:
  - que se agrego/cambio,
  - que se verifico,
  - riesgos o supuestos restantes,
  - proximas acciones concretas.
