#!/usr/bin/env python
"""
📚 Knowledge Ingestion Pipeline

This script provides CLI commands to run document extraction and embedding in stages or together.

🔧 Usage:
    python scripts/pipeline.py extract        # Run only document extraction
    python scripts/pipeline.py embed          # Run only vector embedding
    python scripts/pipeline.py all            # Run full pipeline end-to-end
    python scripts/pipeline.py all --silent   # Run pipeline quietly (logs only)

🧾 Logs:
    Output is written to: logs/pipeline-run.log
"""

import subprocess
import click
import sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
EXTRACT = BASE / "scripts" / "extract_and_caption.py"
EMBED   = BASE / "scripts" / "embed.py"
LOGFILE = BASE / "logs" / "pipeline-run.log"

def run_script(script_path: Path, label: str, silent: bool = False):
    click.echo(f"\n▶️ Running {label}...\n")
    with open(LOGFILE, "a") as log:
        log.write(f"\n\n===== {label} =====\n")
        log.write(f"⏰ Started: {datetime.now().isoformat()}\n")

        process = subprocess.Popen(
            ["python", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            log.write(line)
            if not silent:
                click.echo(line, nl=False)

        process.wait()

        if process.returncode != 0:
            click.secho(f"\n❌ {label} failed. Check {LOGFILE}", fg="red")
            sys.exit(process.returncode)

    click.secho(f"\n✅ {label} completed\n", fg="green")

@click.group()
def cli():
    """Main command group"""
    pass

@cli.command()
@click.option('--silent', is_flag=True, help="Suppress stdout, write only to logs")
def extract(silent):
    """Run document extraction + image captioning"""
    run_script(EXTRACT, "Document Extraction + Captioning", silent)

@cli.command()
@click.option('--silent', is_flag=True, help="Suppress stdout, write only to logs")
def embed(silent):
    """Run embedding to vector store"""
    run_script(EMBED, "Embedding to Vector Store", silent)

@cli.command()
@click.option('--silent', is_flag=True, help="Suppress stdout, write only to logs")
def all(silent):
    """Run both extraction and embedding"""
    click.secho("🚀 Starting full pipeline...\n", fg="cyan")
    run_script(EXTRACT, "Document Extraction + Captioning", silent)
    run_script(EMBED, "Embedding to Vector Store", silent)
    click.secho("🎉 Pipeline complete! Check logs for details.\n", fg="cyan")

if __name__ == "__main__":
    cli()