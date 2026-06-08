import numpy as np
import subprocess
import sys
from pathlib import Path

from scripts.analyze_fhn_outputs import (
    is_temporal_k,
    plot_complete_log_errorbar,
    plot_random_k01_observables,
    plot_random_k01_stationary,
    plot_ring_heatmap,
    plot_ring_k01_observables,
    plot_ring_k01_stationary,
    plot_sync_time_comparison,
)
from scripts.analysis.fhn import (
    GroupKey,
    RunMetrics,
    aggregate_metrics,
    coverage_gaps,
    first_time_stays_below,
    p_grid,
    summarize_series,
)


def test_first_time_stays_below_requires_remaining_tail_below_threshold():
    t = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    sigma = np.array([0.2, 0.01, 0.08, 0.04, 0.03])

    assert first_time_stays_below(t, sigma, threshold=0.05) == 3.0


def test_first_time_stays_below_returns_none_when_threshold_never_holds():
    t = np.array([0.0, 1.0, 2.0])
    sigma = np.array([0.2, 0.01, 0.08])

    assert first_time_stays_below(t, sigma, threshold=0.005) is None


def test_summarize_series_marks_stable_tail_and_sync_time():
    t = np.arange(10.0)
    mean_v = np.linspace(0.0, 1.0, 10)
    sigma = np.array([0.2, 0.1, 0.08, 0.03, 0.02, 0.015, 0.011, 0.010, 0.010, 0.010])

    summary = summarize_series(
        t,
        mean_v,
        sigma,
        sync_threshold=0.05,
        tail_fraction=0.4,
        stationary_abs_tol=0.002,
        stationary_rel_tol=0.05,
    )

    assert summary.sync_time == 3.0
    assert summary.stationary_ok is True
    assert summary.tail_sigma_mean == np.mean([0.011, 0.010, 0.010, 0.010])


def test_aggregate_metrics_preserves_missing_sync_time_fraction():
    metrics = [
        RunMetrics(
            sync_time=2.0,
            tail_sigma_mean=0.01,
            tail_sigma_std=0.001,
            tail_mean_v_mean=0.2,
            tail_mean_v_std=0.01,
            stationary_delta=0.001,
            stationary_ok=True,
            final_time=10.0,
            row_count=11,
        ),
        RunMetrics(
            sync_time=None,
            tail_sigma_mean=0.04,
            tail_sigma_std=0.002,
            tail_mean_v_mean=0.3,
            tail_mean_v_std=0.02,
            stationary_delta=0.02,
            stationary_ok=False,
            final_time=10.0,
            row_count=11,
        ),
    ]

    aggregate = aggregate_metrics(metrics)

    assert aggregate["run_count"] == 2
    assert aggregate["sync_fraction"] == 0.5
    assert aggregate["stable_sync_fraction"] == 0.5
    assert aggregate["sync_time_mean"] == 2.0
    assert aggregate["stable_sync_time_mean"] == 2.0
    assert aggregate["stationary_ok_fraction"] == 0.5
    assert aggregate["tail_sigma_mean"] == 0.025


def test_coverage_gaps_reports_missing_and_partial_expected_groups():
    groups = {
        GroupKey("complete", 0.0, None, None): [object(), object()],
        GroupKey("random", 0.1, 0.0001, None): [object()],
    }

    gaps = coverage_gaps(groups, expected_realizations=2)

    complete_gap = [
        gap
        for gap in gaps
        if gap["topology"] == "complete" and gap["K"] == 0.1
    ][0]
    random_partial = [
        gap
        for gap in gaps
        if gap["topology"] == "random" and gap["K"] == 0.1 and gap["p"] == 0.0001
    ][0]

    assert complete_gap["status"] == "missing"
    assert complete_gap["present_runs"] == 0
    assert random_partial["status"] == "partial"
    assert random_partial["present_runs"] == 1


def test_p_grid_matches_updated_logarithmic_enunciado_range():
    values = p_grid()

    assert len(values) == 10
    assert values[0] == 0.0001
    assert values[-1] == 0.1
    assert np.allclose(np.diff(np.log10(values)), np.diff(np.log10(values))[0])


def test_analysis_cli_is_runnable_as_repo_script():
    result = subprocess.run(
        [sys.executable, "scripts/analyze_fhn_outputs.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--input-dir" in result.stdout
    assert "--complete-log-input-dir" in result.stdout


def test_temporal_figures_use_only_professor_requested_k_values():
    assert is_temporal_k(0.0) is True
    assert is_temporal_k(0.5) is True
    assert is_temporal_k(1.0) is True
    assert is_temporal_k(0.1) is False


def test_plot_ring_heatmap_writes_png_for_ring_summaries(tmp_path):
    summaries = {
        GroupKey("ring", 0.0, None, 1): {"tail_sigma_mean": 0.2},
        GroupKey("ring", 1.0, None, 1): {"tail_sigma_mean": 0.01},
        GroupKey("ring", 0.0, None, 10): {"tail_sigma_mean": 0.15},
        GroupKey("ring", 1.0, None, 10): {"tail_sigma_mean": 0.001},
    }
    output = tmp_path / "ring.png"

    created = plot_ring_heatmap(
        output,
        summaries,
        value_name="tail_sigma_mean",
        title="Anillo test",
    )

    assert created is True
    assert output.exists()
    assert output.stat().st_size > 0


def test_fixed_k01_stationary_figures_use_updated_initial_study_value(tmp_path):
    summaries = {
        GroupKey("random", 0.1, 0.0001, None): {"tail_sigma_mean": 0.2, "tail_sigma_run_std": 0.01},
        GroupKey("random", 0.1, 0.1, None): {"tail_sigma_mean": 0.05, "tail_sigma_run_std": 0.005},
        GroupKey("ring", 0.1, None, 1): {"tail_sigma_mean": 0.2, "tail_sigma_run_std": 0.01},
        GroupKey("ring", 0.1, None, 10): {"tail_sigma_mean": 0.05, "tail_sigma_run_std": 0.005},
    }
    random_output = tmp_path / "random.png"
    ring_output = tmp_path / "ring.png"

    assert plot_random_k01_stationary(random_output, summaries) is True
    assert plot_ring_k01_stationary(ring_output, summaries) is True
    assert random_output.stat().st_size > 0
    assert ring_output.stat().st_size > 0


def test_fixed_k01_observable_figures_use_only_provided_summary_values(tmp_path):
    metric_values = {
        "tail_mean_v_mean": 0.2,
        "tail_mean_v_run_std": 0.01,
        "tail_sigma_mean": 0.05,
        "tail_sigma_run_std": 0.005,
    }
    summaries = {
        GroupKey("random", 0.1, 0.0001, None): metric_values,
        GroupKey("random", 0.1, 0.1, None): metric_values,
        GroupKey("ring", 0.1, None, 1): metric_values,
        GroupKey("ring", 0.1, None, 10): metric_values,
    }
    random_output = tmp_path / "random_observables.png"
    ring_output = tmp_path / "ring_observables.png"

    assert plot_random_k01_observables(random_output, summaries) is True
    assert plot_ring_k01_observables(ring_output, summaries) is True
    assert random_output.stat().st_size > 0
    assert ring_output.stat().st_size > 0


def test_sync_time_comparison_writes_png_for_explicit_representative_networks(tmp_path):
    metric_values = {"sync_time_mean": 4.0, "sync_time_std": 0.5}
    summaries = {
        GroupKey("complete", 0.1, None, None): metric_values,
        GroupKey("random", 0.1, 0.1, None): metric_values,
        GroupKey("ring", 0.1, None, 10): metric_values,
    }
    output = tmp_path / "comparison.png"

    created = plot_sync_time_comparison(
        output,
        summaries,
        representative_p=0.1,
        representative_ring_k=10,
    )

    assert created is True
    assert output.stat().st_size > 0


def test_complete_log_figure_uses_positive_k_and_accepts_zero_reference(tmp_path):
    summaries = {
        GroupKey("complete", 0.0, None, None): {
            "tail_sigma_mean": 0.8,
            "tail_sigma_run_std": 0.02,
        },
        GroupKey("complete", 0.0001, None, None): {
            "tail_sigma_mean": 0.7,
            "tail_sigma_run_std": 0.02,
        },
        GroupKey("complete", 0.1, None, None): {
            "tail_sigma_mean": 0.001,
            "tail_sigma_run_std": 0.0001,
        },
    }
    output = tmp_path / "complete_log.png"

    created = plot_complete_log_errorbar(
        output,
        summaries,
        value_name="tail_sigma_mean",
        ylabel="sigma",
        title="Complete log test",
    )

    assert created is True
    assert output.stat().st_size > 0
