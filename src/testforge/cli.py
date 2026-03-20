"""TestForge CLI -- main entry point for all commands."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from testforge import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="testforge")
def cli() -> None:
    """TestForge -- LLM-powered QA automation platform."""


@cli.command()
@click.argument("name")
@click.option("--directory", "-d", type=click.Path(), default=".", help="Parent directory.")
def init(name: str, directory: str) -> None:
    """Create a new TestForge project."""
    from testforge.core.project import create_project

    project_dir = Path(directory) / name
    create_project(project_dir)
    console.print(f"[green]Project created:[/green] {project_dir}")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--input", "-i", "inputs", multiple=True, help="Input files or URLs to analyze.")
def analyze(project: str, inputs: tuple[str, ...]) -> None:
    """Analyze input documents and extract features."""
    from testforge.analysis.analyzer import run_analysis

    results = run_analysis(Path(project), list(inputs))
    console.print(f"[green]Analysis complete:[/green] {len(results)} features extracted")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--type", "-t", "case_type", default="all", help="Test case type: functional, usecase, checklist, all.")
def generate(project: str, case_type: str) -> None:
    """Generate test cases from analysis results."""
    from testforge.cases.generator import generate_cases

    cases = generate_cases(Path(project), case_type)
    console.print(f"[green]Generated:[/green] {len(cases)} test cases")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--framework", "-f", default="playwright", help="Script framework: playwright.")
def script(project: str, framework: str) -> None:
    """Generate automation scripts from test cases."""
    from testforge.scripts.generator import generate_scripts

    scripts = generate_scripts(Path(project), framework)
    console.print(f"[green]Generated:[/green] {len(scripts)} scripts ({framework})")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--tags", "-t", multiple=True, help="Filter tests by tags.")
@click.option("--parallel", "-p", type=int, default=1, help="Parallel workers.")
def run(project: str, tags: tuple[str, ...], parallel: int) -> None:
    """Execute test scripts and collect evidence."""
    from testforge.execution.runner import run_tests

    results = run_tests(Path(project), list(tags), parallel)
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = len(results) - passed
    console.print(f"[green]Passed:[/green] {passed}  [red]Failed:[/red] {failed}")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--format", "-f", "fmt", default="markdown", help="Report format: markdown, html.")
@click.option("--output", "-o", type=click.Path(), help="Output path.")
def report(project: str, fmt: str, output: str | None) -> None:
    """Generate test reports from execution results."""
    from testforge.report.generator import generate_report

    path = generate_report(Path(project), fmt, output)
    console.print(f"[green]Report generated:[/green] {path}")


@cli.command()
def projects() -> None:
    """List all TestForge projects."""
    from testforge.core.project import list_projects

    project_list = list_projects()
    if not project_list:
        console.print("[yellow]No projects found.[/yellow]")
        return
    for p in project_list:
        console.print(f"  {p}")
