"""
Quick demo / interactive runner.
Run this file directly to try the system interactively.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

load_dotenv()
console = Console()

DEMO_QUERIES = [
    "write a note on GCP BigQuery",
    "explain Kubernetes architecture",
    "write notes on Apache Kafka",
    "explain AWS S3 in depth",
    "write a note on Redis",
    "explain Docker and container networking",
]


def main():
    console.print(Panel.fit(
        "[bold blue]Technical Notes Generator[/]\n"
        "[dim]Powered by DSPy + Multi-Agent Pipeline[/]",
        border_style="blue",
    ))

    console.print("\n[bold]Example queries:[/]")
    for i, q in enumerate(DEMO_QUERIES, 1):
        console.print(f"  [dim]{i}.[/] {q}")

    console.print()
    query = Prompt.ask(
        "[bold green]Enter your query[/]",
        default=DEMO_QUERIES[0],
    )

    model = Prompt.ask(
        "[bold green]Model[/]",
        default="gpt-4o",
        choices=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    )

    # Import here so dotenv is loaded first
    from pipeline import run_pipeline

    file_path = run_pipeline(query=query, model=model)

    console.print(f"\n[bold]Done![/] Open your notes:")
    console.print(f"  [link=file://{file_path.resolve()}]file://{file_path.resolve()}[/link]")
    console.print("\n[dim]Paste the HTML content into a Quill editor for rich-text display.[/]")


if __name__ == "__main__":
    main()
