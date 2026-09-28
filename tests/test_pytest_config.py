"""V-02: the plain `python3 -m pytest -q` from the repo root collects only tests/.

Scratch clones under workspace/ carry their own tests/ copies with the same
module basenames, which used to abort collection with "import file mismatch".
"""
import configparser
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INI = REPO / "pytest.ini"


def test_pytest_ini_limits_collection_to_tests():
    cfg = configparser.ConfigParser()
    cfg.read(INI)
    assert cfg.get("pytest", "testpaths").split() == ["tests"]
    skipped = cfg.get("pytest", "norecursedirs").split()
    for name in ("workspace", "scratch", "logs", "data"):
        assert name in skipped


def test_colliding_scratch_clone_tests_are_not_collected(tmp_path):
    shutil.copy(INI, tmp_path / "pytest.ini")
    body = "def test_one():\n    assert True\n"
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_same.py").write_text(body)
    clone = tmp_path / "workspace" / "redesign" / "scratch" / "clone" / "tests"
    clone.mkdir(parents=True)
    (clone / "test_same.py").write_text(body)
    (tmp_path / "logs" / "tests").mkdir(parents=True)
    (tmp_path / "logs" / "tests" / "test_same.py").write_text(body)

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "--collect-only"],
        cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "1 test collected" in proc.stdout
    assert "error" not in proc.stdout.lower()
