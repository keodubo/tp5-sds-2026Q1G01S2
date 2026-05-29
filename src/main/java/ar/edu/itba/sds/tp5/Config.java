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
        if (topology != null) {
            topology = topology.toLowerCase(Locale.ROOT);
        }
        Config config = new Config(
            mode,
            topology,
            intValue(values, "N", "smoke".equals(mode) ? 12 : 501),
            doubleValue(values, "K", Double.NaN),
            doubleValue(values, "p", Double.NaN),
            intValue(values, "k", -1),
            doubleValue(values, "dt", "smoke".equals(mode) ? 0.02 : 0.01),
            doubleValue(values, "T", "smoke".equals(mode) ? 0.2 : 100.0),
            doubleValue(values, "save-interval", 0.1),
            intValue(values, "realizations", 15),
            longValue(values, "base-seed", 12345L),
            intValue(values, "realization", 1),
            intValue(values, "threads", 1),
            saveStates,
            saveAdjacency,
            overwrite,
            Path.of(values.getOrDefault("output-dir", "outputs"))
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
        if ("all".equals(topology) && !mode.equals("sweep")) {
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
        if (requiresTopologyParameter() && "random".equals(topology) && (Double.isNaN(pValue) || pValue < 1.0e-4 || pValue > 1.0e-1)) {
            throw new IllegalArgumentException("p must be in [1e-4, 1e-1]");
        }
        if (requiresTopologyParameter() && "ring".equals(topology) && (ringK < 1 || ringK > 10)) {
            throw new IllegalArgumentException("k must be in [1, 10]");
        }
        if (!Double.isFinite(dt) || dt <= 0.0) {
            throw new IllegalArgumentException("dt must be positive");
        }
        if (!Double.isFinite(totalTime) || totalTime <= 0.0) {
            throw new IllegalArgumentException("T must be positive");
        }
        if (!Double.isFinite(saveInterval) || saveInterval < dt) {
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
        return ("single".equals(mode) || "smoke".equals(mode))
            && ("complete".equals(topology) || "random".equals(topology) || "ring".equals(topology));
    }

    private boolean requiresTopologyParameter() {
        return "single".equals(mode) || "smoke".equals(mode);
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

    public Config withSweepValues(String newTopology, double newK, double newP, int newRingK, int newRealization) {
        return new Config(
            mode, newTopology, n, newK, newP, newRingK, dt, totalTime, saveInterval,
            realizations, baseSeed, newRealization, threads, saveStates, saveAdjacency, overwrite, outputDir
        );
    }

    private String kDir() {
        return String.format(Locale.ROOT, "K_%.2f", kValue);
    }

    private String pDir() {
        return "p_" + formatProbability(pValue);
    }

    private String ringDir() {
        return String.format(Locale.ROOT, "k_%02d", ringK);
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

    static String formatProbability(double value) {
        if (Double.isNaN(value)) {
            return "";
        }
        if (value >= 0.01) {
            return String.format(Locale.ROOT, "%.2f", value);
        }
        String formatted = String.format(Locale.ROOT, "%.4e", value);
        return formatted.replace("e-0", "e-").replace("e+0", "e+");
    }
}
