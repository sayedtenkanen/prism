from click.testing import CliRunner

from app.cli import cli


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "Prism" in result.output


def test_cli_review_missing_token() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["review", "--owner", "test", "--repo", "repo", "--pr-number", "1"],
    )
    assert result.exit_code != 0
    assert "SCM token required" in result.output or result.exit_code == 1


def test_cli_review_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["review", "--help"])
    assert result.exit_code == 0
    assert "--owner" in result.output
    assert "--repo" in result.output
    assert "--pr-number" in result.output


def test_cli_serve_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert "--host" in result.output
    assert "--port" in result.output


def test_cli_group() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Prism" in result.output
