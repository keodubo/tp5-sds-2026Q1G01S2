package ar.edu.itba.sds.tp5;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

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
        if ("sweep".equals(config.mode()) || "complete-log-sweep".equals(config.mode())) {
            return runSweep(config);
        }
        throw new IllegalArgumentException("mode must be smoke, single, sweep, or complete-log-sweep");
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

    private static int runSweep(Config config) throws Exception {
        List<Config> runs = sweepRuns(config);
        if (config.threads() == 1) {
            for (int i = 0; i < runs.size(); i++) {
                runOneForSweep(config, runs.get(i), String.format("[%d/%d] %s", i + 1, runs.size(), describe(runs.get(i))));
            }
            return 0;
        }

        try (ExecutorService executor = Executors.newFixedThreadPool(config.threads())) {
            List<Future<?>> futures = new ArrayList<>();
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
            for (Future<?> future : futures) {
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
        String okLine = String.format(Locale.ROOT, "%s OK elapsed=%.3fs", prefix, elapsedSeconds);
        System.out.println(okLine);
        OutputWriter.appendLog(root.outputDir(), okLine);
        OutputWriter.appendSummary(root.outputDir(), run, "OK");
    }

    private static Topology topologyFor(Config config) {
        return switch (config.topology()) {
            case "complete" -> Topology.complete(config.n());
            case "random" -> Topology.random(config.n(), config.pValue(), config.runSeed());
            case "ring" -> Topology.ring(config.n(), config.ringK());
            default -> throw new IllegalArgumentException("unsupported topology for run: " + config.topology());
        };
    }

    private static List<Config> sweepRuns(Config config) {
        List<Config> runs = new ArrayList<>();
        if ("complete-log-sweep".equals(config.mode())) {
            for (double k : completeLogCouplingGrid()) {
                for (int rep = 1; rep <= config.realizations(); rep++) {
                    runs.add(config.withSweepValues("complete", k, Double.NaN, -1, rep));
                }
            }
            return runs;
        }
        if ("complete".equals(config.topology()) || "all".equals(config.topology())) {
            for (double k : couplingGrid()) {
                for (int rep = 1; rep <= config.realizations(); rep++) {
                    runs.add(config.withSweepValues("complete", k, Double.NaN, -1, rep));
                }
            }
        }
        if ("random".equals(config.topology()) || "all".equals(config.topology())) {
            for (double p : probabilityGrid()) {
                for (double k : couplingGrid()) {
                    for (int rep = 1; rep <= config.realizations(); rep++) {
                        runs.add(config.withSweepValues("random", k, p, -1, rep));
                    }
                }
            }
        }
        if ("ring".equals(config.topology()) || "all".equals(config.topology())) {
            for (int ringK = 1; ringK <= 10; ringK++) {
                for (double k : couplingGrid()) {
                    for (int rep = 1; rep <= config.realizations(); rep++) {
                        runs.add(config.withSweepValues("ring", k, Double.NaN, ringK, rep));
                    }
                }
            }
        }
        return runs;
    }

    private static String describe(Config run) {
        if ("complete".equals(run.topology())) {
            return String.format(Locale.ROOT, "complete K=%s rep=%d", Config.formatCoupling(run.kValue()), run.realizationIndex());
        }
        if ("random".equals(run.topology())) {
            return String.format(Locale.ROOT, "random p=%s K=%s rep=%d", Config.formatProbability(run.pValue()), Config.formatCoupling(run.kValue()), run.realizationIndex());
        }
        return String.format(Locale.ROOT, "ring k=%d K=%s rep=%d", run.ringK(), Config.formatCoupling(run.kValue()), run.realizationIndex());
    }

    private static double[] couplingGrid() {
        double[] values = new double[11];
        for (int i = 0; i < values.length; i++) {
            values[i] = i / 10.0;
        }
        return values;
    }

    private static double[] probabilityGrid() {
        double[] values = new double[10];
        for (int i = 0; i < values.length; i++) {
            values[i] = Math.pow(10.0, -4.0 + i * (3.0 / (values.length - 1)));
        }
        values[0] = 1.0e-4;
        values[values.length - 1] = 1.0e-1;
        return values;
    }

    private static double[] completeLogCouplingGrid() {
        double[] values = new double[14];
        values[0] = 0.0;
        for (int i = 1; i < values.length; i++) {
            values[i] = Math.pow(10.0, -4.0 + (i - 1) * (3.0 / (values.length - 2)));
        }
        values[1] = 1.0e-4;
        values[values.length - 1] = 1.0e-1;
        return values;
    }
}
