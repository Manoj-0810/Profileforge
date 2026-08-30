"""Unit test performing comprehensive repository-wide secret leakage audit."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

FORBIDDEN_PATTERNS = [
    re.compile(r"password\s*=\s*['\"][^\'\"]+['\"]", re.IGNORECASE),
    re.compile(r"li_at\s*=\s*['\"][^\'\"]+['\"]", re.IGNORECASE),
    re.compile(r"JSESSIONID\s*=\s*['\"][^\'\"]+['\"]", re.IGNORECASE),
    re.compile(r"token\s*=\s*['\"][a-zA-Z0-9_\-]{24,}['\"]", re.IGNORECASE),
]


def test_repository_secret_audit():
    root_dir = Path(__file__).parent.parent.parent
    tracked_files = (
        subprocess.check_output(["git", "ls-files"], cwd=root_dir, text=True)
        .strip()
        .splitlines()
    )

    violations = []
    for rel_path in tracked_files:
        full_path = root_dir / rel_path
        if not full_path.exists() or full_path.is_dir():
            continue

        # Skip example templates or this test file itself
        if rel_path in {".env.example", "tests/unit/test_secret_leakage.py"}:
            continue

        with open(full_path, encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                for pattern in FORBIDDEN_PATTERNS:
                    if pattern.search(line):
                        violations.append(f"{rel_path}:{line_no} -> {line.strip()}")

    assert not violations, (
        f"Potential secret leakage detected in repository files: {violations}"
    )
