import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from app import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="prism")
def cli() -> None:
    """Prism - DSPy Multi-Agent Code Review Platform"""


@cli.command()
@click.option("--owner", required=True, help="Repository owner")
@click.option("--repo", required=True, help="Repository name")
@click.option("--pr-number", required=True, type=int, help="PR number")
@click.option("--scm-token", envvar="SCM_GITHUB_TOKEN", help="GitHub token")
@click.option("--scm-provider", default="github", help="SCM provider")
@click.option("--hitl/--no-hitl", default=True, help="Enable human-in-the-loop")
@click.option("--model", default="gpt-4o", help="LLM model name")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file path")
def review(
    owner: str,
    repo: str,
    pr_number: int,
    scm_token: str | None,
    scm_provider: str,
    hitl: bool,
    model: str,
    output: str | None,
) -> None:
    """Review a pull request."""
    if not scm_token:
        console.print("[red]Error: SCM token required. Set SCM_GITHUB_TOKEN or use --scm-token[/red]")
        sys.exit(1)

    console.print(f"[bold blue]Reviewing PR {owner}/{repo}#{pr_number}...[/bold blue]")

    result = asyncio.run(
        _run_review(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            scm_token=scm_token,
            scm_provider=scm_provider,
            hitl_enabled=hitl,
            llm_model=model,
        )
    )

    if output:
        Path(output).write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        console.print(f"[green]Report saved to {output}[/green]")
    else:
        _print_review_summary(result)


async def _run_review(
    owner: str,
    repo: str,
    pr_number: int,
    scm_token: str,
    scm_provider: str,
    hitl_enabled: bool,
    llm_model: str,
) -> dict:
    """Run the review pipeline."""
    from app.graph.builder import get_graph
    from app.graph.state import create_initial_state

    graph = get_graph()
    initial_state = create_initial_state(
        owner=owner,
        repo=repo,
        pr_number=pr_number,
        scm_token=scm_token,
        scm_provider=scm_provider,
        hitl_enabled=hitl_enabled,
        llm_model=llm_model,
    )

    result = await graph.ainvoke(initial_state)
    return dict(result)


def _print_review_summary(result: dict) -> None:
    """Print review summary to console."""
    table = Table(title="Review Summary")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Summary", result.get("summary", "N/A"))
    table.add_row("Approved", str(result.get("approved", False)))

    critical = result.get("critical_findings", [])
    major = result.get("major_findings", [])
    minor = result.get("minor_findings", [])

    table.add_row("Critical", str(len(critical)))
    table.add_row("Major", str(len(major)))
    table.add_row("Minor", str(len(minor)))

    console.print(table)

    if critical:
        console.print("\n[bold red]Critical Findings:[/bold red]")
        for finding in critical:
            console.print(f"  - {finding.get('finding', 'N/A')}")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8000, type=int, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the Prism API server."""
    import uvicorn

    console.print(f"[bold blue]Starting Prism server on {host}:{port}...[/bold blue]")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@cli.command()
def version() -> None:
    """Show Prism version."""
    console.print(f"Prism v{__version__}")


if __name__ == "__main__":
    cli()
