import subprocess
import sys
from pathlib import Path


def test_multiprocess_buffer_fifo_and_overlap():
    project_root = Path(__file__).resolve().parent
    script = project_root / "test_multiprocess_buffer_experiment.py"

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=45,
    )

    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    assert "PASS: Multiprocess FIFO and overlap test." in output
    assert "Orders verified: 5000" in output