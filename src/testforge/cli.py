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
@click.option("--use-cases", "use_cases", is_flag=True, default=False, help="Generate use case scenarios.")
@click.option("--checklists", is_flag=True, default=False, help="Generate manual test checklists.")
@click.pass_context
def generate(ctx: click.Context, project: str, case_type: str, use_cases: bool, checklists: bool) -> None:
    """Generate test cases from analysis results."""
    from testforge.cases.generator import generate_cases

    non_interactive: bool = ctx.obj.get("non_interactive", False) if ctx.obj else False

    # --use-cases / --checklists flags override the --type option
    if use_cases and checklists:
        effective_type = "all"
    elif use_cases:
        effective_type = "usecase"
    elif checklists:
        effective_type = "checklist"
    else:
        effective_type = case_type

    if non_interactive:
        console.print("[dim]--non-interactive: auto-approving generation without prompts.[/dim]")

    cases = generate_cases(Path(project), effective_type)
    if not cases:
        console.print("[yellow]No cases generated. Run 'testforge analyze' first.[/yellow]")
        return
    console.print(f"[green]Generated:[/green] {len(cases)} test cases ({effective_type})")


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
def coverage(project: str) -> None:
    """Show feature and rule coverage for a project."""
    from testforge.core.config import load_config

    project_dir = Path(project)
    config = load_config(project_dir)

    analysis_path = project_dir / config.analysis_dir / "analysis.json"
    cases_path = project_dir / config.cases_dir / "cases.json"

    if not analysis_path.exists():
        console.print("[yellow]No analysis results found. Run 'testforge analyze' first.[/yellow]")
        raise SystemExit(1)

    if not cases_path.exists():
        console.print("[yellow]No test cases found. Run 'testforge generate' first.[/yellow]")
        raise SystemExit(1)

    from testforge.coverage.tracker import compute_coverage

    report = compute_coverage(analysis_path, cases_path)

    console.print("\n[bold]Coverage Report[/bold]")
    console.print(f"  Features: {report.covered_features}/{report.total_features} ({report.feature_coverage_pct:.0f}%)")
    console.print(f"  Rules:    {report.covered_rules}/{report.total_rules} ({report.rule_coverage_pct:.0f}%)")

    if report.uncovered_features:
        console.print(f"\n[yellow]Uncovered features:[/yellow] {', '.join(report.uncovered_features)}")
    if report.uncovered_rules:
        console.print(f"[yellow]Uncovered rules:[/yellow] {', '.join(report.uncovered_rules)}")

    if not report.uncovered_features and not report.uncovered_rules:
        console.print("\n[green]Full coverage achieved.[/green]")


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


@cli.group()
@click.pass_context
def manual(ctx: click.Context) -> None:
    """Manual test checklist workflow commands."""
    non_interactive: bool = ctx.obj.get("non_interactive", False) if ctx.obj else False
    if non_interactive:
        console.print(
            "[yellow]Warning: --non-interactive has no effect on manual checklist commands "
            "(human verification is required).[/yellow]"
        )


@manual.command("start")
@click.argument("project", type=click.Path(exists=True))
def manual_start(project: str) -> None:
    """Start a manual test checklist session."""
    from testforge.cases.checklist import start_session

    session = start_session(Path(project))
    console.print(f"[green]Session started:[/green] {session.session_id}")
    console.print(f"  Items: {len(session.items)}")
    console.print(f"  State saved to: {project}/.testforge/manual/active-session.json")


@manual.command("check")
@click.argument("project", type=click.Path(exists=True))
@click.argument("item_id")
@click.option("--status", "-s", default="pass", type=click.Choice(["pass", "fail"]), help="pass or fail.")
@click.option("--note", "-n", default="", help="Optional tester note.")
def manual_check(project: str, item_id: str, status: str, note: str) -> None:
    """Record pass/fail for a checklist item."""
    from testforge.cases.checklist import check_item

    try:
        session = check_item(Path(project), item_id, status, note)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1)

    checked = len(session.results)
    total = len(session.items)
    console.print(f"[green]Checked:[/green] {item_id} -> {status}  ({checked}/{total})")


@manual.command("progress")
@click.argument("project", type=click.Path(exists=True))
def manual_progress(project: str) -> None:
    """Show progress of the active manual test session."""
    from testforge.cases.checklist import session_progress

    try:
        prog = session_progress(Path(project))
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1)

    console.print(f"Progress: {prog['checked']}/{prog['total']} ({prog['percent']}%)")
    console.print(f"  Passed:  {prog['passed']}")
    console.print(f"  Failed:  {prog['failed']}")
    console.print(f"  Pending: {prog['pending']}")


@manual.command("finish")
@click.argument("project", type=click.Path(exists=True))
def manual_finish(project: str) -> None:
    """Finish the active session and save the final report."""
    from testforge.cases.checklist import finish_session

    try:
        report_path = finish_session(Path(project))
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1)

    console.print(f"[green]Session finished:[/green] {report_path}")


@cli.command()
@click.argument("project", type=click.Path(), required=False, default=None)
def tui(project: str | None) -> None:
    """Launch the interactive TUI interface."""
    try:
        from testforge.tui import run_tui
    except ImportError:
        console.print(
            "[red]The TUI requires 'textual'.[/red]\n"
            "Install it with:  pip install 'testforge[tui]'"
        )
        raise SystemExit(1)
    run_tui(project_path=project)


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
