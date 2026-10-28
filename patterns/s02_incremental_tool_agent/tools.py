"""Developer tools the agent can choose from (registry pattern, like the original demo)."""

import re

from shared.sandbox import TEST_FILE, run_tests


def make_tools(files: dict[str, str], tests: str) -> dict:
    """Build the tool registry bound to one project snapshot."""

    def list_files() -> str:
        return "\n".join(sorted(files) + [TEST_FILE])

    def read_file(path: str = "") -> str:
        if path == TEST_FILE:
            return tests
        return files.get(path, f"ERROR: no such file '{path}'. Files: {', '.join(sorted(files))}")

    def search_code(pattern: str = "") -> str:
        hits = []
        for name, src in sorted(files.items()):
            for i, line in enumerate(src.splitlines(), 1):
                if re.search(pattern, line, re.IGNORECASE):
                    hits.append(f"{name}:{i}: {line.strip()}")
        return "\n".join(hits[:40]) or "no matches"

    def run_test_suite() -> str:
        report = run_tests(files, tests)
        return f"{report.summary()}\n{report.output}"

    return {
        "list_files": {"fn": list_files, "description": "List project files. Parameters: {}"},
        "read_file": {"fn": read_file, "description": 'Show a file. Parameters: {"path": "<file name>"}'},
        "search_code": {"fn": search_code, "description": 'Regex search all source files. Parameters: {"pattern": "<regex>"}'},
        "run_tests": {"fn": run_test_suite, "description": "Run the unit tests and return the report. Parameters: {}"},
    }


def tool_descriptions(tools: dict) -> str:
    return "\n".join(f"- {name}: {t['description']}" for name, t in tools.items())
