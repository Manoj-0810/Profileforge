"""Unit test performing comprehensive repository-wide secret leakage audit."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# High-confidence secret signatures matching actual leaked credentials
CRITICAL_SECRET_SIGNATURES = [
    # LinkedIn li_at production session tokens (always base64-encoded starting with AQED... > 80 chars)
    re.compile(r"AQED[A-Za-z0-9+/=_\-]{80,}"),
    # AWS Access Key IDs
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # GitHub Personal Access Tokens
    re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{80,}"),
    # Generic Private Key blocks
    re.compile(r"-----BEGIN (?:[A-Z0-9_]+ )?PRIVATE KEY-----"),
]

# Signatures for application source code (excluding tests, docs, and templates)
APP_SECRET_SIGNATURES = [
    re.compile(
        r"(?:password|secret|api_key)\s*=\s*['\"][a-zA-Z0-9_!@#$%^&*()\-+=]{24,}['\"]",
        re.IGNORECASE,
    ),
]


def test_repository_secret_audit():
    """Verify that no real credentials, private keys, or session tokens exist in git tracking."""
    root_dir = Path(__file__).parent.parent.parent
    tracked_files = (
        subprocess.check_output(["git", "ls-files"], cwd=root_dir, text=True)
        .strip()
        .splitlines()
    )

    # 1. Guarantee .env is never tracked
    assert ".env" not in tracked_files, ".env file must NEVER be tracked by Git!"

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
                # Ignore non-secret dev placeholders
                if "test-api-key-123" in line or "forge-secret-dev" in line:
                    continue

                for pattern in CRITICAL_SECRET_SIGNATURES:
                    if pattern.search(line):
                        violations.append(f"{rel_path}:{line_no} -> {line.strip()}")

                if rel_path.startswith("app/"):
                    for pattern in APP_SECRET_SIGNATURES:
                        if pattern.search(line):
                            violations.append(f"{rel_path}:{line_no} -> {line.strip()}")

    assert not violations, (
        f"Potential secret leakage detected in repository files: {violations}"
    )
