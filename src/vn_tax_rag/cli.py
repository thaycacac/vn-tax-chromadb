from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from vn_tax_rag.config import load_settings
from vn_tax_rag.crawl.pipeline import run_crawl
from vn_tax_rag.crawl.seeds import load_seeds
from vn_tax_rag.ingest.pipeline import run_ingest
from vn_tax_rag.logging_setup import setup_logging
from vn_tax_rag.rag.pipeline import run_ask
from vn_tax_rag.rag.store import collection_exists, get_collection

app = typer.Typer(
    name="vn-tax",
    help="Vietnamese tax law RAG CLI (crawl, ingest, ask).",
    add_completion=False,
    no_args_is_help=True,
)


def _bootstrap(
    verbose: bool,
    log_file: Optional[Path],
):
    log = setup_logging(verbose=verbose, log_file=log_file)
    settings = load_settings()
    return settings, log


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable DEBUG logs."),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Also write logs to this file."
    ),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["log_file"] = log_file


@app.command("crawl")
def crawl_cmd(ctx: typer.Context) -> None:
    """Fetch seed tax-law pages and write cleaned text under data/processed."""
    settings, log = _bootstrap(ctx.obj["verbose"], ctx.obj["log_file"])
    summary = run_crawl(settings, log)
    typer.echo(f"Crawl finished: {summary}")


@app.command("ingest")
def ingest_cmd(ctx: typer.Context) -> None:
    """Chunk processed documents and upsert into ChromaDB."""
    settings, log = _bootstrap(ctx.obj["verbose"], ctx.obj["log_file"])
    summary = run_ingest(settings, log)
    typer.echo(f"Ingest finished: {summary}")


@app.command("ask")
def ask_cmd(
    ctx: typer.Context,
    question: str = typer.Argument(..., help="Natural-language tax question."),
    tax_type: Optional[str] = typer.Option(
        None,
        "--tax-type",
        "-t",
        help="Filter metadata tax_type (TNCN, GTGT, TNDN, ADMIN).",
    ),
    n_results: int = typer.Option(4, "--n-results", "-n", help="Top-k chunks to retrieve."),
    show_context: bool = typer.Option(
        False, "--show-context", help="Print retrieved context before the answer."
    ),
) -> None:
    """Retrieve relevant passages and generate an answer with a local/remote LLM."""
    settings, log = _bootstrap(ctx.obj["verbose"], ctx.obj["log_file"])
    run_ask(
        settings,
        log,
        question=question,
        n_results=n_results,
        tax_type=tax_type,
        show_context=show_context,
    )


@app.command("status")
def status_cmd(ctx: typer.Context) -> None:
    """Show paths, seed counts, processed files, and collection size."""
    settings, log = _bootstrap(ctx.obj["verbose"], ctx.obj["log_file"])
    log.step("status.start")

    seeds = load_seeds(settings.seeds_path) if settings.seeds_path.exists() else []
    processed = (
        list(settings.processed_dir.glob("*.txt")) if settings.processed_dir.exists() else []
    )
    raw_dirs = list(settings.raw_dir.iterdir()) if settings.raw_dir.exists() else []

    count = 0
    exists = collection_exists(settings)
    if exists:
        count = get_collection(settings).count()

    typer.echo("vn-tax status")
    typer.echo(f"  project_root : {settings.project_root}")
    typer.echo(f"  chroma_path  : {settings.chroma_path}")
    typer.echo(f"  data_dir     : {settings.data_dir}")
    typer.echo(f"  seeds        : {len(seeds)} ({settings.seeds_path})")
    typer.echo(f"  raw dirs     : {len(raw_dirs)}")
    typer.echo(f"  processed    : {len(processed)}")
    typer.echo(f"  collection   : {settings.collection_name} exists={exists} count={count}")
    typer.echo(f"  embedding    : {settings.embedding_model}")
    typer.echo(f"  llm_model    : {settings.llm_model}")
    typer.echo(f"  llm_base_url : {settings.llm_base_url}")
    log.step("status.done")


if __name__ == "__main__":
    app()
