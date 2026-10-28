"""Sandbox — run generated code and its tests in a throwaway directory.

This is the "ground truth" every pattern leans on: instead of trusting an LLM
to say code is correct, we EXECUTE it against tests. Each run happens in a
fresh temp directory, in a separate Python process, with a timeout.

WARNING: this is process-level isolation, not a security sandbox. It is fine for
a classroom demo running model output locally; do not point it at untrusted
models or use it in production without containers/seccomp.
"""

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from shared.codeutil import truncate

TEST_FILE = "test_suite.py"
_MARKER = "@@RESULT@@"

# Runs the unittest suite and prints one machine-readable line at the end.
_RUNNER = f'''
import io, json, unittest
suite = unittest.defaultTestLoader.loadTestsFromName("test_suite")
stream = io.StringIO()
res = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
print("{_MARKER}" + json.dumps({{
    "total": res.testsRun,
    "failed": len(res.failures) + len(res.errors),
    "output": stream.getvalue(),
}}))
'''


@dataclass
class TestReport:
    __test__ = False  # not a pytest class

    total: int
    failed: int
    output: str

    @property
    def passed(self) -> int:
        return max(self.total - self.failed, 0)

    @property
    def ok(self) -> bool:
        return self.total > 0 and self.failed == 0

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def summary(self) -> str:
        return f"{self.passed}/{self.total} tests passed"


@dataclass
class ScriptResult:
    ok: bool
    stdout: str
    stderr: str


def _write_files(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        target = (root / name).resolve()
        if root.resolve() not in target.parents:
            raise ValueError(f"Refusing to write outside the sandbox: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def _run(args: list[str], cwd: Path, timeout: int) -> tuple[int, str, str]:
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        p = subprocess.run(
            [sys.executable, *args], cwd=cwd, env=env,
            capture_output=True, text=True, timeout=timeout,
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT: exceeded {timeout}s (infinite loop?)"


def run_tests(files: dict[str, str], tests: str | None = None, timeout: int = 20) -> TestReport:
    """Run test_suite.py against `files`. `tests` (if given) is written as test_suite.py."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_files(root, files)
        if tests is not None:
            (root / TEST_FILE).write_text(tests)
        (root / "_runner.py").write_text(_RUNNER)

        code, out, err = _run(["_runner.py"], root, timeout)
        for line in out.splitlines():
            if line.startswith(_MARKER):
                data = json.loads(line[len(_MARKER):])
                return TestReport(data["total"], data["failed"], truncate(data["output"], 3500))
        # Runner crashed or timed out (e.g. syntax error in the test import chain).
        return TestReport(1, 1, truncate((out + err).strip() or "Test runner produced no output.", 3500))


def run_script(files: dict[str, str], script: str, timeout: int = 10) -> ScriptResult:
    """Run an arbitrary driver script next to `files` (used for behavioural probes)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_files(root, files)
        (root / "_probe.py").write_text(script)
        code, out, err = _run(["_probe.py"], root, timeout)
        return ScriptResult(code == 0, out, truncate(err, 1500))
