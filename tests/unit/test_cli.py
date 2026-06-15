"""Unit tests for CLI commands."""
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from app import __version__
from app.cli import cli, review, serve, version, _print_review_summary


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


class TestReviewCommand:
    """Tests for the review command."""

    def test_review_missing_token(self, cli_runner: CliRunner) -> None:
        """Test review command without SCM token fails."""
        result = cli_runner.invoke(
            review,
            ["--owner", "test", "--repo", "repo", "--pr-number", "1"],
        )
        assert result.exit_code == 1
        assert "Error: SCM token required" in result.output

    @patch("app.cli._run_review")
    def test_review_with_token(self, mock_run: AsyncMock, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test review command with valid token."""
        mock_result = {
            "summary": "Test summary",
            "approved": True,
            "critical_findings": [],
            "major_findings": [],
            "minor_findings": [],
        }
        mock_run.return_value = mock_result

        result = cli_runner.invoke(
            review,
            ["--owner", "test", "--repo", "repo", "--pr-number", "1", "--scm-token", "token123"],
        )
        assert result.exit_code == 0

    @patch("app.cli._run_review")
    def test_review_with_output_file(self, mock_run: AsyncMock, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test review command saves output to JSON file."""
        output_file = tmp_path / "output.json"
        mock_result = {
            "summary": "Test summary",
            "approved": True,
            "critical_findings": [],
        }
        mock_run.return_value = mock_result

        result = cli_runner.invoke(
            review,
            [
                "--owner", "test",
                "--repo", "repo",
                "--pr-number", "1",
                "--scm-token", "token123",
                "--output", str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        assert json.loads(output_file.read_text())["summary"] == "Test summary"

    @patch("app.cli._run_review")
    def test_review_with_custom_model(self, mock_run: AsyncMock, cli_runner: CliRunner) -> None:
        """Test review command with custom LLM model."""
        mock_run.return_value = {"summary": "Test", "approved": True}

        result = cli_runner.invoke(
            review,
            [
                "--owner", "test",
                "--repo", "repo",
                "--pr-number", "1",
                "--scm-token", "token123",
                "--model", "gpt-4",
            ],
        )
        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["llm_model"] == "gpt-4"

    def test_review_with_hitl_disabled(self, cli_runner: CliRunner) -> None:
        """Test review command with HITL disabled."""
        with patch("app.cli._run_review") as mock_run:
            mock_run.return_value = {"summary": "Test", "approved": True}

            result = cli_runner.invoke(
                review,
                [
                    "--owner", "test",
                    "--repo", "repo",
                    "--pr-number", "1",
                    "--scm-token", "token123",
                    "--no-hitl",
                ],
            )
            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["hitl_enabled"] is False


class TestServeCommand:
    """Tests for the serve command."""

    def test_serve_default_args(self, cli_runner: CliRunner) -> None:
        """Test serve command with default arguments."""
        with patch("app.cli.uvicorn.run") as mock_run:
            result = cli_runner.invoke(serve, [])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_args, call_kwargs = mock_run.call_args
            assert call_args[0] == "app.main:app"
            assert call_kwargs["host"] == "0.0.0.0"
            assert call_kwargs["port"] == 8000
            assert call_kwargs["reload"] is False

    def test_serve_custom_host_port(self, cli_runner: CliRunner) -> None:
        """Test serve command with custom host and port."""
        with patch("app.cli.uvicorn.run") as mock_run:
            result = cli_runner.invoke(
                serve,
                ["--host", "127.0.0.1", "--port", "9000"],
            )
            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["host"] == "127.0.0.1"
            assert call_kwargs["port"] == 9000

    def test_serve_with_reload(self, cli_runner: CliRunner) -> None:
        """Test serve command with reload enabled."""
        with patch("app.cli.uvicorn.run") as mock_run:
            result = cli_runner.invoke(serve, ["--reload"])
            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["reload"] is True


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_output(self, cli_runner: CliRunner) -> None:
        """Test version command outputs correct version."""
        result = cli_runner.invoke(version)
        assert result.exit_code == 0
        assert __version__ in result.output
        assert "Prism" in result.output


class TestCliGroup:
    """Tests for CLI group behavior."""

    def test_cli_help(self, cli_runner: CliRunner) -> None:
        """Test CLI help text."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Prism" in result.output

    def test_cli_version_option(self, cli_runner: CliRunner) -> None:
        """Test CLI version option."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestPrintReviewSummary:
    """Tests for _print_review_summary helper."""

    @patch("app.cli.console.print")
    def test_print_review_summary_with_findings(self, mock_print) -> None:
        """Test printing review summary with findings."""
        result = {
            "summary": "All checks passed",
            "approved": True,
            "critical_findings": [{"finding": "Critical issue"}],
            "major_findings": [{"finding": "Major issue"}],
            "minor_findings": [{"finding": "Minor issue"}],
        }
        _print_review_summary(result)
        assert mock_print.call_count > 0

    @patch("app.cli.console.print")
    def test_print_review_summary_empty(self, mock_print) -> None:
        """Test printing review summary with no findings."""
        result = {
            "summary": "No issues",
            "approved": True,
            "critical_findings": [],
            "major_findings": [],
            "minor_findings": [],
        }
        _print_review_summary(result)
        assert mock_print.call_count > 0
