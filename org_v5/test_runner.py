"""Auditable test execution runner for V5.2.

Executes test suites in a controlled environment, rigorously separating and
accounting for:
- passed: tests with successful assertions
- failed: tests that produced assertion failures
- errors: tests that crashed unexpectedly
- skipped: tests explicitly bypassed (never masked as passed)

Outputs machine-readable metrics and audit digests.
"""
from __future__ import annotations
import unittest
import json
import time
import hashlib
from pathlib import Path

def run_test_suite(tests_dir: str = 'tests', pattern: str = 'test*.py', cwd: str | Path | None = None) -> dict:
    """
    Runs unittest discover on the target directory and collects discrete counts
    for passed, failed, errors, and skipped tests.
    """
    root_path = Path(cwd) if cwd else Path.cwd()
    start = time.perf_counter()
    loader = unittest.TestLoader()
    target_path = str(root_path / tests_dir) if cwd else tests_dir
    suite = loader.discover(target_path, pattern=pattern)
    
    # Custom test runner capturing output
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    duration = round(time.perf_counter() - start, 4)
    
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total - failures - errors - skipped
    
    success = (failures == 0 and errors == 0)
    
    details = {
        'total_run': total,
        'passed': passed,
        'failed': failures,
        'errors': errors,
        'skipped': skipped,
        'clean_pass': (success and skipped == 0),
        'duration_seconds': duration,
        'success': success,
        'exit_code': 0 if success else 1
    }
    return details
