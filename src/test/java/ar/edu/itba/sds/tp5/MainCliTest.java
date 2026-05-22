package ar.edu.itba.sds.tp5;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
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
            "single", "--topology", "random", "--K", "0.3", "--p", "0.4",
            "--N", "501", "--T", "0.1", "--dt", "0.01", "--save-interval", "0.1",
            "--output-dir", tempDir.toString()
        });

        assertEquals(0, exitCode);
        Path runDir = tempDir.resolve("runs").resolve("random").resolve("p_0.40").resolve("K_0.30").resolve("seed_0001");
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
