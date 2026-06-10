import asyncio
import json
import re
import xml.etree.ElementTree as ET
from typing import Any, Optional

from app.core.config import Settings
from app.core.models import Language, TestResult
from app.graph.state import PRReviewState


async def run_test_suites(state: PRReviewState, settings: Settings) -> dict[str, Any]:
    """Execute test suites and collect results with coverage analysis.

    Supports pytest (with --junitxml and --cov) and JUnit XML parsing.
    Returns a TestResult with pass/fail/skip counts, coverage, and failure details.
    """
    languages = state.get("languages", [])
    project_key = state.get("project_key", "")

    results: list[TestResult] = []

    for lang in languages:
        result = await _run_tests_for_language(lang, project_key, settings)
        results.append(result)

    if not results:
        return {"test_results": TestResult(framework="none")}

    # Merge results (aggregate across languages)
    merged = _merge_results(results)

    # Evaluate coverage thresholds
    primary_lang = languages[0] if languages else Language.PYTHON
    lang_name = primary_lang.value if isinstance(primary_lang, Language) else primary_lang
    threshold = settings.test.get_threshold(lang_name, project_key)
    merged.evaluate(threshold)

    return {"test_results": merged}


async def _run_tests_for_language(
    language: Language,
    project_key: str,
    settings: Settings,
) -> TestResult:
    """Run test suite for a specific language."""
    if language == Language.PYTHON:
        return await _run_pytest(settings)
    elif language == Language.JAVA:
        return await _run_maven_test(settings)
    elif language == Language.CPP:
        return await _run_cmake_test(settings)
    else:
        return TestResult(framework="none")


async def _run_pytest(settings: Settings) -> TestResult:
    """Run pytest with coverage and parse results."""
    timeout = settings.test.test_timeout

    # Run pytest with JUnit XML and coverage
    cmd = [
        "python",
        "-m",
        "pytest",
        "--junitxml=/tmp/prism-test-results.xml",
        "--cov=app",
        "--cov-report=json:/tmp/prism-coverage.json",
        "-v",
        "--tb=short",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return _parse_pytest_output(proc.returncode or 0, stdout, stderr)
    except asyncio.TimeoutError:
        return TestResult(
            framework="pytest",
            failed=1,
            failures=[{"message": f"Test execution timed out after {timeout}s"}],
        )
    except FileNotFoundError:
        return TestResult(
            framework="pytest",
            failed=1,
            failures=[{"message": "pytest not found. Install with: pip install pytest"}],
        )
    except Exception as e:
        return TestResult(
            framework="pytest",
            failed=1,
            failures=[{"message": f"Test execution error: {str(e)}"}],
        )


def _parse_pytest_output(
    returncode: int,
    stdout: bytes,
    stderr: bytes,
) -> TestResult:
    """Parse pytest output and JUnit XML to build TestResult."""
    output = stdout.decode("utf-8", errors="replace")
    failures: list[dict[str, Any]] = []

    # Try to parse JUnit XML first
    junit_result = _parse_junit_xml("/tmp/prism-test-results.xml")
    if junit_result:
        return junit_result

    # Fall back to parsing stdout
    # Pattern: "X passed, Y failed, Z skipped" or similar
    summary_pattern = r"(\d+)\s+passed.*?(\d+)\s+failed.*?(\d+)\s+skipped"
    match = re.search(summary_pattern, output)

    total = passed = failed = skipped = 0

    if match:
        passed = int(match.group(1))
        failed = int(match.group(2))
        skipped = int(match.group(3))
        total = passed + failed + skipped
    else:
        # Try simpler patterns
        passed_match = re.search(r"(\d+)\s+passed", output)
        failed_match = re.search(r"(\d+)\s+failed", output)
        skipped_match = re.search(r"(\d+)\s+skipped", output)

        if passed_match:
            passed = int(passed_match.group(1))
        if failed_match:
            failed = int(failed_match.group(1))
        if skipped_match:
            skipped = int(skipped_match.group(1))
        total = passed + failed + skipped

    # Extract failure details from output
    failure_blocks = re.findall(r"FAILED\s+(.+?)::(.+?)\s+-\s+(.+?)(?:\n|$)", output)
    for file_path, test_name, message in failure_blocks:
        failures.append(
            {
                "file": file_path,
                "test": test_name,
                "message": message.strip(),
            }
        )

    # Parse coverage
    coverage = _parse_coverage_json("/tmp/prism-coverage.json")

    return TestResult(
        framework="pytest",
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        coverage=coverage,
        failures=failures,
    )


def _parse_junit_xml(path: str) -> Optional[TestResult]:
    """Parse JUnit XML file."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()

        # Handle both <testsuites> and <testsuite> root elements
        if root.tag == "testsuites":
            testsuites = root.findall("testsuite")
        elif root.tag == "testsuite":
            testsuites = [root]
        else:
            return None

        total = passed = failed = skipped = 0
        failures: list[dict[str, Any]] = []

        for ts in testsuites:
            total += int(ts.get("tests", 0))
            failed += int(ts.get("failures", 0))
            skipped += int(ts.get("skipped", 0))

            for tc in ts.findall("testcase"):
                failure = tc.find("failure")
                if failure is not None:
                    failures.append(
                        {
                            "file": tc.get("classname", ""),
                            "test": tc.get("name", ""),
                            "message": failure.get("message", ""),
                        }
                    )
                error = tc.find("error")
                if error is not None:
                    failures.append(
                        {
                            "file": tc.get("classname", ""),
                            "test": tc.get("name", ""),
                            "message": error.get("message", ""),
                        }
                    )

        passed = total - failed - skipped

        return TestResult(
            framework="junit",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            failures=failures,
        )
    except (ET.ParseError, FileNotFoundError, OSError):
        return None


def _parse_coverage_json(path: str) -> Optional[float]:
    """Parse coverage JSON report from coverage.py."""
    try:
        with open(path) as f:
            data = json.load(f)
        # coverage.py JSON format has "totals" -> "percent_covered"
        totals = data.get("totals", {})
        percent = totals.get("percent_covered")
        if percent is not None:
            return round(float(percent), 2)
        return None
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return None


async def _run_maven_test(settings: Settings) -> TestResult:
    """Run Maven test suite."""
    timeout = settings.test.test_timeout
    cmd = ["mvn", "test", "-q"]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return _parse_maven_output(proc.returncode or 0, stdout)
    except (asyncio.TimeoutError, FileNotFoundError, Exception) as e:
        msg = str(e) if not isinstance(e, asyncio.TimeoutError) else f"Timed out after {timeout}s"
        return TestResult(
            framework="maven",
            failed=1,
            failures=[{"message": msg}],
        )


def _parse_maven_output(returncode: int, stdout: bytes) -> TestResult:
    """Parse Maven test output."""
    output = stdout.decode("utf-8", errors="replace")

    total_match = re.search(r"Tests run:\s*(\d+)", output)
    failures_match = re.search(r"Failures:\s*(\d+)", output)
    errors_match = re.search(r"Errors:\s*(\d+)", output)
    skipped_match = re.search(r"Skipped:\s*(\d+)", output)

    total = int(total_match.group(1)) if total_match else 0
    failed = (int(failures_match.group(1)) if failures_match else 0) + (
        int(errors_match.group(1)) if errors_match else 0
    )
    skipped = int(skipped_match.group(1)) if skipped_match else 0
    passed = total - failed - skipped

    return TestResult(
        framework="maven",
        total=total,
        passed=max(0, passed),
        failed=failed,
        skipped=skipped,
    )


async def _run_cmake_test(settings: Settings) -> TestResult:
    """Run CTest test suite."""
    timeout = settings.test.test_timeout
    cmd = ["ctest", "--output-on-failure"]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return _parse_ctest_output(proc.returncode or 0, stdout)
    except (asyncio.TimeoutError, FileNotFoundError, Exception) as e:
        msg = str(e) if not isinstance(e, asyncio.TimeoutError) else f"Timed out after {timeout}s"
        return TestResult(
            framework="ctest",
            failed=1,
            failures=[{"message": msg}],
        )


def _parse_ctest_output(returncode: int, stdout: bytes) -> TestResult:
    """Parse CTest output."""
    output = stdout.decode("utf-8", errors="replace")

    passed = len(re.findall(r"Passed", output))
    failed = len(re.findall(r"Failed", output))
    skipped = len(re.findall(r"Not Run", output))
    total = passed + failed + skipped

    return TestResult(
        framework="ctest",
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
    )


def _merge_results(results: list[TestResult]) -> TestResult:
    """Merge multiple TestResults into a single aggregated result."""
    total = sum(r.total for r in results)
    passed = sum(r.passed for r in results)
    failed = sum(r.failed for r in results)
    skipped = sum(r.skipped for r in results)
    all_failures = []
    for r in results:
        all_failures.extend(r.failures)

    # Use the first non-None coverage
    coverage = None
    for r in results:
        if r.coverage is not None:
            coverage = r.coverage
            break

    frameworks = list({r.framework for r in results if r.framework != "none"})

    return TestResult(
        framework="+".join(frameworks) if frameworks else "none",
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        coverage=coverage,
        failures=all_failures,
    )
