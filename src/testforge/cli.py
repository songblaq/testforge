"""TestForge CLI -- main entry point for all commands."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from testforge import __version__

console = Console()


def _find_selftest_dir() -> Path | None:
    """Locate the bundled self-test directory for source and packaged installs."""
    cli_file = Path(__file__).resolve()
    candidates = [
        cli_file.parents[2] / "tests" / "selftest",
        cli_file.parent / "tests" / "selftest",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


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
@click.option(
    "--no-llm",
    is_flag=True,
    default=False,
    help="Force offline mode -- skip all LLM calls and suppress LLM warnings.",
    expose_value=False,
    is_eager=True,
    callback=lambda ctx, _param, value: ctx.ensure_object(dict).__setitem__("no_llm", value),
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
@click.pass_context
def analyze(ctx: click.Context, project: str, inputs: tuple[str, ...]) -> None:
    """Analyze input documents and extract features."""
    from testforge.analysis.analyzer import run_analysis

    no_llm: bool = ctx.obj.get("no_llm", False) if ctx.obj else False

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

    results = run_analysis(Path(project), list(inputs), no_llm=no_llm)
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
    no_llm: bool = ctx.obj.get("no_llm", False) if ctx.obj else False

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

    cases = generate_cases(Path(project), effective_type, no_llm=no_llm)
    if not cases:
        console.print("[yellow]No cases generated. Run 'testforge analyze' first.[/yellow]")
        return
    console.print(f"[green]Generated:[/green] {len(cases)} test cases ({effective_type})")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--framework", "-f", default="playwright", help="Script framework: playwright.")
@click.pass_context
def script(ctx: click.Context, project: str, framework: str) -> None:
    """Generate automation scripts from test cases."""
    from testforge.scripts.generator import generate_scripts

    no_llm: bool = ctx.obj.get("no_llm", False) if ctx.obj else False
    scripts = generate_scripts(Path(project), framework, no_llm=no_llm)
    console.print(f"[green]Generated:[/green] {len(scripts)} scripts ({framework})")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--tags", "-t", multiple=True, help="Filter tests by tags.")
@click.option("--parallel", "-p", type=int, default=1, help="Parallel workers.")
@click.option(
    "--engine",
    "-e",
    "engines",
    multiple=True,
    help="Execution engine(s): playwright, expect, agent-browser. Repeatable. Defaults to project config.",
)
@click.option(
    "--cross-validate",
    is_flag=True,
    default=None,
    help="Enable cross-validation across engines.",
)
def run(
    project: str,
    tags: tuple[str, ...],
    parallel: int,
    engines: tuple[str, ...],
    cross_validate: bool | None,
) -> None:
    """Execute test scripts and collect evidence."""
    import json
    from datetime import datetime, timezone

    from testforge.core.config import load_config
    from testforge.execution.runner import run_tests

    config = load_config(Path(project))
    active_engines = list(engines) if engines else config.execution_engines
    cv_enabled = cross_validate if cross_validate is not None else config.cross_validation

    results = run_tests(
        Path(project),
        list(tags),
        parallel,
        engines=active_engines,
        engine_configs=config.engine_configs,
        cross_validate_enabled=cv_enabled,
    )

    cv_rows = [r for r in results if r.get("case_id") == "__cross_validation__"]
    test_rows = [r for r in results if r.get("case_id") != "__cross_validation__"]
    passed = sum(1 for r in test_rows if r.get("status") == "passed")
    failed = sum(1 for r in test_rows if r.get("status") == "failed")
    skipped = len(test_rows) - passed - failed

    # Persist results so `testforge report` can read them
    output_dir = Path(project) / config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    results_data = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "summary": {"total": len(test_rows), "passed": passed, "failed": failed},
    }
    results_path = output_dir / "results.json"
    results_path.write_text(json.dumps(results_data, indent=2, ensure_ascii=False))

    console.print(f"[green]Passed:[/green] {passed}  [red]Failed:[/red] {failed}  [dim]Skipped:[/dim] {skipped}")
    if active_engines != ["playwright"]:
        console.print(f"  Engines: {', '.join(active_engines)}")
    for cv in cv_rows:
        console.print(f"  [bold]Cross-validation:[/bold] {cv.get('agreed', 0)} agree, {cv.get('disagreed', 0)} disagree")

    console.print(f"  Results saved to: {results_path}")

    if failed > 0:
        top_failures = [r["case_id"] for r in test_rows if r.get("status") == "failed"][:5]
        console.print(f"\n[yellow]Top failures:[/yellow] {', '.join(top_failures)}")
        console.print("[dim]Run 'testforge report <project>' to generate a detailed report.[/dim]")
        raise SystemExit(1)


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

    console.print("\n[bold]Traceability Coverage Report[/bold]")
    console.print("[dim](Measures whether test cases reference each feature/rule, NOT execution pass rate)[/dim]")
    console.print(f"  Features: {report.covered_features}/{report.total_features} ({report.feature_coverage_pct:.0f}%)")
    console.print(f"  Rules:    {report.covered_rules}/{report.total_rules} ({report.rule_coverage_pct:.0f}%)")

    if report.uncovered_features:
        console.print(f"\n[yellow]Uncovered features:[/yellow] {', '.join(report.uncovered_features)}")
    if report.uncovered_rules:
        console.print(f"[yellow]Uncovered rules:[/yellow] {', '.join(report.uncovered_rules)}")

    if not report.uncovered_features and not report.uncovered_rules:
        console.print("\n[green]All features and rules are mapped to test cases.[/green]")

    # Show execution pass rate if results exist
    results_path = project_dir / config.output_dir / "results.json"
    if results_path.exists():
        import json
        with open(results_path) as f:
            results_data = json.load(f)
        summary = results_data.get("summary", {})
        total = summary.get("total", 0)
        p = summary.get("passed", 0)
        if total > 0:
            console.print(f"\n[bold]Execution Pass Rate:[/bold] {p}/{total} ({p/total*100:.0f}%)")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--stages", "-s", multiple=True, help="Pipeline stages to run.")
@click.option("--input", "-i", "inputs", multiple=True, help="Input files for analysis.")
@click.pass_context
def pipeline(ctx: click.Context, project: str, stages: tuple[str, ...], inputs: tuple[str, ...]) -> None:
    """Run the full TestForge pipeline end to end."""
    from testforge.core.pipeline import run_pipeline

    no_llm: bool = ctx.obj.get("no_llm", False) if ctx.obj else False
    result = run_pipeline(
        Path(project),
        stages=list(stages) if stages else None,
        inputs=list(inputs) if inputs else None,
        no_llm=no_llm,
    )

    if result.success:
        console.print(f"[green]Pipeline complete:[/green] {', '.join(result.stages_completed)}")
    else:
        console.print(f"[red]Pipeline failed:[/red] {'; '.join(result.errors)}")
        console.print(f"  Completed stages: {', '.join(result.stages_completed)}")


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--max-iter", default=3, type=int, help="Maximum research iterations.")
@click.option("--threshold", default=0.95, type=float, help="Target pass-rate threshold.")
@click.option(
    "--strategy",
    default="fix-failed",
    type=click.Choice(["fix-failed", "expand-coverage", "both"]),
    help="Research improvement strategy.",
)
@click.option(
    "--ledger-dir",
    type=click.Path(),
    default=None,
    help="Optional external directory for testforge-results.tsv.",
)
@click.option(
    "--plaza-runtime",
    default="",
    help="Optional runtime id for Plaza logging, e.g. codex or claude-code.",
)
@click.option("--input", "-i", "inputs", multiple=True, help="Input files for the initial analysis.")
@click.pass_context
def research(
    ctx: click.Context,
    project: str,
    max_iter: int,
    threshold: float,
    strategy: str,
    ledger_dir: str | None,
    plaza_runtime: str,
    inputs: tuple[str, ...],
) -> None:
    """Run the AutoResearch loop for a TestForge project."""
    from testforge.research.loop import run_research
    from testforge.research.loop import ResearchNoOpError

    no_llm: bool = ctx.obj.get("no_llm", False) if ctx.obj else False
    try:
        summary = run_research(
            Path(project),
            max_iterations=max_iter,
            threshold=threshold,
            strategy=strategy,
            inputs=list(inputs) if inputs else None,
            ledger_dir=Path(ledger_dir) if ledger_dir else None,
            plaza_runtime=plaza_runtime or None,
            no_llm=no_llm,
        )
    except ResearchNoOpError as exc:
        console.print(f"[red]Research no-op:[/red] {exc}")
        raise SystemExit(1)

    console.print(
        f"[green]Research complete:[/green] "
        f"iterations={len(summary.iterations)} "
        f"final_pass_rate={summary.final_pass_rate:.3f} "
        f"converged={summary.converged}"
    )


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
@click.pass_context
def manual_start(ctx: click.Context, project: str) -> None:
    """Start a manual test checklist session."""
    from testforge.cases.checklist import start_session

    no_llm: bool = ctx.obj.get("no_llm", False) if ctx.obj else False
    session = start_session(Path(project), no_llm=no_llm)
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
@click.option("--port", "-p", default=8000, help="Server port.")
@click.option("--host", "-h", default="127.0.0.1", help="Server host.")
def web(port: int, host: str) -> None:
    """Launch TestForge Web GUI."""
    try:
        import uvicorn
        from testforge.web.app import create_app
    except ImportError:
        console.print(
            "[red]The Web GUI requires 'fastapi' and 'uvicorn'.[/red]\n"
            "Install them with:  pip install 'testforge[web]'"
        )
        raise SystemExit(1)

    app = create_app()
    console.print(f"[green]TestForge Web GUI[/green] starting at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


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

    selftest_dir = _find_selftest_dir()
    if selftest_dir is None:
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
