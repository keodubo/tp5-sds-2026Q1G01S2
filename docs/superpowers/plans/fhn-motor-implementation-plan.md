# FHN Motor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Java/Maven simulation motor for TP5 Sistema 2, FitzHugh-Nagumo, following `docs/superpowers/specs/fhn-motor-design.md`.

**Architecture:** A compact Java 21 CLI motor with five focused production classes: `Main`, `Config`, `Topology`, `FhnSimulation`, and `OutputWriter`. The motor uses fixed-step RK4, an internal adjacency matrix `Aij`, reproducible seeds, resumable output directories, and lightweight CSV/properties outputs.

**Tech Stack:** Java 21, Maven 3, JUnit Jupiter for tests only, Java standard library for production code.

---

## Source References

- Repo rules: `AGENTS.md`
- Design spec: `docs/superpowers/specs/fhn-motor-design.md`
- Official statement: `docs/TP5_Enunciado.pdf`
- Theory support: `docs/Teoricas/Teorica5a.pdf`

## File Map

Create:

- `pom.xml`: Java 21 Maven config, JUnit tests, exec plugin entrypoint.
- `src/main/java/ar/edu/itba/sds/tp5/Main.java`: CLI entrypoint and mode dispatch.
- `src/main/java/ar/edu/itba/sds/tp5/Config.java`: defaults, parsing, validation, seed derivation, run path naming.
- `src/main/java/ar/edu/itba/sds/tp5/Topology.java`: adjacency matrix constructors and public edge contract.
- `src/main/java/ar/edu/itba/sds/tp5/FhnSimulation.java`: RK4, state initialization, observables, optional state snapshots.
- `src/main/java/ar/edu/itba/sds/tp5/OutputWriter.java`: metadata, observables, states, adjacency, sweep log, summary.
- `src/test/java/ar/edu/itba/sds/tp5/TopologyTest.java`: topology contracts.
- `src/test/java/ar/edu/itba/sds/tp5/FhnSimulationTest.java`: determinism and observable contract.
- `src/test/java/ar/edu/itba/sds/tp5/MainCliTest.java`: smoke/single CLI outputs and validation.
- `src/test/java/ar/edu/itba/sds/tp5/SweepTest.java`: resumable sweep behavior on tiny runs.

Modify:

- `.gitignore`: ignore `target/`, `outputs/`, temporary runs, video/render artifacts, and caches.

Public production API intended for tests:

```java
package ar.edu.itba.sds.tp5;

public final class Main {
    public static void main(String[] args) throws Exception;
    public static int run(String[] args) throws Exception;
}

public record Config(
    String mode,
    String topology,
    int n,
    double kValue,
    double pValue,
    int ringK,
    double dt,
    double totalTime,
    double saveInterval,
    int realizations,
    long baseSeed,
    int realizationIndex,
    int threads,
    boolean saveStates,
    boolean saveAdjacency,
    boolean overwrite,
    java.nio.file.Path outputDir
) {
    public static Config parse(String[] args);
    public long runSeed();
    public java.nio.file.Path runDirectory();
}

public final class Topology {
    public enum Type { COMPLETE, RANDOM, RING }
    public static Topology complete(int n);
    public static Topology random(int n, double p, long seed);
    public static Topology ring(int n, int k);
    public int size();
    public boolean edge(int i, int j);
    public boolean[][] adjacency();
}

public final class FhnSimulation {
    public record Observable(double t, double meanV, double sigmaV, double meanW) {}
    public record StateRow(double t, int i, double v, double w) {}
    public record Result(java.util.List<Observable> observables, java.util.List<StateRow> states) {}
    public static Result run(Config config, Topology topology);
}

public final class OutputWriter {
    public static void writeRun(Config config, Topology topology, FhnSimulation.Result result) throws java.io.IOException;
}
```

The signatures can be extended during implementation only if the tests and CLI contract remain simple and public.

---

### Task 1: Maven Scaffold and Git Hygiene

**Files:**

- Create: `pom.xml`
- Modify: `.gitignore`

- [ ] **Step 1: Extend `.gitignore` before any generated artifacts exist**

Set `.gitignore` to:

```gitignore
.DS_Store
target/
outputs/
tmp/
runs/
*.mp4
*.avi
*.gif
*.mov
*.log
*.class
```

- [ ] **Step 2: Add Maven project file**

Create `pom.xml`:

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <groupId>ar.edu.itba.sds</groupId>
  <artifactId>tp5-fhn-motor</artifactId>
  <version>1.0.0</version>

  <properties>
    <maven.compiler.release>21</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <junit.jupiter.version>5.10.3</junit.jupiter.version>
  </properties>

  <dependencies>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>${junit.jupiter.version}</version>
      <scope>test</scope>
    </dependency>
  </dependencies>

  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.2.5</version>
        <configuration>
          <useModulePath>false</useModulePath>
        </configuration>
      </plugin>
      <plugin>
        <groupId>org.codehaus.mojo</groupId>
        <artifactId>exec-maven-plugin</artifactId>
        <version>3.3.0</version>
        <configuration>
          <mainClass>ar.edu.itba.sds.tp5.Main</mainClass>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
```

- [ ] **Step 3: Run Maven test lifecycle before code exists**

Run:

```bash
mvn test
```

Expected: build succeeds with no tests, or Maven reports no sources/tests and exits successfully.

- [ ] **Step 4: Commit scaffold**

```bash
git add .gitignore pom.xml
git commit -m "chore: scaffold Java motor project"
```

---

### Task 2: Config Parsing and Validation

**Files:**

- Create: `src/main/java/ar/edu/itba/sds/tp5/Config.java`
- Create: `src/test/java/ar/edu/itba/sds/tp5/MainCliTest.java`

- [ ] **Step 1: Write failing validation tests**

Create `src/test/java/ar/edu/itba/sds/tp5/MainCliTest.java`:

```java
package ar.edu.itba.sds.tp5;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

final class MainCliTest {
    @TempDir
    Path tempDir;

    @Test
    void singleRequiresTopology() {
        IllegalArgumentException ex = assertThrows(
            IllegalArgumentException.class,
            () -> Config.parse(new String[] {"single", "--K", "0.5", "--output-dir", tempDir.toString()})
        );
        assertEquals("single requires --topology", ex.getMessage());
    }

    @Test
    void productionRejectsNAtOrBelowFiveHundred() {
        IllegalArgumentException ex = assertThrows(
            IllegalArgumentException.class,
            () -> Config.parse(new String[] {
                "single", "--topology", "complete", "--K", "0.5", "--N", "500",
                "--output-dir", tempDir.toString()
            })
        );
        assertEquals("N must be greater than 500 for production modes", ex.getMessage());
    }

    @Test
    void smokeAllowsSmallN() {
        Config config = Config.parse(new String[] {"smoke", "--output-dir", tempDir.toString()});
        assertEquals("smoke", config.mode());
        assertEquals(12, config.n());
    }
}
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
mvn test -Dtest=MainCliTest
```

Expected: compilation fails because `Config` does not exist.

- [ ] **Step 3: Implement `Config`**

Create `src/main/java/ar/edu/itba/sds/tp5/Config.java`:

```java
package ar.edu.itba.sds.tp5;

import java.nio.file.Path;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;

public record Config(
    String mode,
    String topology,
    int n,
    double kValue,
    double pValue,
    int ringK,
    double dt,
    double totalTime,
    double saveInterval,
    int realizations,
    long baseSeed,
    int realizationIndex,
    int threads,
    boolean saveStates,
    boolean saveAdjacency,
    boolean overwrite,
    Path outputDir
) {
    public static Config parse(String[] args) {
        if (args.length == 0) {
            throw new IllegalArgumentException("mode is required");
        }

        String mode = args[0].toLowerCase(Locale.ROOT);
        Map<String, String> values = new HashMap<>();
        boolean saveStates = false;
        boolean saveAdjacency = false;
        boolean overwrite = false;

        for (int i = 1; i < args.length; i++) {
            String arg = args[i];
            if ("--save-states".equals(arg)) {
                saveStates = true;
            } else if ("--save-adjacency".equals(arg)) {
                saveAdjacency = true;
            } else if ("--overwrite".equals(arg)) {
                overwrite = true;
            } else if (arg.startsWith("--")) {
                if (i + 1 >= args.length || args[i + 1].startsWith("--")) {
                    throw new IllegalArgumentException(arg + " requires a value");
                }
                values.put(arg.substring(2), args[++i]);
            } else {
                throw new IllegalArgumentException("unexpected argument: " + arg);
            }
        }

        String topology = values.get("topology");
        int n = intValue(values, "N", "smoke".equals(mode) ? 12 : 600);
        double kValue = doubleValue(values, "K", Double.NaN);
        double pValue = doubleValue(values, "p", Double.NaN);
        int ringK = intValue(values, "k", -1);
        double dt = doubleValue(values, "dt", "smoke".equals(mode) ? 0.02 : 0.01);
        double totalTime = doubleValue(values, "T", "smoke".equals(mode) ? 0.2 : 100.0);
        double saveInterval = doubleValue(values, "save-interval", "smoke".equals(mode) ? 0.1 : 0.1);
        int realizations = intValue(values, "realizations", 15);
        long baseSeed = longValue(values, "base-seed", 12345L);
        int realizationIndex = intValue(values, "realization", 1);
        int threads = intValue(values, "threads", 1);
        Path outputDir = Path.of(values.getOrDefault("output-dir", "outputs"));

        Config config = new Config(
            mode, topology, n, kValue, pValue, ringK, dt, totalTime, saveInterval,
            realizations, baseSeed, realizationIndex, threads, saveStates,
            saveAdjacency, overwrite, outputDir
        );
        config.validate();
        return config;
    }

    private void validate() {
        if (!mode.equals("smoke") && !mode.equals("single") && !mode.equals("sweep")) {
            throw new IllegalArgumentException("mode must be smoke, single, or sweep");
        }
        if (mode.equals("single") && topology == null) {
            throw new IllegalArgumentException("single requires --topology");
        }
        if (mode.equals("sweep") && topology == null) {
            throw new IllegalArgumentException("sweep requires --topology");
        }
        if (topology != null && !topology.equals("complete") && !topology.equals("random")
            && !topology.equals("ring") && !topology.equals("all")) {
            throw new IllegalArgumentException("--topology must be complete, random, ring, or all");
        }
        if (mode.equals("single") && "all".equals(topology)) {
            throw new IllegalArgumentException("all is only valid for sweep");
        }
        if (!mode.equals("smoke") && n <= 500) {
            throw new IllegalArgumentException("N must be greater than 500 for production modes");
        }
        if (n <= 0) {
            throw new IllegalArgumentException("N must be positive");
        }
        if (requiresK() && (Double.isNaN(kValue) || kValue < 0.0 || kValue > 1.0)) {
            throw new IllegalArgumentException("K must be in [0, 1]");
        }
        if ("random".equals(topology) && (Double.isNaN(pValue) || pValue < 0.0 || pValue > 1.0)) {
            throw new IllegalArgumentException("p must be in [0, 1]");
        }
        if ("ring".equals(topology) && (ringK < 1 || ringK > 10)) {
            throw new IllegalArgumentException("k must be in [1, 10]");
        }
        if (dt <= 0.0) {
            throw new IllegalArgumentException("dt must be positive");
        }
        if (totalTime <= 0.0) {
            throw new IllegalArgumentException("T must be positive");
        }
        if (saveInterval < dt) {
            throw new IllegalArgumentException("save-interval must be greater than or equal to dt");
        }
        if (realizations < 1) {
            throw new IllegalArgumentException("realizations must be positive");
        }
        if (realizationIndex < 1) {
            throw new IllegalArgumentException("realization must be positive");
        }
        if (threads < 1) {
            throw new IllegalArgumentException("threads must be positive");
        }
        Objects.requireNonNull(outputDir, "outputDir");
    }

    private boolean requiresK() {
        return mode.equals("single") && ("complete".equals(topology) || "random".equals(topology) || "ring".equals(topology));
    }

    public long runSeed() {
        long hash = 1125899906842597L;
        hash = 31 * hash + baseSeed;
        hash = 31 * hash + Objects.hashCode(topology);
        hash = 31 * hash + Double.doubleToLongBits(kValue);
        hash = 31 * hash + Double.doubleToLongBits(pValue);
        hash = 31 * hash + ringK;
        hash = 31 * hash + realizationIndex;
        return hash;
    }

    public Path runDirectory() {
        String seedPart = String.format(Locale.ROOT, "seed_%04d", realizationIndex);
        if ("complete".equals(topology)) {
            return outputDir.resolve("runs").resolve("complete").resolve(kDir()).resolve(seedPart);
        }
        if ("random".equals(topology)) {
            return outputDir.resolve("runs").resolve("random").resolve(pDir()).resolve(kDir()).resolve(seedPart);
        }
        if ("ring".equals(topology)) {
            return outputDir.resolve("runs").resolve("ring").resolve(ringDir()).resolve(kDir()).resolve(seedPart);
        }
        return outputDir.resolve("runs").resolve(mode).resolve(seedPart);
    }

    private String kDir() {
        return String.format(Locale.ROOT, "K_%.2f", kValue);
    }

    private String pDir() {
        return String.format(Locale.ROOT, "p_%.2f", pValue);
    }

    private String ringDir() {
        return String.format(Locale.ROOT, "k_%02d", ringK);
    }

    public Config withSweepValues(String newTopology, double newK, double newP, int newRingK, int newRealization) {
        return new Config(
            mode, newTopology, n, newK, newP, newRingK, dt, totalTime, saveInterval,
            realizations, baseSeed, newRealization, threads, saveStates, saveAdjacency,
            overwrite, outputDir
        );
    }

    private static int intValue(Map<String, String> values, String key, int defaultValue) {
        return values.containsKey(key) ? Integer.parseInt(values.get(key)) : defaultValue;
    }

    private static long longValue(Map<String, String> values, String key, long defaultValue) {
        return values.containsKey(key) ? Long.parseLong(values.get(key)) : defaultValue;
    }

    private static double doubleValue(Map<String, String> values, String key, double defaultValue) {
        return values.containsKey(key) ? Double.parseDouble(values.get(key)) : defaultValue;
    }
}
```

- [ ] **Step 4: Run validation tests**

Run:

```bash
mvn test -Dtest=MainCliTest
```

Expected: all tests in `MainCliTest` pass.

- [ ] **Step 5: Commit config parsing**

```bash
git add src/main/java/ar/edu/itba/sds/tp5/Config.java src/test/java/ar/edu/itba/sds/tp5/MainCliTest.java
git commit -m "feat: add motor CLI configuration"
```

---

### Task 3: Topology Matrix

**Files:**

- Create: `src/main/java/ar/edu/itba/sds/tp5/Topology.java`
- Create: `src/test/java/ar/edu/itba/sds/tp5/TopologyTest.java`

- [ ] **Step 1: Write topology contract tests**

Create `src/test/java/ar/edu/itba/sds/tp5/TopologyTest.java`:

```java
package ar.edu.itba.sds.tp5;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class TopologyTest {
    @Test
    void completeHasAllEdgesExceptDiagonal() {
        Topology topology = Topology.complete(4);

        assertFalse(topology.edge(0, 0));
        assertTrue(topology.edge(0, 1));
        assertTrue(topology.edge(0, 2));
        assertTrue(topology.edge(0, 3));
        assertTrue(topology.edge(3, 0));
    }

    @Test
    void ringUsesPeriodicTwoKNeighborhood() {
        Topology topology = Topology.ring(6, 2);

        assertFalse(topology.edge(0, 0));
        assertTrue(topology.edge(0, 1));
        assertTrue(topology.edge(0, 2));
        assertTrue(topology.edge(0, 4));
        assertTrue(topology.edge(0, 5));
        assertFalse(topology.edge(0, 3));
    }

    @Test
    void randomIsReproducibleWithSeed() {
        boolean[][] first = Topology.random(8, 0.35, 99L).adjacency();
        boolean[][] second = Topology.random(8, 0.35, 99L).adjacency();

        assertArrayEquals(first, second);
    }

    @Test
    void randomDoesNotForceSymmetry() {
        Topology topology = Topology.random(20, 0.5, 12345L);
        boolean foundAsymmetry = false;
        for (int i = 0; i < topology.size(); i++) {
            for (int j = 0; j < topology.size(); j++) {
                if (i != j && topology.edge(i, j) != topology.edge(j, i)) {
                    foundAsymmetry = true;
                }
            }
        }
        assertTrue(foundAsymmetry);
    }
}
```

- [ ] **Step 2: Run failing topology tests**

Run:

```bash
mvn test -Dtest=TopologyTest
```

Expected: compilation fails because `Topology` does not exist.

- [ ] **Step 3: Implement topology matrix**

Create `src/main/java/ar/edu/itba/sds/tp5/Topology.java`:

```java
package ar.edu.itba.sds.tp5;

import java.util.Random;

public final class Topology {
    public enum Type { COMPLETE, RANDOM, RING }

    private final Type type;
    private final boolean[][] adjacency;

    private Topology(Type type, boolean[][] adjacency) {
        this.type = type;
        this.adjacency = adjacency;
    }

    public static Topology complete(int n) {
        boolean[][] adjacency = new boolean[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                adjacency[i][j] = i != j;
            }
        }
        return new Topology(Type.COMPLETE, adjacency);
    }

    public static Topology random(int n, double p, long seed) {
        boolean[][] adjacency = new boolean[n][n];
        Random random = new Random(seed);
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                adjacency[i][j] = i != j && random.nextDouble() < p;
            }
        }
        return new Topology(Type.RANDOM, adjacency);
    }

    public static Topology ring(int n, int k) {
        boolean[][] adjacency = new boolean[n][n];
        for (int i = 0; i < n; i++) {
            for (int offset = 1; offset <= k; offset++) {
                adjacency[i][Math.floorMod(i - offset, n)] = true;
                adjacency[i][Math.floorMod(i + offset, n)] = true;
            }
            adjacency[i][i] = false;
        }
        return new Topology(Type.RING, adjacency);
    }

    public Type type() {
        return type;
    }

    public int size() {
        return adjacency.length;
    }

    public boolean edge(int i, int j) {
        return adjacency[i][j];
    }

    public boolean[][] adjacency() {
        boolean[][] copy = new boolean[adjacency.length][adjacency.length];
        for (int i = 0; i < adjacency.length; i++) {
            System.arraycopy(adjacency[i], 0, copy[i], 0, adjacency.length);
        }
        return copy;
    }
}
```

- [ ] **Step 4: Run topology tests**

Run:

```bash
mvn test -Dtest=TopologyTest
```

Expected: all topology tests pass.

- [ ] **Step 5: Commit topology**

```bash
git add src/main/java/ar/edu/itba/sds/tp5/Topology.java src/test/java/ar/edu/itba/sds/tp5/TopologyTest.java
git commit -m "feat: add adjacency matrix topologies"
```

---

### Task 4: RK4 FHN Simulation Core

**Files:**

- Create: `src/main/java/ar/edu/itba/sds/tp5/FhnSimulation.java`
- Create: `src/test/java/ar/edu/itba/sds/tp5/FhnSimulationTest.java`

- [ ] **Step 1: Write simulation behavior tests**

Create `src/test/java/ar/edu/itba/sds/tp5/FhnSimulationTest.java`:

```java
package ar.edu.itba.sds.tp5;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

final class FhnSimulationTest {
    @TempDir
    Path tempDir;

    @Test
    void simulationIsDeterministicForSameSeedAndParameters() {
        Config config = Config.parse(new String[] {
            "smoke", "--topology", "complete", "--K", "0.2",
            "--base-seed", "7", "--output-dir", tempDir.toString()
        });
        Topology topology = Topology.complete(config.n());

        FhnSimulation.Result first = FhnSimulation.run(config, topology);
        FhnSimulation.Result second = FhnSimulation.run(config, topology);

        assertEquals(first.observables(), second.observables());
    }

    @Test
    void observablesIncludeInitialAndFinalSavedTimes() {
        Config config = Config.parse(new String[] {
            "smoke", "--topology", "complete", "--K", "0.2",
            "--dt", "0.02", "--T", "0.2", "--save-interval", "0.1",
            "--output-dir", tempDir.toString()
        });

        FhnSimulation.Result result = FhnSimulation.run(config, Topology.complete(config.n()));
        List<FhnSimulation.Observable> observables = result.observables();

        assertEquals(3, observables.size());
        assertEquals(0.0, observables.get(0).t(), 1e-12);
        assertEquals(0.1, observables.get(1).t(), 1e-12);
        assertEquals(0.2, observables.get(2).t(), 1e-12);
        assertFalse(Double.isNaN(observables.get(2).meanV()));
        assertFalse(Double.isNaN(observables.get(2).sigmaV()));
        assertFalse(Double.isNaN(observables.get(2).meanW()));
    }

    @Test
    void saveStatesCapturesAllNeuronsAtSavedTimes() {
        Config config = Config.parse(new String[] {
            "smoke", "--topology", "ring", "--K", "0.2", "--k", "2",
            "--dt", "0.02", "--T", "0.2", "--save-interval", "0.1",
            "--save-states", "--output-dir", tempDir.toString()
        });

        FhnSimulation.Result result = FhnSimulation.run(config, Topology.ring(config.n(), config.ringK()));

        assertEquals(3 * config.n(), result.states().size());
    }
}
```

- [ ] **Step 2: Run failing simulation tests**

Run:

```bash
mvn test -Dtest=FhnSimulationTest
```

Expected: compilation fails because `FhnSimulation` does not exist.

- [ ] **Step 3: Implement RK4 simulation**

Create `src/main/java/ar/edu/itba/sds/tp5/FhnSimulation.java`:

```java
package ar.edu.itba.sds.tp5;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class FhnSimulation {
    private static final double I_EXT = 0.5;
    private static final double EPSILON = 0.08;
    private static final double A = 0.7;
    private static final double B = 0.8;

    private FhnSimulation() {
    }

    public record Observable(double t, double meanV, double sigmaV, double meanW) {
    }

    public record StateRow(double t, int i, double v, double w) {
    }

    public record Result(List<Observable> observables, List<StateRow> states) {
    }

    public static Result run(Config config, Topology topology) {
        int n = config.n();
        double[] v = new double[n];
        double[] w = new double[n];
        initialize(v, w, config.runSeed());

        List<Observable> observables = new ArrayList<>();
        List<StateRow> states = config.saveStates() ? new ArrayList<>() : List.of();

        double t = 0.0;
        int steps = (int) Math.round(config.totalTime() / config.dt());
        int saveEvery = Math.max(1, (int) Math.round(config.saveInterval() / config.dt()));

        save(t, v, w, observables, states, config.saveStates());
        for (int step = 1; step <= steps; step++) {
            rk4Step(v, w, topology, config.kValue(), config.dt());
            t = step * config.dt();
            if (step % saveEvery == 0 || step == steps) {
                save(roundTime(t), v, w, observables, states, config.saveStates());
            }
        }

        return new Result(List.copyOf(observables), config.saveStates() ? List.copyOf(states) : List.of());
    }

    private static void initialize(double[] v, double[] w, long seed) {
        Random random = new Random(seed);
        for (int i = 0; i < v.length; i++) {
            v[i] = -0.05 + 0.1 * random.nextDouble();
            w[i] = -0.05 + 0.1 * random.nextDouble();
        }
    }

    private static void rk4Step(double[] v, double[] w, Topology topology, double k, double dt) {
        int n = v.length;
        double[] k1v = new double[n];
        double[] k1w = new double[n];
        double[] k2v = new double[n];
        double[] k2w = new double[n];
        double[] k3v = new double[n];
        double[] k3w = new double[n];
        double[] k4v = new double[n];
        double[] k4w = new double[n];
        double[] tmpV = new double[n];
        double[] tmpW = new double[n];

        derivatives(v, w, topology, k, k1v, k1w);
        combine(v, w, k1v, k1w, tmpV, tmpW, 0.5 * dt);
        derivatives(tmpV, tmpW, topology, k, k2v, k2w);
        combine(v, w, k2v, k2w, tmpV, tmpW, 0.5 * dt);
        derivatives(tmpV, tmpW, topology, k, k3v, k3w);
        combine(v, w, k3v, k3w, tmpV, tmpW, dt);
        derivatives(tmpV, tmpW, topology, k, k4v, k4w);

        for (int i = 0; i < n; i++) {
            v[i] += dt * (k1v[i] + 2.0 * k2v[i] + 2.0 * k3v[i] + k4v[i]) / 6.0;
            w[i] += dt * (k1w[i] + 2.0 * k2w[i] + 2.0 * k3w[i] + k4w[i]) / 6.0;
        }
    }

    private static void derivatives(double[] v, double[] w, Topology topology, double k, double[] dv, double[] dw) {
        int n = v.length;
        for (int i = 0; i < n; i++) {
            double coupling = 0.0;
            for (int j = 0; j < n; j++) {
                if (topology.edge(i, j)) {
                    coupling += v[j] - v[i];
                }
            }
            dv[i] = v[i] - (v[i] * v[i] * v[i]) / 3.0 - w[i] + I_EXT + k * coupling;
            dw[i] = EPSILON * (v[i] + A - B * w[i]);
        }
    }

    private static void combine(
        double[] v, double[] w, double[] dv, double[] dw, double[] outV, double[] outW, double factor
    ) {
        for (int i = 0; i < v.length; i++) {
            outV[i] = v[i] + factor * dv[i];
            outW[i] = w[i] + factor * dw[i];
        }
    }

    private static void save(
        double t, double[] v, double[] w, List<Observable> observables, List<StateRow> states, boolean saveStates
    ) {
        double meanV = 0.0;
        double meanW = 0.0;
        for (int i = 0; i < v.length; i++) {
            meanV += v[i];
            meanW += w[i];
        }
        meanV /= v.length;
        meanW /= w.length;

        double variance = 0.0;
        for (double value : v) {
            double delta = value - meanV;
            variance += delta * delta;
        }
        observables.add(new Observable(t, meanV, Math.sqrt(variance / v.length), meanW));

        if (saveStates) {
            for (int i = 0; i < v.length; i++) {
                states.add(new StateRow(t, i, v[i], w[i]));
            }
        }
    }

    private static double roundTime(double t) {
        return Math.round(t * 1_000_000_000_000.0) / 1_000_000_000_000.0;
    }
}
```

- [ ] **Step 4: Run simulation tests**

Run:

```bash
mvn test -Dtest=FhnSimulationTest
```

Expected: all simulation tests pass.

- [ ] **Step 5: Commit simulation core**

```bash
git add src/main/java/ar/edu/itba/sds/tp5/FhnSimulation.java src/test/java/ar/edu/itba/sds/tp5/FhnSimulationTest.java
git commit -m "feat: add RK4 FitzHugh-Nagumo simulation"
```

---

### Task 5: Output Writer

**Files:**

- Create: `src/main/java/ar/edu/itba/sds/tp5/OutputWriter.java`
- Modify: `src/test/java/ar/edu/itba/sds/tp5/MainCliTest.java`

- [ ] **Step 1: Add output file behavior test**

Append this test to `MainCliTest`:

```java
    @Test
    void outputWriterCreatesMetadataObservablesAndStatesWhenRequested() throws Exception {
        Config config = Config.parse(new String[] {
            "smoke", "--topology", "ring", "--K", "0.2", "--k", "2",
            "--save-states", "--save-adjacency", "--output-dir", tempDir.toString()
        });
        Topology topology = Topology.ring(config.n(), config.ringK());
        FhnSimulation.Result result = FhnSimulation.run(config, topology);

        OutputWriter.writeRun(config, topology, result);

        Path runDir = config.runDirectory();
        org.junit.jupiter.api.Assertions.assertTrue(java.nio.file.Files.exists(runDir.resolve("metadata.properties")));
        org.junit.jupiter.api.Assertions.assertTrue(java.nio.file.Files.exists(runDir.resolve("observables.csv")));
        org.junit.jupiter.api.Assertions.assertTrue(java.nio.file.Files.exists(runDir.resolve("states.csv")));
        org.junit.jupiter.api.Assertions.assertTrue(java.nio.file.Files.exists(runDir.resolve("adjacency.csv")));
    }
```

- [ ] **Step 2: Run failing output test**

Run:

```bash
mvn test -Dtest=MainCliTest
```

Expected: compilation fails because `OutputWriter` does not exist.

- [ ] **Step 3: Implement output writer**

Create `src/main/java/ar/edu/itba/sds/tp5/OutputWriter.java`:

```java
package ar.edu.itba.sds.tp5;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Locale;
import java.util.Properties;

public final class OutputWriter {
    private OutputWriter() {
    }

    public static void writeRun(Config config, Topology topology, FhnSimulation.Result result) throws IOException {
        Path runDir = config.runDirectory();
        Files.createDirectories(runDir);
        writeMetadata(runDir.resolve("metadata.properties"), config, topology);
        writeObservables(runDir.resolve("observables.csv"), result);
        if (config.saveStates()) {
            writeStates(runDir.resolve("states.csv"), result);
        }
        if (config.saveAdjacency()) {
            writeAdjacency(runDir.resolve("adjacency.csv"), topology);
        }
    }

    public static boolean completed(Config config) {
        Path runDir = config.runDirectory();
        return Files.exists(runDir.resolve("metadata.properties")) && Files.exists(runDir.resolve("observables.csv"));
    }

    public static void appendLog(Path outputDir, String line) throws IOException {
        Files.createDirectories(outputDir);
        try (BufferedWriter writer = Files.newBufferedWriter(
            outputDir.resolve("sweep.log"),
            StandardOpenOption.CREATE, StandardOpenOption.APPEND
        )) {
            writer.write(line);
            writer.newLine();
        }
    }

    public static void appendSummary(Path outputDir, Config config, String status) throws IOException {
        Files.createDirectories(outputDir);
        Path summary = outputDir.resolve("summary.csv");
        boolean writeHeader = !Files.exists(summary);
        try (BufferedWriter writer = Files.newBufferedWriter(
            summary,
            StandardOpenOption.CREATE,
            StandardOpenOption.APPEND
        )) {
            if (writeHeader) {
                writer.write("topology,K,p,k,realization,baseSeed,runSeed,outputDir,status");
                writer.newLine();
            }
            writer.write(String.format(
                Locale.ROOT,
                "%s,%.2f,%s,%s,%d,%d,%d,%s,%s",
                config.topology(),
                config.kValue(),
                Double.isNaN(config.pValue()) ? "" : String.format(Locale.ROOT, "%.2f", config.pValue()),
                config.ringK() < 0 ? "" : Integer.toString(config.ringK()),
                config.realizationIndex(),
                config.baseSeed(),
                config.runSeed(),
                config.runDirectory(),
                status
            ));
            writer.newLine();
        }
    }

    private static void writeMetadata(Path path, Config config, Topology topology) throws IOException {
        Properties properties = new Properties();
        properties.setProperty("mode", config.mode());
        properties.setProperty("topology", config.topology());
        properties.setProperty("N", Integer.toString(config.n()));
        properties.setProperty("K", Double.toString(config.kValue()));
        properties.setProperty("p", Double.isNaN(config.pValue()) ? "" : Double.toString(config.pValue()));
        properties.setProperty("k", config.ringK() < 0 ? "" : Integer.toString(config.ringK()));
        properties.setProperty("dt", Double.toString(config.dt()));
        properties.setProperty("T", Double.toString(config.totalTime()));
        properties.setProperty("saveInterval", Double.toString(config.saveInterval()));
        properties.setProperty("realization", Integer.toString(config.realizationIndex()));
        properties.setProperty("baseSeed", Long.toString(config.baseSeed()));
        properties.setProperty("runSeed", Long.toString(config.runSeed()));
        properties.setProperty("saveStates", Boolean.toString(config.saveStates()));
        properties.setProperty("saveAdjacency", Boolean.toString(config.saveAdjacency()));
        properties.setProperty("topologyType", topology.type().name());
        try (BufferedWriter writer = Files.newBufferedWriter(path)) {
            properties.store(writer, "TP5 Sistema 2 FitzHugh-Nagumo run metadata");
        }
    }

    private static void writeObservables(Path path, FhnSimulation.Result result) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(path)) {
            writer.write("t,mean_v,sigma_v,mean_w");
            writer.newLine();
            for (FhnSimulation.Observable row : result.observables()) {
                writer.write(String.format(Locale.ROOT, "%.12f,%.12f,%.12f,%.12f",
                    row.t(), row.meanV(), row.sigmaV(), row.meanW()));
                writer.newLine();
            }
        }
    }

    private static void writeStates(Path path, FhnSimulation.Result result) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(path)) {
            writer.write("t,i,v,w");
            writer.newLine();
            for (FhnSimulation.StateRow row : result.states()) {
                writer.write(String.format(Locale.ROOT, "%.12f,%d,%.12f,%.12f",
                    row.t(), row.i(), row.v(), row.w()));
                writer.newLine();
            }
        }
    }

    private static void writeAdjacency(Path path, Topology topology) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(path)) {
            writer.write("i,j,Aij");
            writer.newLine();
            for (int i = 0; i < topology.size(); i++) {
                for (int j = 0; j < topology.size(); j++) {
                    writer.write(i + "," + j + "," + (topology.edge(i, j) ? "1" : "0"));
                    writer.newLine();
                }
            }
        }
    }
}
```

- [ ] **Step 4: Run output tests**

Run:

```bash
mvn test -Dtest=MainCliTest
```

Expected: all tests in `MainCliTest` pass.

- [ ] **Step 5: Commit output writer**

```bash
git add src/main/java/ar/edu/itba/sds/tp5/OutputWriter.java src/test/java/ar/edu/itba/sds/tp5/MainCliTest.java
git commit -m "feat: write simulation output files"
```

---

### Task 6: Main CLI for Smoke and Single Runs

**Files:**

- Create: `src/main/java/ar/edu/itba/sds/tp5/Main.java`
- Modify: `src/test/java/ar/edu/itba/sds/tp5/MainCliTest.java`

- [ ] **Step 1: Add CLI smoke and single tests**

Append these tests to `MainCliTest`:

```java
    @Test
    void smokeCommandGeneratesBaseOutputs() throws Exception {
        int exitCode = Main.run(new String[] {"smoke", "--output-dir", tempDir.toString()});

        assertEquals(0, exitCode);
        Path runDir = tempDir.resolve("runs").resolve("complete").resolve("K_0.20").resolve("seed_0001");
        org.junit.jupiter.api.Assertions.assertTrue(java.nio.file.Files.exists(runDir.resolve("metadata.properties")));
        org.junit.jupiter.api.Assertions.assertTrue(java.nio.file.Files.exists(runDir.resolve("observables.csv")));
    }

    @Test
    void singleRandomCommandGeneratesOutputs() throws Exception {
        int exitCode = Main.run(new String[] {
            "single", "--topology", "random", "--K", "0.3", "--p", "0.4",
            "--N", "501", "--T", "0.1", "--dt", "0.01", "--save-interval", "0.1",
            "--output-dir", tempDir.toString()
        });

        assertEquals(0, exitCode);
        Path runDir = tempDir.resolve("runs").resolve("random").resolve("p_0.40").resolve("K_0.30").resolve("seed_0001");
        org.junit.jupiter.api.Assertions.assertTrue(java.nio.file.Files.exists(runDir.resolve("observables.csv")));
    }
```

- [ ] **Step 2: Run failing CLI tests**

Run:

```bash
mvn test -Dtest=MainCliTest
```

Expected: compilation fails because `Main` does not exist.

- [ ] **Step 3: Implement `Main` smoke and single modes**

Create `src/main/java/ar/edu/itba/sds/tp5/Main.java`:

```java
package ar.edu.itba.sds.tp5;

import java.util.ArrayList;
import java.util.List;

public final class Main {
    private Main() {
    }

    public static void main(String[] args) throws Exception {
        int exitCode = run(args);
        if (exitCode != 0) {
            System.exit(exitCode);
        }
    }

    public static int run(String[] args) throws Exception {
        Config config = Config.parse(args);
        if ("smoke".equals(config.mode())) {
            Config smoke = config.withSweepValues("complete", 0.2, Double.NaN, -1, 1);
            runOne(smoke);
            return 0;
        }
        if ("single".equals(config.mode())) {
            runOne(config);
            return 0;
        }
        if ("sweep".equals(config.mode())) {
            return runSweep(config);
        }
        throw new IllegalArgumentException("mode must be smoke, single, or sweep");
    }

    private static void runOne(Config config) throws Exception {
        if (OutputWriter.completed(config) && !config.overwrite()) {
            System.out.println("SKIP existing " + config.runDirectory());
            return;
        }
        Topology topology = topologyFor(config);
        FhnSimulation.Result result = FhnSimulation.run(config, topology);
        OutputWriter.writeRun(config, topology, result);
        System.out.println("OK " + config.runDirectory());
    }

    private static Topology topologyFor(Config config) {
        return switch (config.topology()) {
            case "complete" -> Topology.complete(config.n());
            case "random" -> Topology.random(config.n(), config.pValue(), config.runSeed());
            case "ring" -> Topology.ring(config.n(), config.ringK());
            default -> throw new IllegalArgumentException("unsupported topology for run: " + config.topology());
        };
    }

    private static int runSweep(Config config) throws Exception {
        List<Config> runs = sweepRuns(config);
        for (int i = 0; i < runs.size(); i++) {
            Config run = runs.get(i);
            System.out.printf("[%d/%d] %s START%n", i + 1, runs.size(), run.runDirectory());
            runOne(run);
            OutputWriter.appendSummary(config.outputDir(), run, "OK");
        }
        return 0;
    }

    private static List<Config> sweepRuns(Config config) {
        List<Config> runs = new ArrayList<>();
        if ("complete".equals(config.topology()) || "all".equals(config.topology())) {
            for (double k : grid01()) {
                for (int rep = 1; rep <= config.realizations(); rep++) {
                    runs.add(config.withSweepValues("complete", k, Double.NaN, -1, rep));
                }
            }
        }
        if ("random".equals(config.topology()) || "all".equals(config.topology())) {
            for (double p : grid01()) {
                for (double k : grid01()) {
                    for (int rep = 1; rep <= config.realizations(); rep++) {
                        runs.add(config.withSweepValues("random", k, p, -1, rep));
                    }
                }
            }
        }
        if ("ring".equals(config.topology()) || "all".equals(config.topology())) {
            for (int ringK = 1; ringK <= 10; ringK++) {
                for (double k : grid01()) {
                    for (int rep = 1; rep <= config.realizations(); rep++) {
                        runs.add(config.withSweepValues("ring", k, Double.NaN, ringK, rep));
                    }
                }
            }
        }
        return runs;
    }

    private static double[] grid01() {
        double[] values = new double[11];
        for (int i = 0; i < values.length; i++) {
            values[i] = i / 10.0;
        }
        return values;
    }
}
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
mvn test -Dtest=MainCliTest
```

Expected: all CLI tests pass.

- [ ] **Step 5: Run manual smoke**

Run:

```bash
mvn exec:java -Dexec.args="smoke"
```

Expected: prints `OK outputs/runs/complete/K_0.20/seed_0001` and creates `outputs/runs/complete/K_0.20/seed_0001/observables.csv`.

- [ ] **Step 6: Remove manual smoke outputs from working tree if needed**

Run:

```bash
rm -rf outputs
```

This is allowed because `outputs/` was generated by the current task and is ignored.

- [ ] **Step 7: Commit smoke and single CLI**

```bash
git add src/main/java/ar/edu/itba/sds/tp5/Main.java src/test/java/ar/edu/itba/sds/tp5/MainCliTest.java
git commit -m "feat: add smoke and single CLI runs"
```

---

### Task 7: Sweep Resume, Summary, Log, and Threads

**Files:**

- Modify: `src/main/java/ar/edu/itba/sds/tp5/Main.java`
- Modify: `src/main/java/ar/edu/itba/sds/tp5/OutputWriter.java`
- Create: `src/test/java/ar/edu/itba/sds/tp5/SweepTest.java`

- [ ] **Step 1: Write sweep behavior tests with tiny parameters**

Create `src/test/java/ar/edu/itba/sds/tp5/SweepTest.java`:

```java
package ar.edu.itba.sds.tp5;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class SweepTest {
    @TempDir
    Path tempDir;

    @Test
    void sweepCompleteCanRunTinyGridAndWritesSummaryAndLog() throws Exception {
        int exitCode = Main.run(new String[] {
            "sweep", "--topology", "complete", "--N", "501",
            "--T", "0.02", "--dt", "0.01", "--save-interval", "0.01",
            "--realizations", "1", "--threads", "1", "--output-dir", tempDir.toString()
        });

        assertEquals(0, exitCode);
        assertTrue(Files.exists(tempDir.resolve("summary.csv")));
        assertTrue(Files.exists(tempDir.resolve("sweep.log")));
    }

    @Test
    void secondSweepSkipsExistingRuns() throws Exception {
        String[] args = {
            "sweep", "--topology", "complete", "--N", "501",
            "--T", "0.02", "--dt", "0.01", "--save-interval", "0.01",
            "--realizations", "1", "--threads", "1", "--output-dir", tempDir.toString()
        };

        Main.run(args);
        Main.run(args);

        String log = Files.readString(tempDir.resolve("sweep.log"));
        assertTrue(log.contains("SKIP existing"));
    }
}
```

- [ ] **Step 2: Run failing sweep tests**

Run:

```bash
mvn test -Dtest=SweepTest
```

Expected: test fails because `sweep.log` is not written and skips may not be logged.

- [ ] **Step 3: Update `Main.runSweep` with log and skip status**

Replace `runSweep` and add `runOneForSweep` in `Main.java`:

```java
    private static int runSweep(Config config) throws Exception {
        List<Config> runs = sweepRuns(config);
        if (config.threads() == 1) {
            for (int i = 0; i < runs.size(); i++) {
                Config run = runs.get(i);
                String prefix = String.format("[%d/%d] %s", i + 1, runs.size(), describe(run));
                runOneForSweep(config, run, prefix);
            }
            return 0;
        }

        try (java.util.concurrent.ExecutorService executor = java.util.concurrent.Executors.newFixedThreadPool(config.threads())) {
            List<java.util.concurrent.Future<?>> futures = new ArrayList<>();
            for (int i = 0; i < runs.size(); i++) {
                Config run = runs.get(i);
                String prefix = String.format("[%d/%d] %s", i + 1, runs.size(), describe(run));
                futures.add(executor.submit(() -> {
                    try {
                        runOneForSweep(config, run, prefix);
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                }));
            }
            for (java.util.concurrent.Future<?> future : futures) {
                future.get();
            }
        }
        return 0;
    }

    private static void runOneForSweep(Config root, Config run, String prefix) throws Exception {
        long start = System.nanoTime();
        if (OutputWriter.completed(run) && !run.overwrite()) {
            String line = prefix + " SKIP existing";
            System.out.println(line);
            OutputWriter.appendLog(root.outputDir(), line);
            OutputWriter.appendSummary(root.outputDir(), run, "SKIP");
            return;
        }

        String startLine = prefix + " START";
        System.out.println(startLine);
        OutputWriter.appendLog(root.outputDir(), startLine);
        Topology topology = topologyFor(run);
        FhnSimulation.Result result = FhnSimulation.run(run, topology);
        OutputWriter.writeRun(run, topology, result);
        double elapsedSeconds = (System.nanoTime() - start) / 1_000_000_000.0;
        String okLine = String.format(java.util.Locale.ROOT, "%s OK elapsed=%.3fs", prefix, elapsedSeconds);
        System.out.println(okLine);
        OutputWriter.appendLog(root.outputDir(), okLine);
        OutputWriter.appendSummary(root.outputDir(), run, "OK");
    }

    private static String describe(Config run) {
        if ("complete".equals(run.topology())) {
            return String.format(java.util.Locale.ROOT, "complete K=%.2f rep=%d", run.kValue(), run.realizationIndex());
        }
        if ("random".equals(run.topology())) {
            return String.format(java.util.Locale.ROOT, "random p=%.2f K=%.2f rep=%d", run.pValue(), run.kValue(), run.realizationIndex());
        }
        return String.format(java.util.Locale.ROOT, "ring k=%d K=%.2f rep=%d", run.ringK(), run.kValue(), run.realizationIndex());
    }
```

- [ ] **Step 4: Make summary/log writes thread-safe**

Add `synchronized` to these `OutputWriter` methods:

```java
    public static synchronized void appendLog(Path outputDir, String line) throws IOException {
        Files.createDirectories(outputDir);
        try (BufferedWriter writer = Files.newBufferedWriter(
            outputDir.resolve("sweep.log"),
            StandardOpenOption.CREATE,
            StandardOpenOption.APPEND
        )) {
            writer.write(line);
            writer.newLine();
        }
    }

    public static synchronized void appendSummary(Path outputDir, Config config, String status) throws IOException {
        Files.createDirectories(outputDir);
        Path summary = outputDir.resolve("summary.csv");
        boolean writeHeader = !Files.exists(summary);
        try (BufferedWriter writer = Files.newBufferedWriter(
            summary,
            StandardOpenOption.CREATE,
            StandardOpenOption.APPEND
        )) {
            if (writeHeader) {
                writer.write("topology,K,p,k,realization,baseSeed,runSeed,outputDir,status");
                writer.newLine();
            }
            writer.write(String.format(
                Locale.ROOT,
                "%s,%.2f,%s,%s,%d,%d,%d,%s,%s",
                config.topology(),
                config.kValue(),
                Double.isNaN(config.pValue()) ? "" : String.format(Locale.ROOT, "%.2f", config.pValue()),
                config.ringK() < 0 ? "" : Integer.toString(config.ringK()),
                config.realizationIndex(),
                config.baseSeed(),
                config.runSeed(),
                config.runDirectory(),
                status
            ));
            writer.newLine();
        }
    }
```

- [ ] **Step 5: Run sweep tests**

Run:

```bash
mvn test -Dtest=SweepTest
```

Expected: all sweep tests pass.

- [ ] **Step 6: Run all tests**

Run:

```bash
mvn test
```

Expected: all tests pass.

- [ ] **Step 7: Commit sweep support**

```bash
git add src/main/java/ar/edu/itba/sds/tp5/Main.java src/main/java/ar/edu/itba/sds/tp5/OutputWriter.java src/test/java/ar/edu/itba/sds/tp5/SweepTest.java
git commit -m "feat: add resumable sweep execution"
```

---

### Task 8: Manual Verification and Delivery Guardrails

**Files:**

- Modify: `docs/superpowers/plans/fhn-motor-implementation-plan.md` only if verification discovers a mismatch in this plan.

- [ ] **Step 1: Run complete test suite**

Run:

```bash
mvn test
```

Expected: all tests pass.

- [ ] **Step 2: Run smoke from Maven exec**

Run:

```bash
mvn exec:java -Dexec.args="smoke --output-dir tmp/smoke"
```

Expected:

```text
OK tmp/smoke/runs/complete/K_0.20/seed_0001
```

Files expected:

```text
tmp/smoke/runs/complete/K_0.20/seed_0001/metadata.properties
tmp/smoke/runs/complete/K_0.20/seed_0001/observables.csv
```

- [ ] **Step 3: Run representative single cases**

Run:

```bash
mvn exec:java -Dexec.args="single --topology complete --K 0.5 --N 600 --dt 0.01 --T 1 --output-dir tmp/manual"
mvn exec:java -Dexec.args="single --topology random --K 0.5 --p 0.3 --N 600 --dt 0.01 --T 1 --output-dir tmp/manual"
mvn exec:java -Dexec.args="single --topology ring --K 0.5 --k 5 --N 600 --dt 0.01 --T 1 --output-dir tmp/manual"
```

Expected: three `OK` lines and one run directory for each topology under `tmp/manual/runs/`.

- [ ] **Step 4: Verify output headers**

Run:

```bash
head -1 tmp/manual/runs/complete/K_0.50/seed_0001/observables.csv
```

Expected:

```text
t,mean_v,sigma_v,mean_w
```

- [ ] **Step 5: Verify optional states output**

Run:

```bash
mvn exec:java -Dexec.args="single --topology ring --K 0.5 --k 5 --N 600 --dt 0.01 --T 0.2 --save-states --output-dir tmp/states"
head -1 tmp/states/runs/ring/k_05/K_0.50/seed_0001/states.csv
```

Expected:

```text
t,i,v,w
```

- [ ] **Step 6: Verify source size signal**

Run:

```bash
find src/main/java -name '*.java' -print0 | xargs -0 wc -c
```

Expected: record the total in the task closeout. If the total is far above 20 kB, do not minify immediately; report it as a delivery risk because Maven repo code and final deliverable can be handled separately.

- [ ] **Step 7: Remove generated verification outputs**

Run:

```bash
rm -rf tmp outputs target
```

This removes artifacts generated by the verification steps. It must not delete source, docs, or user data.

- [ ] **Step 8: Final git status**

Run:

```bash
git status --short
```

Expected: only intended source/test/doc changes are present.

- [ ] **Step 9: Commit final verification adjustments if any**

If no plan mismatch was found, skip this commit. If a correction to the plan was necessary:

```bash
git add docs/superpowers/plans/fhn-motor-implementation-plan.md
git commit -m "docs: align FHN motor implementation plan"
```

---

## Execution Notes

- Keep production code dependency-free. JUnit is test-only.
- Keep tests blackbox and behavior-oriented. Do not assert private method behavior or exact internal call order.
- Do not implement analysis, animation, presentation, Sistema 1, or Sistema 3 in this plan.
- Do not generate production-scale sweeps until smoke, single, and tiny sweep checks pass.
- Do not commit `outputs/`, `tmp/`, `target/`, videos, or generated caches.
- Preserve the literal coupling from the enunciado:

```text
K * sum_j Aij * (v_j - v_i)
```

## Self-Review

Spec coverage:

- Maven Java 21 motor: Task 1.
- CLI parsing and validation: Task 2.
- Matrix topologies complete/random/ring: Task 3.
- RK4 FHN simulation and observables: Task 4.
- Metadata, observables, states, adjacency outputs: Task 5.
- `smoke` and `single`: Task 6.
- `sweep`, resume, summary, log, threads: Task 7.
- Verification and delivery risk checks: Task 8.

Known implementation tradeoffs:

- `--output-dir` is added as a practical CLI flag for tests and local runs. Default remains `outputs`.
- `adjacency.csv` is written as full `i,j,Aij` when requested. This matches the spec recommendation and keeps the optional output explicit.
- `Config.withSweepValues` reuses the base config to derive sweep runs. Validation remains centralized in `Config.parse`; generated sweep configs are built from already validated values.
