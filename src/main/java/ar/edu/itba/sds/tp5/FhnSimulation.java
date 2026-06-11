package ar.edu.itba.sds.tp5;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class FhnSimulation {
    private static final double EPS = 1e-12;
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

    public record Result(List<Observable> observables, List<StateRow> states, boolean usedPartialFinalStep) {
    }

    private static final class Workspace {
        final double[] k1v, k1w, k2v, k2w, k3v, k3w, k4v, k4w, tmpV, tmpW;

        Workspace(int n) {
            k1v = new double[n];
            k1w = new double[n];
            k2v = new double[n];
            k2w = new double[n];
            k3v = new double[n];
            k3w = new double[n];
            k4v = new double[n];
            k4w = new double[n];
            tmpV = new double[n];
            tmpW = new double[n];
        }
    }

    public static Result run(Config config, Topology topology) {
        int n = config.n();
        double[] v = new double[n];
        double[] w = new double[n];
        initialize(v, w, config.runSeed(), config.initialStateMin(), config.initialStateMax());

        List<Observable> observables = new ArrayList<>();
        List<StateRow> states = config.saveStates() ? new ArrayList<>() : List.of();
        Workspace workspace = new Workspace(n);

        double t = 0.0;
        double nextSaveTime = config.saveInterval();
        boolean usedPartialFinalStep = false;

        save(t, v, w, observables, states, config.saveStates());
        while (t < config.totalTime() - EPS) {
            double stepDt = Math.min(config.dt(), config.totalTime() - t);
            if (stepDt < config.dt() - EPS) {
                usedPartialFinalStep = true;
            }
            rk4Step(v, w, topology, config.kValue(), stepDt, workspace);
            t = roundTime(t + stepDt);
            if (t + EPS >= nextSaveTime || t >= config.totalTime() - EPS) {
                save(roundTime(t), v, w, observables, states, config.saveStates());
                while (nextSaveTime <= t + EPS) {
                    nextSaveTime += config.saveInterval();
                }
            }
        }

        return new Result(
            List.copyOf(observables),
            config.saveStates() ? List.copyOf(states) : List.of(),
            usedPartialFinalStep
        );
    }

    private static void initialize(double[] v, double[] w, long seed, double initialStateMin, double initialStateMax) {
        Random random = new Random(seed);
        double width = initialStateMax - initialStateMin;
        for (int i = 0; i < v.length; i++) {
            v[i] = initialStateMin + width * random.nextDouble();
            w[i] = initialStateMin + width * random.nextDouble();
        }
    }

    private static void rk4Step(double[] v, double[] w, Topology topology, double k, double dt, Workspace ws) {
        derivatives(v, w, topology, k, ws.k1v, ws.k1w);
        combine(v, w, ws.k1v, ws.k1w, ws.tmpV, ws.tmpW, 0.5 * dt);
        derivatives(ws.tmpV, ws.tmpW, topology, k, ws.k2v, ws.k2w);
        combine(v, w, ws.k2v, ws.k2w, ws.tmpV, ws.tmpW, 0.5 * dt);
        derivatives(ws.tmpV, ws.tmpW, topology, k, ws.k3v, ws.k3w);
        combine(v, w, ws.k3v, ws.k3w, ws.tmpV, ws.tmpW, dt);
        derivatives(ws.tmpV, ws.tmpW, topology, k, ws.k4v, ws.k4w);

        for (int i = 0; i < v.length; i++) {
            v[i] += dt * (ws.k1v[i] + 2.0 * ws.k2v[i] + 2.0 * ws.k3v[i] + ws.k4v[i]) / 6.0;
            w[i] += dt * (ws.k1w[i] + 2.0 * ws.k2w[i] + 2.0 * ws.k3w[i] + ws.k4w[i]) / 6.0;
        }
    }

    private static void derivatives(double[] v, double[] w, Topology topology, double k, double[] dv, double[] dw) {
        for (int i = 0; i < v.length; i++) {
            double coupling = 0.0;
            if (k != 0.0) {
                for (int j : topology.activeNeighbors(i)) {
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
