"""Tests for the TestForge CLI."""

from __future__ import annotations

from click.testing import CliRunner

from testforge.cli import cli


def test_version() -> None:
    """CLI --version prints the version string."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help() -> None:
    """CLI --help shows available commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "analyze" in result.output
    assert "generate" in result.output
    assert "report" in result.output


def test_init(tmp_path: str) -> None:
    """CLI init creates a project directory."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "demo", "-d", str(tmp_path)])
    assert result.exit_code == 0
    assert "Project created" in result.output


def test_projects_empty() -> None:
    """CLI projects with no projects shows empty message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["projects"])
    assert result.exit_code == 0


def test_selftest_command_exists() -> None:
    """testforge selftest --help is recognised as a valid command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["selftest", "--help"])
    assert result.exit_code == 0
    assert "self-test" in result.output.lower() or "selftest" in result.output.lower()


def test_non_interactive_flag() -> None:
    """--non-interactive / -y flag is recognised at the group level."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--non-interactive", "--help"])
    assert result.exit_code == 0

    result_short = runner.invoke(cli, ["-y", "--help"])
    assert result_short.exit_code == 0
