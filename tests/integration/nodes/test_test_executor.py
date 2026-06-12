import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.core.models import Language, TestResult
from app.graph.nodes.test_executor import (
    _merge_results,
    _parse_coverage_json,
    _parse_ctest_output,
    _parse_junit_xml,
    _parse_maven_output,
    _parse_pytest_output,
    _run_pytest,
    run_test_suites,
)


class TestParsePytestOutput:
    def test_parse_standard_output(self):
        stdout = b"5 passed, 2 failed, 1 skipped in 1.23s"
        result = _parse_pytest_output(1, stdout, b"")
        assert result.framework == "pytest"
        assert result.total == 8
        assert result.passed == 5
        assert result.failed == 2
        assert result.skipped == 1

    def test_parse_all_passed(self):
        stdout = b"10 passed in 0.5s"
        result = _parse_pytest_output(0, stdout, b"")
        assert result.total == 10
        assert result.passed == 10
        assert result.failed == 0

    def test_parse_no_tests(self):
        stdout = b"no tests ran"
        result = _parse_pytest_output(0, stdout, b"")
        assert result.total == 0
        assert result.passed == 0

    def test_parse_failure_details(self):
        stdout = b"FAILED tests/test_app.py::test_login - AssertionError\n2 passed, 1 failed"
        result = _parse_pytest_output(1, stdout, b"")
        assert result.failed == 1
        assert len(result.failures) == 1
        assert result.failures[0]["test"] == "test_login"


class TestParseJunitXml:
    def test_parse_valid_xml(self, tmp_path):
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <testsuites>
            <testsuite name="pytest" tests="3" failures="1" skipped="0">
                <testcase classname="test_app" name="test_login" time="0.1"/>
                <testcase classname="test_app" name="test_logout" time="0.2">
                    <failure message="assertion failed">Details here</failure>
                </testcase>
                <testcase classname="test_app" name="test_register" time="0.3"/>
            </testsuite>
        </testsuites>"""
        path = tmp_path / "results.xml"
        path.write_text(xml_content)
        result = _parse_junit_xml(str(path))
        assert result is not None
        assert result.framework == "junit"
        assert result.total == 3
        assert result.failed == 1
        assert result.passed == 2
        assert len(result.failures) == 1
        assert result.failures[0]["test"] == "test_logout"

    def test_parse_nonexistent_file(self):
        result = _parse_junit_xml("/nonexistent/path.xml")
        assert result is None

    def test_parse_invalid_xml(self, tmp_path):
        path = tmp_path / "bad.xml"
        path.write_text("not xml at all")
        result = _parse_junit_xml(str(path))
        assert result is None


class TestParseCoverageJson:
    def test_parse_valid_coverage(self, tmp_path):
        data = {"totals": {"percent_covered": 87.5}}
        path = tmp_path / "coverage.json"
        path.write_text(json.dumps(data))
        result = _parse_coverage_json(str(path))
        assert result == 87.5

    def test_parse_no_totals(self, tmp_path):
        path = tmp_path / "coverage.json"
        path.write_text(json.dumps({}))
        result = _parse_coverage_json(str(path))
        assert result is None

    def test_parse_nonexistent_file(self):
        result = _parse_coverage_json("/nonexistent/coverage.json")
        assert result is None

    def test_parse_invalid_json(self, tmp_path):
        path = tmp_path / "coverage.json"
        path.write_text("not json")
        result = _parse_coverage_json(str(path))
        assert result is None


class TestParseMavenOutput:
    def test_parse_standard_output(self):
        stdout = b"Tests run: 10, Failures: 2, Errors: 0, Skipped: 1"
        result = _parse_maven_output(1, stdout)
        assert result.framework == "maven"
        assert result.total == 10
        assert result.failed == 2
        assert result.skipped == 1
        assert result.passed == 7

    def test_parse_with_errors(self):
        stdout = b"Tests run: 5, Failures: 0, Errors: 1, Skipped: 0"
        result = _parse_maven_output(1, stdout)
        assert result.failed == 1
        assert result.passed == 4

    def test_parse_no_tests(self):
        stdout = b"BUILD SUCCESS"
        result = _parse_maven_output(0, stdout)
        assert result.total == 0


class TestParseCtestOutput:
    def test_parse_standard_output(self):
        stdout = b"  Passed\n  Passed\n  Failed\n  Not Run\n"
        result = _parse_ctest_output(1, stdout)
        assert result.framework == "ctest"
        assert result.total == 4
        assert result.passed == 2
        assert result.failed == 1
        assert result.skipped == 1


class TestMergeResults:
    def test_merge_multiple_results(self):
        r1 = TestResult(framework="pytest", total=10, passed=8, failed=1, skipped=1, coverage=85.0)
        r2 = TestResult(framework="maven", total=5, passed=4, failed=1, skipped=0)
        merged = _merge_results([r1, r2])
        assert merged.total == 15
        assert merged.passed == 12
        assert merged.failed == 2
        assert merged.skipped == 1
        assert merged.coverage == 85.0
        assert "pytest" in merged.framework
        assert "maven" in merged.framework

    def test_merge_single_result(self):
        r1 = TestResult(framework="pytest", total=5, passed=5, coverage=92.0)
        merged = _merge_results([r1])
        assert merged.total == 5
        assert merged.passed == 5
        assert merged.coverage == 92.0

    def test_merge_empty_results(self):
        merged = _merge_results([])
        assert merged.total == 0
        assert merged.framework == "none"


class TestRunTestSuites:
    @pytest.mark.asyncio
    async def test_no_languages(self):
        state = {"languages": [], "project_key": "TEST"}
        settings = Settings()
        result = await run_test_suites(state, settings)
        assert result["test_results"].framework == "none"

    @pytest.mark.asyncio
    async def test_python_language(self):
        state = {"languages": [Language.PYTHON], "project_key": "TEST"}
        settings = Settings()
        with patch("app.graph.nodes.test_executor._run_pytest") as mock_pytest:
            mock_pytest.return_value = TestResult(framework="pytest", total=5, passed=5, coverage=90.0)
            result = await run_test_suites(state, settings)
            assert result["test_results"].passed == 5
            assert result["test_results"].coverage == 90.0
            mock_pytest.assert_called_once()

    @pytest.mark.asyncio
    async def test_java_language(self):
        state = {"languages": [Language.JAVA], "project_key": "TEST"}
        settings = Settings()
        with patch("app.graph.nodes.test_executor._run_maven_test") as mock_maven:
            mock_maven.return_value = TestResult(framework="maven", total=10, passed=9, failed=1)
            result = await run_test_suites(state, settings)
            assert result["test_results"].failed == 1

    @pytest.mark.asyncio
    async def test_unknown_language(self):
        state = {"languages": [Language.UNKNOWN], "project_key": "TEST"}
        settings = Settings()
        result = await run_test_suites(state, settings)
        assert result["test_results"].framework == "none"

    @pytest.mark.asyncio
    async def test_coverage_threshold_enforced(self):
        state = {"languages": [Language.PYTHON], "owner": "TEST", "repo": "repo"}
        settings = Settings()
        settings.test.project_thresholds = {"TEST/repo": 80.0}
        with patch("app.graph.nodes.test_executor._run_pytest") as mock_pytest:
            mock_pytest.return_value = TestResult(framework="pytest", total=5, passed=5, coverage=60.0)
            result = await run_test_suites(state, settings)
            tr = result["test_results"]
            assert tr.coverage == 60.0
            assert tr.coverage_threshold == 80.0
            assert tr.coverage_passed is False

    @pytest.mark.asyncio
    async def test_coverage_above_threshold(self):
        state = {"languages": [Language.PYTHON], "owner": "TEST", "repo": "repo"}
        settings = Settings()
        settings.test.project_thresholds = {"TEST/repo": 80.0}
        with patch("app.graph.nodes.test_executor._run_pytest") as mock_pytest:
            mock_pytest.return_value = TestResult(framework="pytest", total=5, passed=5, coverage=95.0)
            result = await run_test_suites(state, settings)
            assert result["test_results"].coverage_passed is True


class TestRunPytest:
    @pytest.mark.asyncio
    async def test_pytest_timeout(self):
        settings = Settings()
        settings.test.timeout = 1
        with patch("asyncio.create_subprocess_exec") as mock_proc:
            mock_proc.return_value = AsyncMock()
            mock_proc.return_value.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
            result = await _run_pytest(settings)
            assert result.failed == 1
            assert "timed out" in result.failures[0]["message"].lower()

    @pytest.mark.asyncio
    async def test_pytest_not_found(self):
        settings = Settings()
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await _run_pytest(settings)
            assert result.failed == 1
            assert "not found" in result.failures[0]["message"].lower()

    @pytest.mark.asyncio
    async def test_pytest_success(self):
        settings = Settings()
        with patch("asyncio.create_subprocess_exec") as mock_proc:
            proc_mock = AsyncMock()
            proc_mock.returncode = 0
            proc_mock.communicate = AsyncMock(return_value=(b"3 passed in 0.1s", b""))
            mock_proc.return_value = proc_mock
            with patch("app.graph.nodes.test_executor._parse_junit_xml", return_value=None):
                with patch("app.graph.nodes.test_executor._parse_coverage_json", return_value=None):
                    result = await _run_pytest(settings)
                    assert result.passed == 3
                    assert result.failed == 0
