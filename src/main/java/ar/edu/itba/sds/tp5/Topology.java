package ar.edu.itba.sds.tp5;

import java.util.Random;

public final class Topology {
    public enum Type { COMPLETE, RANDOM, RING }

    private final Type type;
    private final boolean[][] adjacency;
    private final int[][] activeNeighbors;

    private Topology(Type type, boolean[][] adjacency) {
        this.type = type;
        this.adjacency = adjacency;
        this.activeNeighbors = activeNeighbors(adjacency);
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

    public int[] activeNeighbors(int i) {
        return activeNeighbors[i];
    }

    public boolean[][] adjacency() {
        boolean[][] copy = new boolean[adjacency.length][adjacency.length];
        for (int i = 0; i < adjacency.length; i++) {
            System.arraycopy(adjacency[i], 0, copy[i], 0, adjacency.length);
        }
        return copy;
    }

    private static int[][] activeNeighbors(boolean[][] adjacency) {
        int[][] neighbors = new int[adjacency.length][];
        for (int i = 0; i < adjacency.length; i++) {
            int count = 0;
            for (int j = 0; j < adjacency.length; j++) {
                if (adjacency[i][j]) {
                    count++;
                }
            }
            neighbors[i] = new int[count];
            int index = 0;
            for (int j = 0; j < adjacency.length; j++) {
                if (adjacency[i][j]) {
                    neighbors[i][index++] = j;
                }
            }
        }
        return neighbors;
    }
}
