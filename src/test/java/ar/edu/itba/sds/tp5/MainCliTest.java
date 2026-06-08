package ar.edu.itba.sds.tp5;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

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

    @Test
    void smokeRejectsAllTopology() {
        IllegalArgumentException ex = assertThrows(
            IllegalArgumentException.class,
            () -> Config.parse(new String[] {"smoke", "--topology", "all", "--output-dir", tempDir.toString()})
        );
        assertEquals("all is only valid for sweep", ex.getMessage());
    }

    @Test
    void completeLogSweepRequiresCompleteTopology() {
        IllegalArgumentException ex = assertThrows(
            IllegalArgumentException.class,
            () -> Config.parse(new String[] {
                "complete-log-sweep", "--topology", "ring", "--output-dir", tempDir.toString()
            })
        );
        assertEquals("complete-log-sweep requires --topology complete", ex.getMessage());
    }

    @Test
    void smallCouplingsUseDistinctDirectoryNames() {
        Config first = Config.parse(new String[] {
            "single", "--topology", "complete", "--K", "0.0001", "--N", "501",
            "--output-dir", tempDir.toString()
        });
        Config second = Config.parse(new String[] {
            "single", "--topology", "complete", "--K", "0.0001778279", "--N", "501",
            "--output-dir", tempDir.toString()
        });

        assertTrue(first.runDirectory().toString().contains("K_1.0000e-4"));
        assertTrue(second.runDirectory().toString().contains("K_1.7783e-4"));
        assertFalse(first.runDirectory().equals(second.runDirectory()));
    }

    @Test
    void rejectsNaNTimeParameters() {
        IllegalArgumentException ex = assertThrows(
            IllegalArgumentException.class,
            () -> Config.parse(new String[] {
                "single", "--topology", "complete", "--K", "0.2", "--dt", "NaN",
                "--output-dir", tempDir.toString()
            })
        );
        assertEquals("dt must be positive", ex.getMessage());
    }

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
        assertTrue(Files.exists(runDir.resolve("metadata.properties")));
        assertTrue(Files.exists(runDir.resolve("observables.csv")));
        assertTrue(Files.exists(runDir.resolve("states.csv")));
        assertTrue(Files.exists(runDir.resolve("adjacency.csv")));
        String metadata = Files.readString(runDir.resolve("metadata.properties"));
        assertTrue(metadata.contains("initialStateMin=-0.5"));
        assertTrue(metadata.contains("initialStateMax=0.5"));
    }

    @Test
    void completedRejectsOutputsWithOldInitialRangeMetadata() throws Exception {
        Config config = Config.parse(new String[] {
            "smoke", "--topology", "complete", "--K", "0.2",
            "--output-dir", tempDir.toString()
        });
        Topology topology = Topology.complete(config.n());
        OutputWriter.writeRun(config, topology, FhnSimulation.run(config, topology));

        Path metadataPath = config.runDirectory().resolve("metadata.properties");
        String oldMetadata = Files.readString(metadataPath)
            .replace("initialStateMin=-0.5", "initialStateMin=-0.05")
            .replace("initialStateMax=0.5", "initialStateMax=0.05");
        Files.writeString(metadataPath, oldMetadata);

        assertFalse(OutputWriter.completed(config));
    }

    @Test
    void smokeCommandGeneratesBaseOutputs() throws Exception {
        int exitCode = Main.run(new String[] {"smoke", "--output-dir", tempDir.toString()});

        assertEquals(0, exitCode);
        Path runDir = tempDir.resolve("runs").resolve("complete").resolve("K_0.20").resolve("seed_0001");
        assertTrue(Files.exists(runDir.resolve("metadata.properties")));
        assertTrue(Files.exists(runDir.resolve("observables.csv")));
    }

    @Test
    void singleRandomCommandGeneratesOutputs() throws Exception {
        int exitCode = Main.run(new String[] {
            "single", "--topology", "random", "--K", "0.3", "--p", "0.1",
            "--N", "501", "--T", "0.1", "--dt", "0.01", "--save-interval", "0.1",
            "--output-dir", tempDir.toString()
        });

        assertEquals(0, exitCode);
        Path runDir = tempDir.resolve("runs").resolve("random").resolve("p_0.10").resolve("K_0.30").resolve("seed_0001");
        assertTrue(Files.exists(runDir.resolve("observables.csv")));
    }

    @Test
    void singleRandomCommandKeepsSmallProbabilitiesDistinct() throws Exception {
        int exitCode = Main.run(new String[] {
            "single", "--topology", "random", "--K", "0.1", "--p", "0.0001",
            "--N", "501", "--T", "0.1", "--dt", "0.01", "--save-interval", "0.1",
            "--output-dir", tempDir.toString()
        });

        assertEquals(0, exitCode);
        Path runDir = tempDir.resolve("runs").resolve("random").resolve("p_1.0000e-4").resolve("K_0.10").resolve("seed_0001");
        assertTrue(Files.exists(runDir.resolve("observables.csv")));
    }

    @Test
    void repeatedSingleRunWritesRequestedOptionalOutputs() throws Exception {
        String[] baseArgs = {
            "single", "--topology", "ring", "--K", "0.2", "--k", "2",
            "--N", "501", "--T", "0.05", "--dt", "0.01", "--save-interval", "0.05",
            "--output-dir", tempDir.toString()
        };
        String[] optionalArgs = {
            "single", "--topology", "ring", "--K", "0.2", "--k", "2",
            "--N", "501", "--T", "0.05", "--dt", "0.01", "--save-interval", "0.05",
            "--save-states", "--save-adjacency", "--output-dir", tempDir.toString()
        };

        Main.run(baseArgs);
        Main.run(optionalArgs);

        Path runDir = tempDir.resolve("runs").resolve("ring").resolve("k_02").resolve("K_0.20").resolve("seed_0001");
        assertTrue(Files.exists(runDir.resolve("states.csv")));
        assertTrue(Files.exists(runDir.resolve("adjacency.csv")));
    }

    @Test
    void repeatedSingleRunDoesNotSkipDifferentSeed() throws Exception {
        String[] firstArgs = {
            "single", "--topology", "complete", "--K", "0.2", "--base-seed", "1",
            "--N", "501", "--T", "0.05", "--dt", "0.01", "--save-interval", "0.05",
            "--output-dir", tempDir.toString()
        };
        String[] secondArgs = {
            "single", "--topology", "complete", "--K", "0.2", "--base-seed", "2",
            "--N", "501", "--T", "0.05", "--dt", "0.01", "--save-interval", "0.05",
            "--output-dir", tempDir.toString()
        };

        Main.run(firstArgs);
        Path metadata = tempDir.resolve("runs").resolve("complete").resolve("K_0.20").resolve("seed_0001").resolve("metadata.properties");
        String firstMetadata = Files.readString(metadata);
        Main.run(secondArgs);

        String secondMetadata = Files.readString(metadata);
        assertTrue(firstMetadata.contains("baseSeed=1"));
        assertTrue(secondMetadata.contains("baseSeed=2"));
    }
}
