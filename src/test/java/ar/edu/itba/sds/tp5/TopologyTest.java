package ar.edu.itba.sds.tp5;

import org.junit.jupiter.api.Test;

import java.util.Arrays;

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
    void activeNeighborsMatchAdjacencyRows() {
        Topology topology = Topology.ring(6, 2);

        assertArrayEquals(new int[] {1, 2, 4, 5}, topology.activeNeighbors(0));
    }

    @Test
    void randomIsReproducibleWithSeed() {
        boolean[][] first = Topology.random(8, 0.35, 99L).adjacency();
        boolean[][] second = Topology.random(8, 0.35, 99L).adjacency();

        assertTrue(Arrays.deepEquals(first, second));
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
