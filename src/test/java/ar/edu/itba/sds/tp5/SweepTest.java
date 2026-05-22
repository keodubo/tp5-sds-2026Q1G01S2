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

    @Test
    void randomSweepDoesNotRequireSpecificP() throws Exception {
        int exitCode = Main.run(new String[] {
            "sweep", "--topology", "random", "--N", "501",
            "--T", "0.01", "--dt", "0.01", "--save-interval", "0.01",
            "--realizations", "1", "--threads", "1", "--output-dir", tempDir.toString()
        });

        assertEquals(0, exitCode);
        assertTrue(Files.exists(tempDir.resolve("runs").resolve("random").resolve("p_0.00").resolve("K_0.00").resolve("seed_0001").resolve("observables.csv")));
        assertTrue(Files.exists(tempDir.resolve("runs").resolve("random").resolve("p_1.00").resolve("K_1.00").resolve("seed_0001").resolve("observables.csv")));
    }

    @Test
    void ringSweepDoesNotRequireSpecificK() throws Exception {
        int exitCode = Main.run(new String[] {
            "sweep", "--topology", "ring", "--N", "501",
            "--T", "0.01", "--dt", "0.01", "--save-interval", "0.01",
            "--realizations", "1", "--threads", "1", "--output-dir", tempDir.toString()
        });

        assertEquals(0, exitCode);
        assertTrue(Files.exists(tempDir.resolve("runs").resolve("ring").resolve("k_01").resolve("K_0.00").resolve("seed_0001").resolve("observables.csv")));
        assertTrue(Files.exists(tempDir.resolve("runs").resolve("ring").resolve("k_10").resolve("K_1.00").resolve("seed_0001").resolve("observables.csv")));
    }
}
