# Spec: Animaciones Python para Sistema 2 - FitzHugh-Nagumo

## Alcance

Este spec define un modulo Python independiente para generar animaciones del Sistema 2 del TP5 a partir de outputs de texto ya producidos por el motor Java.

El modulo no debe ejecutar ni modificar la simulacion. Su unica responsabilidad es consumir una carpeta de corrida existente y producir videos/fotogramas para inspeccion, presentacion oral y preparacion del PDF final.

Fuentes de referencia:

- `AGENTS.md`
- `docs/superpowers/specs/fhn-motor-design.md`
- Outputs actuales del motor: `metadata.properties`, `observables.csv`, `states.csv`, `adjacency.csv`
- Decisiones tomadas con el usuario durante el armado de este spec

## Decisiones Confirmadas

- El modulo se implementara en Python.
- La visualizacion principal incluira:
  - red animada;
  - dashboard animado con series y snapshot.
- La red animada debe usar NetworkX + Matplotlib.
- La red debe dibujar todos los enlaces presentes en `adjacency.csv`.
- La direccion de enlaces debe ser configurable:
  - default: lineas sin flecha;
  - opcion: flechas dirigidas.
- Por cada corrida se generaran MP4 y PNG representativos.
- El nombre del archivo de spec no debe incluir fecha.

## Objetivos

- Generar animaciones reproducibles desde archivos de texto existentes.
- Mantener separadas simulacion, analisis y animacion.
- Permitir revisar visualmente sincronizacion/desincronizacion en una corrida.
- Producir artefactos utilizables en slides y como fotogramas para el PDF final.
- Fallar temprano con mensajes claros si la corrida no contiene los archivos necesarios.

## Fuera de Alcance

- Reejecutar simulaciones.
- Modificar el motor Java.
- Generar barridos estadisticos.
- Calcular conclusiones finales.
- Subir videos a YouTube, Vimeo o similar.
- Crear la presentacion final.
- Implementar Sistema 1 o Sistema 3.

## Ubicacion y Entrypoint

Archivo principal:

```text
scripts/animate_fhn.py
```

Comando base:

```bash
python scripts/animate_fhn.py --run-dir outputs/runs/ring/k_05/K_0.50/seed_0001
```

El script debe ser ejecutable desde la raiz del repo.

## Dependencias

Dependencias de runtime:

```text
python >= 3.11
matplotlib
networkx
numpy
```

Backend de video:

```text
ffmpeg
```

No se requiere `pandas` para v1. La lectura de CSV puede implementarse con `csv` de la biblioteca estandar y arrays de `numpy`.

## Inputs

### Carpeta de Corrida

`--run-dir` debe apuntar a una carpeta con estructura compatible con el motor:

```text
<run-dir>/
  metadata.properties
  observables.csv
  states.csv
  adjacency.csv
```

### `metadata.properties`

Se usa para:

- topologia;
- `N`;
- `K`;
- `p` o `k`, si aplica;
- `dt`;
- `T`;
- `saveInterval`;
- seed;
- flags de outputs.

### `observables.csv`

Formato esperado:

```csv
t,mean_v,sigma_v,mean_w
```

Se usa para el dashboard.

### `states.csv`

Formato esperado:

```csv
t,i,v,w
```

Se usa para:

- color de nodos en la red animada;
- snapshot `v_i(t)` del dashboard.

Si falta, el script debe fallar para ambas animaciones con un mensaje que indique regenerar la corrida con `--save-states`.

### `adjacency.csv`

Formato esperado:

```csv
i,j,Aij
```

Se usa para construir el grafo NetworkX.

Si falta:

- `network.mp4` no puede generarse;
- `dashboard.mp4` si puede generarse, porque solo depende de `observables.csv` y `states.csv`.

El script debe ofrecer un flag para generar solo dashboard:

```bash
--only dashboard
```

## Outputs

Por default, el script escribe en:

```text
renders/
  <run-id>/
    network.mp4
    network_frame.png
    dashboard.mp4
    dashboard_frame.png
```

`<run-id>` debe derivarse de la metadata y/o path de corrida de forma estable:

```text
<topology>_<params>_seed_<realization>
```

Ejemplos:

```text
complete_K_0.20_seed_0001
random_p_0.30_K_0.20_seed_0001
ring_k_02_K_0.20_seed_0001
```

El output dir debe ser configurable:

```bash
--output-dir renders
```

## CLI

Comando completo esperado:

```bash
python scripts/animate_fhn.py \
  --run-dir outputs/runs/ring/k_05/K_0.50/seed_0001 \
  --output-dir renders \
  --fps 24 \
  --dpi 140 \
  --frame-stride 1
```

Flags:

```text
--run-dir PATH              requerido
--output-dir PATH           default: renders
--only network|dashboard|all default: all
--fps INT                   default: 24
--dpi INT                   default: 140
--frame-stride INT          default: 1
--representative-time FLOAT opcional; si no se pasa, usar T/2
--directed-edges            default: false
--layout circular|spring    default: circular
--edge-alpha FLOAT          default: 0.08 para redes densas, 0.20 para redes no densas
--edge-width FLOAT          default: 0.25
--node-size FLOAT           default: 18
--colormap NAME             default: coolwarm
--overwrite                 default: false
```

Reglas:

- `--frame-stride` permite saltear muestras de `states.csv` para acelerar renders.
- `--representative-time` elige el fotograma PNG mas cercano al tiempo indicado.
- Si los outputs ya existen y no se pasa `--overwrite`, el script debe saltear o fallar con mensaje claro. Default recomendado: saltear con `SKIP existing`.
- `--layout spring` debe advertir que puede ser lento con `N > 200`.

## Construccion del Grafo

NetworkX debe construirse desde todos los registros `Aij = 1` de `adjacency.csv`.

Regla base:

- usar `nx.DiGraph` como estructura interna para preservar la direccion de `Aij`;
- agregar todos los nodos `0..N-1`;
- agregar todos los edges `(i, j)` con `Aij = 1`;
- no deduplicar pares reciprocos.

Render default:

- dibujar todos los edges del `DiGraph`;
- `arrows=False`;
- los pares reciprocos pueden superponerse visualmente, pero siguen estando en el grafo.

Render dirigido:

- si se pasa `--directed-edges`, dibujar con flechas;
- usar flechas chicas y alpha bajo;
- advertir en consola cuando `edge_count` sea alto porque la direccion puede quedar ilegible.

## Layout

Default:

```text
circular
```

Justificacion:

- determinista;
- rapido para `N=501`;
- comparable entre topologias;
- suficiente para mostrar propagacion/sincronizacion por color.

`spring`:

- opcional;
- usar seed fija derivada de `runSeed`;
- recomendado solo para corridas chicas o redes esparsas;
- debe advertir si `N > 200` o `edge_count > 20000`.

## Red Animada

Archivo:

```text
network.mp4
network_frame.png
```

Contenido:

- nodos `0..N-1`;
- todos los enlaces de `adjacency.csv`;
- color de cada nodo segun `v_i(t)`;
- titulo con topologia, parametros, seed y tiempo actual;
- barra de color con etiqueta `v_i(t)`.

Escala de color:

- calcular `vmin` y `vmax` globales desde `states.csv` para evitar que la escala cambie entre frames;
- si `vmin == vmax`, expandir levemente el rango para evitar errores de Matplotlib.

Performance:

- calcular layout una sola vez;
- construir colecciones de edges/nodos una sola vez;
- actualizar solo los colores de nodos por frame;
- no recalcular NetworkX por frame.

Advertencias:

- red completa con `N=501` contiene hasta `501 * 500 = 250500` enlaces dirigidos;
- dibujar todos los enlaces puede ser lento y visualmente saturado;
- el script debe imprimir `N`, `edge_count`, cantidad de frames y ruta de output antes de renderizar.

## Dashboard Animado

Archivo:

```text
dashboard.mp4
dashboard_frame.png
```

Contenido minimo:

1. Curva `<v(t)>` completa con marcador vertical del tiempo actual.
2. Curva `sigma_v(t)` completa con marcador vertical del tiempo actual.
3. Snapshot `v_i(t)` por indice `i`, como scatter o linea.

Reglas visuales:

- ejes con nombres claros;
- titulo con topologia, parametros y seed;
- misma escala temporal que `observables.csv`;
- snapshot con eje x `i` y eje y `v_i(t)`;
- marcador del tiempo actual sincronizado con el frame de red.

El dashboard no requiere `adjacency.csv`.

## Sincronizacion de Frames

La fuente de frames debe ser `states.csv`.

Para cada tiempo de `states.csv` seleccionado por `frame_stride`:

- la red usa `v_i(t)` para colorear nodos;
- el dashboard marca el mismo `t`;
- si `observables.csv` no contiene exactamente ese `t`, usar la fila de observable mas cercana.

El script debe validar:

- todos los tiempos de `states.csv` tienen exactamente `N` filas;
- todos los indices `i` estan en `[0, N-1]`;
- los tiempos estan ordenados o se pueden ordenar sin perder datos;
- hay al menos dos tiempos para producir MP4.

## Manejo de Errores

Errores fatales:

- falta `--run-dir`;
- `metadata.properties` inexistente o invalido;
- `observables.csv` inexistente o con header incorrecto;
- `states.csv` inexistente cuando se pide `network` o `dashboard`;
- `states.csv` incompleto para algun tiempo;
- `adjacency.csv` inexistente cuando se pide `network`;
- `ffmpeg` no disponible al exportar MP4.

Errores recuperables:

- `adjacency.csv` falta y `--only all`: generar dashboard, reportar que network fue omitido;
- outputs existentes sin `--overwrite`: saltear y reportar `SKIP existing`;
- `--layout spring` en grafo grande: advertir y permitir continuar.

Los mensajes deben incluir el path afectado y el comando de regeneracion cuando aplique.

Ejemplo para `states.csv` faltante:

```text
ERROR: states.csv not found in <run-dir>. Regenerate the simulation with --save-states.
```

## Smoke Manual Esperado

Generar una corrida minima desde el motor:

```bash
mvn -q -DskipTests exec:java \
  -Dexec.args="single --topology ring --N 501 --K 0.2 --k 2 --dt 0.02 --T 0.2 --save-interval 0.02 --output-dir /tmp/tp5-fhn-animation-smoke --save-states --save-adjacency --overwrite"
```

Renderizar:

```bash
python scripts/animate_fhn.py \
  --run-dir /tmp/tp5-fhn-animation-smoke/runs/ring/k_02/K_0.20/seed_0001 \
  --output-dir /tmp/tp5-fhn-animation-renders \
  --fps 12 \
  --dpi 100 \
  --overwrite
```

Resultado esperado:

```text
/tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/network.mp4
/tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/network_frame.png
/tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/dashboard.mp4
/tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/dashboard_frame.png
```

## Tests

Los tests que se agreguen deben ser unit-level, blackbox y behavior-only.

Set minimo:

- parser de `metadata.properties` devuelve valores esperados;
- parser de `observables.csv` rechaza header invalido;
- parser de `states.csv` rechaza tiempos incompletos;
- parser de `adjacency.csv` construye un grafo con todos los edges `Aij=1`;
- CLI falla con mensaje claro si falta `states.csv`;
- CLI con corrida minima genera los cuatro artefactos esperados usando un dataset chico.

No testear:

- metodos privados;
- detalles internos de Matplotlib;
- orden exacto de llamadas a NetworkX;
- pixeles exactos del video;
- strings internos que no sean mensajes publicos de error.

Para evitar tests lentos, los tests de render deben usar un dataset chico, pocos frames y output temporal.

## Criterios de Aceptacion

- El script puede generar dashboard sin `adjacency.csv`.
- El script puede generar red animada cuando existen `states.csv` y `adjacency.csv`.
- La red usa todos los enlaces `Aij=1`.
- La direccion de enlaces es configurable con `--directed-edges`.
- Los MP4 y PNG se escriben en una carpeta `renders/<run-id>/` o en `--output-dir`.
- El render no modifica outputs de simulacion.
- Los errores comunes indican que archivo falta y como regenerarlo.
- Existe al menos un smoke reproducible con una corrida chica.

## Riesgos y Trade-offs

- Dibujar todos los enlaces de red completa para `N=501` puede ser lento y poco legible.
- Las flechas dirigidas en grafos densos pueden saturar la visualizacion.
- `spring_layout` puede ser caro para grafos grandes.
- MP4 requiere `ffmpeg`; si no esta instalado, la generacion de video falla aunque el parsing sea correcto.

Decision: aceptar estos riesgos porque el usuario priorizo fidelidad visual de todos los enlaces y configurabilidad de direccion.

## Rollback

Como el modulo es independiente del motor, el rollback es simple:

- eliminar o revertir `scripts/animate_fhn.py`;
- eliminar o revertir tests Python asociados;
- borrar renders generados en `renders/` o `/tmp`.

No hay migraciones ni cambios de formato del motor.
