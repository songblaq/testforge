"""TestForge CLI -- main entry point for all commands."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from testforge import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="testforge")
@click.option(
    "--non-interactive",
    "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation prompts and auto-approve.",
    expose_value=False,
    is_eager=True,
    callback=lambda ctx, _param, value: ctx.ensure_object(dict).__setitem__("non_interactive", value),
)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """TestForge -- LLM-powered QA automation platform."""
    ctx.ensure_object(dict)


@cli.command()
@click.argument("name")
@click.option("--directory", "-d", type=click.Path(), default=".", help="Parent directory.")
@click.option("--provider", "-p", default="anthropic", help="LLM provider: anthropic, openai, cli.")
@click.option("--model", "-m", default="", help="LLM model name.")
def init(name: str, directory: str, provider: str, model: str) -> None:
    """Create a new TestForge project."""
    from testforge.core.config import TestForgeConfig, save_config
    from testforge.core.project import create_project

    project_dir = Path(directory) / name
    create_project(project_dir)

    # Update config with user-specified LLM settings
    if provider != "anthropic" or model:
        config = TestForgeConfig(
            project_name=name,
            llm_provider=provider,
            llm_model=model,
        )
        save_config(project_dir, config)

    console.print(f"[green]Project created:[/green] {project_dir}")
    console.print(f"  LLM provider: {provider}")
    if model:
        console.print(f"  LLM model: {model}")
    console.print(f"  Config: {project_dir / '.testforge' / 'config.yaml'}")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--input", "-i", "inputs", multiple=True, help="Input files or URLs to analyze.")
def analyze(project: str, inputs: tuple[str, ...]) -> None:
    """Analyze input documents and extract features."""
    from testforge.analysis.analyzer import run_analysis

    if not inputs:
        # Auto-discover files in project inputs/ directory
        from testforge.core.config import load_config

        config = load_config(Path(project))
        input_dir = Path(project) / config.input_dir
        if input_dir.exists():
            discovered = [
                str(f) for f in input_dir.iterdir()
                if f.is_file() and not f.name.startswith(".")
            ]
            if discovered:
                console.print(f"[dim]Auto-discovered {len(discovered)} input file(s)[/dim]")
                inputs = tuple(discovered)

    if not inputs:
        console.print("[yellow]No input files specified. Use -i or place files in inputs/ directory.[/yellow]")
        return

    results = run_analysis(Path(project), list(inputs))
    total_features = sum(len(r.get("features", [])) for r in results)
    console.print(f"[green]Analysis complete:[/green] {len(results)} source(s), {total_features} features extracted")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--type", "-t", "case_type", default="all", help="Test case type: functional, usecase, checklist, all.")
def generate(project: str, case_type: str) -> None:
    """Generate test cases from analysis results."""
    from testforge.cases.generator import generate_cases

    cases = generate_cases(Path(project), case_type)
    if not cases:
        console.print("[yellow]No cases generated. Run 'testforge analyze' first.[/yellow]")
        return
    console.print(f"[green]Generated:[/green] {len(cases)} test cases ({case_type})")


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
@click.argument("project", type=click.Path(exists=True))
@click.option("--stages", "-s", multiple=True, help="Pipeline stages to run.")
@click.option("--input", "-i", "inputs", multiple=True, help="Input files for analysis.")
def pipeline(project: str, stages: tuple[str, ...], inputs: tuple[str, ...]) -> None:
    """Run the full TestForge pipeline end to end."""
    from testforge.core.pipeline import run_pipeline

    result = run_pipeline(
        Path(project),
        stages=list(stages) if stages else None,
        inputs=list(inputs) if inputs else None,
    )

    if result.success:
        console.print(f"[green]Pipeline complete:[/green] {', '.join(result.stages_completed)}")
    else:
        console.print(f"[red]Pipeline failed:[/red] {'; '.join(result.errors)}")
        console.print(f"  Completed stages: {', '.join(result.stages_completed)}")


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


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Show stdout/stderr for each script.")
def selftest(verbose: bool) -> None:
    """Run built-in self-test suite against the installed TestForge."""
    import subprocess

    # Locate the selftest scripts directory relative to this file
    selftest_dir = Path(__file__).parent.parent.parent.parent / "tests" / "selftest"
    if not selftest_dir.exists():
        # Fallback: look relative to package install root
        selftest_dir = Path(__file__).parent / "tests" / "selftest"

    if not selftest_dir.exists():
        console.print("[yellow]No selftest directory found. Expected: tests/selftest/[/yellow]")
        raise SystemExit(0)

    scripts = sorted(selftest_dir.glob("*.sh"))
    if not scripts:
        console.print("[yellow]No selftest scripts found in tests/selftest/[/yellow]")
        raise SystemExit(0)

    passed: list[str] = []
    failed: list[str] = []

    for script in scripts:
        console.print(f"  [dim]running[/dim] {script.name} ...", end=" ")
        proc = subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            console.print("[green]PASS[/green]")
            passed.append(script.name)
        else:
            console.print("[red]FAIL[/red]")
            failed.append(script.name)

        if verbose:
            if proc.stdout:
                console.print(proc.stdout.rstrip())
            if proc.stderr:
                console.print(f"[red]{proc.stderr.rstrip()}[/red]")

    total = len(passed) + len(failed)
    console.print(f"\n[bold]Results:[/bold] {len(passed)}/{total} passed", end="")
    if failed:
        console.print(f"  [red]Failed: {', '.join(failed)}[/red]")
    else:
        console.print("  [green]All tests passed.[/green]")

    raise SystemExit(1 if failed else 0)
