package ar.edu.itba.sds.tp5;

import java.io.BufferedReader;
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
        writeMetadata(runDir.resolve("metadata.properties"), config, topology, result);
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
        Path metadata = runDir.resolve("metadata.properties");
        Path observables = runDir.resolve("observables.csv");
        if (!Files.exists(metadata) || !Files.exists(observables)) {
            return false;
        }
        try {
            if (!metadataMatches(metadata, config)) {
                return false;
            }
        } catch (IOException e) {
            return false;
        }
        if (config.saveStates() && !Files.exists(runDir.resolve("states.csv"))) {
            return false;
        }
        if (config.saveAdjacency() && !Files.exists(runDir.resolve("adjacency.csv"))) {
            return false;
        }
        try (BufferedReader reader = Files.newBufferedReader(observables)) {
            String header = reader.readLine();
            if (!"t,mean_v,sigma_v,mean_w".equals(header)) {
                return false;
            }
            String last = null;
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.isBlank()) {
                    last = line;
                }
            }
            if (last == null) {
                return false;
            }
            String[] columns = last.split(",", -1);
            return columns.length >= 4 && Math.abs(Double.parseDouble(columns[0]) - config.totalTime()) < 1e-9;
        } catch (IOException | NumberFormatException e) {
            return false;
        }
    }

    private static boolean metadataMatches(Path metadata, Config config) throws IOException {
        Properties properties = new Properties();
        try (BufferedReader reader = Files.newBufferedReader(metadata)) {
            properties.load(reader);
        }
        return equalsProperty(properties, "topology", config.topology())
            && equalsProperty(properties, "N", Integer.toString(config.n()))
            && equalsProperty(properties, "K", Double.toString(config.kValue()))
            && equalsProperty(properties, "p", Double.isNaN(config.pValue()) ? "" : Double.toString(config.pValue()))
            && equalsProperty(properties, "k", config.ringK() < 0 ? "" : Integer.toString(config.ringK()))
            && equalsProperty(properties, "dt", Double.toString(config.dt()))
            && equalsProperty(properties, "T", Double.toString(config.totalTime()))
            && equalsProperty(properties, "saveInterval", Double.toString(config.saveInterval()))
            && equalsProperty(properties, "realization", Integer.toString(config.realizationIndex()))
            && equalsProperty(properties, "baseSeed", Long.toString(config.baseSeed()))
            && equalsProperty(properties, "runSeed", Long.toString(config.runSeed()))
            && equalsProperty(properties, "initialStateMin", Double.toString(config.initialStateMin()))
            && equalsProperty(properties, "initialStateMax", Double.toString(config.initialStateMax()));
    }

    private static boolean equalsProperty(Properties properties, String key, String expected) {
        return expected.equals(properties.getProperty(key));
    }

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
                "%s,%s,%s,%s,%d,%d,%d,%s,%s",
                config.topology(),
                Config.formatCoupling(config.kValue()),
                Config.formatProbability(config.pValue()),
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

    private static void writeMetadata(
        Path path, Config config, Topology topology, FhnSimulation.Result result
    ) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(path)) {
            writeProperty(writer, "mode", config.mode());
            writeProperty(writer, "topology", config.topology());
            writeProperty(writer, "N", Integer.toString(config.n()));
            writeProperty(writer, "K", Double.toString(config.kValue()));
            writeProperty(writer, "p", Double.isNaN(config.pValue()) ? "" : Double.toString(config.pValue()));
            writeProperty(writer, "k", config.ringK() < 0 ? "" : Integer.toString(config.ringK()));
            writeProperty(writer, "dt", Double.toString(config.dt()));
            writeProperty(writer, "T", Double.toString(config.totalTime()));
            writeProperty(writer, "saveInterval", Double.toString(config.saveInterval()));
            writeProperty(writer, "realization", Integer.toString(config.realizationIndex()));
            writeProperty(writer, "baseSeed", Long.toString(config.baseSeed()));
            writeProperty(writer, "runSeed", Long.toString(config.runSeed()));
            writeProperty(writer, "initialStateMin", Double.toString(config.initialStateMin()));
            writeProperty(writer, "initialStateMax", Double.toString(config.initialStateMax()));
            writeProperty(writer, "saveStates", Boolean.toString(config.saveStates()));
            writeProperty(writer, "saveAdjacency", Boolean.toString(config.saveAdjacency()));
            writeProperty(writer, "usedPartialFinalStep", Boolean.toString(result.usedPartialFinalStep()));
            writeProperty(writer, "topologyType", topology.type().name());
        }
    }

    private static void writeProperty(BufferedWriter writer, String key, String value) throws IOException {
        writer.write(key + "=" + value);
        writer.newLine();
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
