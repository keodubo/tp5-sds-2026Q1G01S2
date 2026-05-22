import subprocess
import sys


def test_cli_requires_run_dir():
    result = subprocess.run(
        [sys.executable, "scripts/animate_fhn.py"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "--run-dir" in result.stderr
