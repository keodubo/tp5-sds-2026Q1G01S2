package ar.edu.itba.sds.tp5;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

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
    void nonMultipleTotalTimeUsesPartialFinalStep() {
        Config config = Config.parse(new String[] {
            "smoke", "--topology", "complete", "--K", "0.2",
            "--dt", "0.1", "--T", "0.25", "--save-interval", "0.1",
            "--output-dir", tempDir.toString()
        });

        FhnSimulation.Result result = FhnSimulation.run(config, Topology.complete(config.n()));
        List<FhnSimulation.Observable> observables = result.observables();

        assertEquals(4, observables.size());
        assertEquals(0.25, observables.get(3).t(), 1e-12);
        assertTrue(result.usedPartialFinalStep());
    }

    @Test
    void nonMultipleSaveIntervalUsesFirstSimulatedTimeAfterInterval() {
        Config config = Config.parse(new String[] {
            "smoke", "--topology", "complete", "--K", "0.2",
            "--dt", "0.03", "--T", "0.12", "--save-interval", "0.05",
            "--output-dir", tempDir.toString()
        });

        FhnSimulation.Result result = FhnSimulation.run(config, Topology.complete(config.n()));
        List<FhnSimulation.Observable> observables = result.observables();

        assertEquals(3, observables.size());
        assertEquals(0.0, observables.get(0).t(), 1e-12);
        assertEquals(0.06, observables.get(1).t(), 1e-12);
        assertEquals(0.12, observables.get(2).t(), 1e-12);
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
