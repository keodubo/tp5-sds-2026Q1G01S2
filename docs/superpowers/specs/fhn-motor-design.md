# Spec: Motor Java para Sistema 2 - FitzHugh-Nagumo

## Alcance

Este spec define el motor de simulacion para el Sistema 2 del TP5: red de neuronas excitables con modelo FitzHugh-Nagumo.

El alcance de esta version es solo el motor. El analisis, las animaciones y la presentacion se haran despues, pero el motor debe producir outputs de texto suficientes para que esas etapas consuman resultados sin rerun innecesario.

Fuentes de referencia:

- `docs/TP5_Enunciado.pdf`
- `docs/Teoricas/Teorica5a.pdf`
- Indicacion del profesor: usar Runge-Kutta 4
- Decisiones tomadas con el usuario durante el armado del spec

## Clarifications

### Session 2026-05-22

- Q: ¿Permitimos que `Topology` mantenga la matriz `Aij` como fuente de verdad, pero ademas construya una estructura derivada de vecinos activos para calcular mas rapido el acoplamiento? -> A: Si. Matriz `Aij` como fuente de verdad y vecinos activos derivados para performance.
- Q: ¿Que `N` default usamos para produccion? -> A: `N = 501`, porque cumple `N > 500` y reduce costo computacional frente a `N = 600`.
- Q: ¿`activeNeighbors(i)` debe devolver copia defensiva o arreglo interno? -> A: Devuelve el arreglo interno; contrato: no mutarlo.
- Q: ¿Como manejar `T` no divisible por `dt`? -> A: Permitirlo y hacer un ultimo paso mas corto para terminar exactamente en `T`.
- Q: ¿Como manejar `saveInterval` no divisible por `dt`? -> A: Guardar en el primer tiempo simulado que cruza cada intervalo y guardar siempre `T` exacto.

## Objetivos

- Implementar un motor reproducible para FitzHugh-Nagumo en Java.
- Usar integracion numerica Runge-Kutta 4.
- Cubrir las tres topologias pedidas por el enunciado: completa, aleatoria y anillo.
- Generar outputs de texto livianos para barridos completos.
- Permitir outputs mas completos solo para corridas representativas.
- Mantener el codigo del motor compacto y facil de separar para la entrega final.

## Fuera de Alcance

- Analisis estadistico final.
- Figuras finales.
- Animaciones.
- Presentacion oral/PDF.
- Sistema 1 y Sistema 3.
- Normalizacion del acoplamiento.

## Modelo

Para cada neurona `i`:

```text
dv_i/dt = v_i - v_i^3 / 3 - w_i + I + K * sum_j Aij * (v_j - v_i)
dw_i/dt = epsilon * (v_i + a - b * w_i)
```

Parametros fijos del enunciado:

```text
I = 0.5
epsilon = 0.08
a = 0.7
b = 0.8
```

Condiciones iniciales:

```text
v_i(0) ~ U[-0.05, 0.05]
w_i(0) ~ U[-0.05, 0.05]
```

Observable principal:

```text
mean_v(t) = (1 / N) * sum_i v_i(t)
sigma_v(t) = sqrt((1 / N) * sum_i (v_i(t) - mean_v(t))^2)
```

Observable auxiliar:

```text
mean_w(t) = (1 / N) * sum_i w_i(t)
```

`mean_w` no es un resultado principal del enunciado; se guarda porque ocupa poco y ayuda a diagnosticar la dinamica lenta.

## Acoplamiento

El acoplamiento se implementa literal segun el enunciado:

```text
coupling_i = K * sum_j Aij * (v_j - v_i)
```

No se normaliza por grado ni por `N`.

Implicancia tecnica:

- En red completa, el termino escala con `N - 1`.
- En red aleatoria, escala aproximadamente con `p * (N - 1)`.
- En anillo, escala con `2k`.
- Por lo tanto, el mismo `K` no representa la misma intensidad total entre topologias.

Esto se acepta para mantenerse fiel al enunciado. La validacion de `dt` y `T` se hara despues de observar resultados de simulacion.

## Integrador

El motor usara Runge-Kutta 4 clasico con paso fijo.

Defaults:

```text
dt = 0.01
T = 100
```

Para los defaults de produccion, `T / dt` es entero. Si una corrida manual usa un `T` que no es multiplo exacto de `dt`, el motor debe avanzar con pasos `dt` y hacer solo el ultimo paso mas corto para terminar exactamente en `T`. Ese ultimo paso parcial debe registrarse en metadata como comportamiento de integracion.

No hay un `T` fijo impuesto por el enunciado. El objetivo es que, al analizar las curvas, se note si el sistema llega a estacionario. Si no se observa estacionario con `T = 100`, se repetiran casos con mayor `T`. Si el paso resulta demasiado grande, se contrastara contra corridas con menor `dt`.

## Parametros Default de Produccion

```text
N = 501
realizations = 15
baseSeed = 12345
saveInterval = 0.1
threads = 1
```

Grilla de `K`:

```text
K = 0.0, 0.1, 0.2, ..., 1.0
```

Grilla de `p` para red aleatoria:

```text
p = 0.0, 0.1, 0.2, ..., 1.0
```

Grilla de `k` para anillo:

```text
k = 1, 2, ..., 10
```

Cantidad estimada de corridas para barrido completo:

```text
complete: 11 K * 15 = 165
random:   11 p * 11 K * 15 = 1815
ring:     10 k * 11 K * 15 = 1650
total:    3630
```

## Topologias

La adyacencia se representara internamente como matriz `Aij`, para mantenerse lo mas cerca posible de la formulacion del enunciado.

La matriz `Aij` es la fuente de verdad del modelo. Para acelerar el calculo del acoplamiento, `Topology` puede construir una estructura derivada de vecinos activos a partir de esa matriz. Esa estructura no cambia la semantica: debe corresponder exactamente a los indices `j` para los cuales `Aij = 1`.

La matriz puede implementarse como `boolean[][]` o una estructura equivalente compacta, pero la abstraccion publica del motor debe exponer la matriz de adyacencia y permitir auditar los vecinos activos derivados.

Para evitar asignaciones masivas durante RK4, el acceso a vecinos activos puede devolver el arreglo interno. Ese arreglo es de solo lectura por contrato: el motor y los tests no deben mutarlo.

### Red Completa

```text
Aij = 1 para todo i != j
Aii = 0
```

### Red Aleatoria

Lectura literal del enunciado:

```text
Para todo i != j:
Aij = 1 con probabilidad p
Aii = 0
```

`Aij` y `Aji` se sortean independientemente. Por lo tanto, la red aleatoria es dirigida en la implementacion.

La topologia aleatoria se genera una vez al inicio de cada corrida y permanece fija durante toda la simulacion.

### Red Anillo

Anillo periodico:

```text
Aij = 1 si j pertenece a [i-k, ..., i-1, i+1, ..., i+k]
```

con indices periodicos y sin autoconexion.

Cada neurona tiene `2k` vecinos.

## Seeds y Reproducibilidad

Cada corrida tendra un `runSeed` derivado deterministicamente:

```text
runSeed = hash(baseSeed, topology, K, p_or_k, realizationIndex)
```

Ese `runSeed` controla:

- matriz aleatoria, si corresponde;
- condiciones iniciales de `v`;
- condiciones iniciales de `w`.

Cada corrida debe registrar en metadata:

- `baseSeed`
- `runSeed`
- topologia
- `N`
- `dt`
- `T`
- `K`
- `p` o `k`, si aplica
- indice de realizacion
- intervalo de guardado
- si se uso ultimo paso parcial
- flags de outputs opcionales

## CLI

El motor usara argumentos simples sin dependencias externas:

```text
<mode> --key value --flag
```

Modos:

- `smoke`: corrida chica para verificar compilacion y outputs.
- `single`: una corrida parametrizada.
- `sweep`: barrido de produccion.

### Comandos Esperados

Compilar y testear:

```bash
mvn test
```

Smoke test:

```bash
mvn exec:java -Dexec.args="smoke"
```

Corrida single completa:

```bash
mvn exec:java -Dexec.args="single --topology complete --K 0.5 --N 501 --dt 0.01 --T 100"
```

Corrida single aleatoria:

```bash
mvn exec:java -Dexec.args="single --topology random --K 0.5 --p 0.3 --N 501 --dt 0.01 --T 100"
```

Corrida single anillo:

```bash
mvn exec:java -Dexec.args="single --topology ring --K 0.5 --k 5 --N 501 --dt 0.01 --T 100"
```

Guardar estados completos para animacion o inspeccion:

```bash
mvn exec:java -Dexec.args="single --topology ring --K 0.5 --k 5 --save-states"
```

Barrido por topologia:

```bash
mvn exec:java -Dexec.args="sweep --topology complete --threads 4"
mvn exec:java -Dexec.args="sweep --topology random --threads 4"
mvn exec:java -Dexec.args="sweep --topology ring --threads 4"
```

Barrido completo explicito:

```bash
mvn exec:java -Dexec.args="sweep --topology all --threads 4"
```

### Reglas de CLI

- `single` requiere `--topology`.
- `sweep` requiere `--topology`.
- Valores validos de topologia: `complete`, `random`, `ring`, `all`.
- `all` solo es valido para `sweep`.
- `single --topology complete` requiere `--K`.
- `single --topology random` requiere `--K` y `--p`.
- `single --topology ring` requiere `--K` y `--k`.
- `--save-states` es opcional.
- `--save-adjacency` es opcional.
- `--overwrite` permite regenerar corridas existentes.
- `--threads` controla paralelismo en `sweep`; default `1`.

## Validacion de Parametros

Produccion usa validacion estricta:

- `N > 500`
- `0 <= K <= 1`
- `0 <= p <= 1`
- `1 <= k <= 10`
- `dt > 0`
- `T > 0`
- `saveInterval >= dt`
- `threads >= 1`

El modo `smoke` puede usar `N` chico de forma explicita para verificar rapidamente.

Los errores deben ser claros y terminar la ejecucion sin generar outputs parciales ambiguos.

## Outputs

El output base de cada corrida es:

```text
metadata.properties
observables.csv
```

Outputs opcionales:

```text
states.csv       # solo con --save-states
adjacency.csv    # solo con --save-adjacency
```

### Frecuencia de Guardado

Default:

```text
saveInterval = 0.1
```

Con `dt = 0.01` y `T = 100`, esto produce aproximadamente 1001 filas de observables por corrida.

Para los defaults de produccion, `saveInterval / dt` es entero y los tiempos guardados son exactos. Si una corrida manual usa un `saveInterval` que no es multiplo de `dt`, el motor debe guardar en el primer tiempo simulado `t >= n * saveInterval` para cada muestra esperada, y siempre debe guardar `t = 0` y `t = T` exacto.

No se guardan estados completos por default para mantener el barrido completo dentro de un tamano razonable. El objetivo aproximado es que la simulacion completa no supere 10 GB, y el esquema default deberia quedar muy por debajo de ese limite.

### `observables.csv`

Formato:

```csv
t,mean_v,sigma_v,mean_w
0.0,...
0.1,...
```

### `states.csv`

Solo si se pide `--save-states`.

Formato:

```csv
t,i,v,w
0.0,0,...
0.0,1,...
```

### `adjacency.csv`

Solo si se pide `--save-adjacency`.

Formato obligatorio:

```csv
i,j,Aij
0,1,1
0,2,0
```

El archivo debe incluir todos los pares `(i, j)` de la matriz, incluyendo ceros y diagonal, para que una corrida representativa pueda auditar la matriz completa. Este output sigue siendo opcional y no se usa por default en barridos completos.

## Estructura de Directorios de Output

```text
outputs/
  summary.csv
  sweep.log
  runs/
    complete/
      K_0.50/
        seed_0001/
          metadata.properties
          observables.csv
    random/
      p_0.30/
        K_0.50/
          seed_0001/
            metadata.properties
            observables.csv
    ring/
      k_05/
        K_0.50/
          seed_0001/
            metadata.properties
            observables.csv
```

Cada corrida vive en su propia carpeta para que los barridos sean resumibles.

## Barridos Resumibles

Por default, `sweep` saltea una corrida si ya existen:

- `metadata.properties`
- `observables.csv`

Una corrida se considera completa solo si `metadata.properties` existe y `observables.csv` existe, tiene header `t,mean_v,sigma_v,mean_w`, tiene al menos una fila de datos, y su ultima fila corresponde a `t = T` dentro de tolerancia numerica.

Para regenerar:

```bash
--overwrite
```

El sweep debe registrar progreso por consola:

```text
[123/1815] random p=0.30 K=0.50 rep=7 START
[123/1815] random p=0.30 K=0.50 rep=7 OK elapsed=2.4s
[124/1815] random p=0.30 K=0.50 rep=8 SKIP existing
```

Tambien debe escribir:

```text
outputs/sweep.log
outputs/summary.csv
```

`summary.csv` debe incluir al menos:

```csv
topology,K,p,k,realization,baseSeed,runSeed,outputDir,status
```

## Estructura de Codigo

Diseno modular pero compacto:

```text
Main
Config
Topology
FhnSimulation
OutputWriter
```

Responsabilidades:

- `Main`: parseo CLI, seleccion de modo, ejecucion.
- `Config`: parametros, defaults y validacion.
- `Topology`: construccion de matriz `Aij` y vecinos activos derivados.
- `FhnSimulation`: estado, RK4, calculo de derivadas y observables.
- `OutputWriter`: metadata, observables, estados opcionales, resumen/log.

El motor no debe depender de librerias externas. Solo Java estandar.

Maven se usa para build y tests. JUnit queda permitido solo para tests y no forma parte del codigo del motor entregable.

## Tests Minimos

Los tests deben ser unit-level, blackbox y behavior-only. No se busca cobertura artificial.

Set minimo:

- `smoke` genera `metadata.properties` y `observables.csv`.
- Misma seed y mismos parametros generan el mismo `observables.csv`.
- Parametros invalidos fallan con error claro.
- `--save-states` genera `states.csv` con cantidad esperada de filas para `N` chico.
- Topologias correctas en casos chicos mediante contrato publico:
  - completa sin diagonal;
  - anillo periodico;
  - aleatoria reproducible con seed fija.

No testear:

- metodos privados;
- orden interno exacto de llamadas;
- strings internos no publicos;
- detalles de implementacion del parser;
- estructura privada de clases.

## Entrega Final

El repo de trabajo puede tener:

- Maven;
- tests;
- specs;
- scripts auxiliares futuros;
- outputs locales ignorados por Git.

La entrega oficial del codigo debe contener solo fuente del motor de simulacion, sin:

- outputs;
- documentos;
- specs;
- tests;
- `target/`;
- caches;
- figuras;
- animaciones.

Nombre oficial segun enunciado para el grupo:

```text
SdS_TP5_2026Q1G01CS2_Codigo
```

Antes de entregar:

- verificar que el paquete contiene solo codigo fuente del motor;
- verificar tamano objetivo menor a 20 kB si el criterio se aplica estrictamente;
- verificar que el motor genera archivos de texto;
- verificar que analisis y animacion pueden ejecutarse luego consumiendo esos textos.

## Riesgos y Decisiones Abiertas

- `dt = 0.01` y `T = 100` son defaults iniciales. Se deben contrastar con datos simulados para confirmar que se observa estacionario y que el paso es adecuado.
- El acoplamiento literal puede producir dinamicas muy fuertes en redes densas. Esto es intencional para seguir el enunciado, pero puede exigir menor `dt`.
- Aunque `N = 501` reduce costo frente a valores mayores, red completa y aleatoria densa siguen siendo caras. Por eso se permite usar vecinos activos derivados de `Aij` para calcular el acoplamiento sin cambiar el modelo.
- La red aleatoria se implementa dirigida porque el enunciado define `Aij` independiente y el usuario pidio no imponer simetria.
- `adjacency.csv` queda opcional para no aumentar el peso de outputs.

## Criterio de Aceptacion del Motor

El motor se considera listo para pasar a la etapa de simulaciones exploratorias cuando:

- `mvn test` pasa.
- `smoke` genera outputs validos.
- `single` funciona para completa, aleatoria y anillo.
- `sweep --topology complete` puede correr o resumir sin pisar resultados.
- los outputs contienen metadata suficiente para reproducir corridas.
- el esquema default de outputs es liviano y no guarda estados completos salvo pedido explicito.
