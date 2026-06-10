"""
Main pipeline entry point.
Configures DSPy, loads agents, runs the full generation pipeline,
and saves the output HTML file.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console

import dspy
from config import get_lm, detect_provider
from agents import MasterAgent
from style_template import build_toc, wrap_final_document

load_dotenv()
console = Console()


def run_pipeline(query: str, output_dir: str = "output", api_key: str = "") -> Path:
    """
    Run the full multi-agent pipeline for a given query.
    api_key: Azure or OpenRouter key (falls back to AZURE_API_KEY / OPENROUTER_API_KEY env vars).
    Returns the path to the saved HTML file.
    """
    if not api_key:
        api_key = os.getenv("AZURE_API_KEY") or os.getenv("OPENROUTER_API_KEY") or ""
    if not api_key:
        console.print("[red]Error:[/] No API key found. Pass --api-key or set AZURE_API_KEY / OPENROUTER_API_KEY.")
        sys.exit(1)

    provider = detect_provider(api_key)
    lm = get_lm(api_key)
    dspy.configure(lm=lm)   # safe: pipeline.py runs single-threaded from CLI
    console.print(f"[dim]DSPy configured -> {provider}[/]\n")

    master = MasterAgent()

    # Run the full pipeline — returns (html, curriculum)
    raw_html, curriculum = master(query=query)

    overall_topic = (
        query
        .replace("write a note on", "")
        .replace("write notes on", "")
        .replace("explain", "")
        .replace("What is", "")
        .strip()
        .title()
    )

    toc_html = build_toc(curriculum)

    # If the LLM already produced a full HTML doc, use it directly.
    # Otherwise wrap with our style template.
    if raw_html.strip().startswith("<!DOCTYPE") or raw_html.strip().startswith("<html"):
        final_html = raw_html
    else:
        final_html = wrap_final_document(
            topic=overall_topic,
            toc_html=toc_html,
            chapters_html=raw_html,
        )

    # Save output
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True)
    slug = overall_topic.lower().replace(" ", "_").replace("/", "_")[:60]
    file_path = out_path / f"{slug}_notes.html"
    file_path.write_text(final_html, encoding="utf-8")

    console.print(f"\n[bold green]Output saved:[/] {file_path.resolve()}")
    return file_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive single-page technical notes using DSPy multi-agent flow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py "write a note on GCP BigQuery" --api-key sk-or-v1-...
  python pipeline.py "explain Kubernetes networking" --api-key 4tzKD...
  python pipeline.py "Apache Kafka deep dive" --output my_notes
        """,
    )
    parser.add_argument("query", help="The technical topic to generate notes for")
    parser.add_argument("--api-key", default="", help="Azure or OpenRouter API key (or set AZURE_API_KEY env var)")
    parser.add_argument("--output", default="output", help="Output directory (default: output)")
    args = parser.parse_args()

    file_path = run_pipeline(
        query=args.query,
        output_dir=args.output,
        api_key=args.api_key,
    )
    console.print(f"\n[dim]Open in browser:[/] file://{file_path.resolve()}")


if __name__ == "__main__":
    main()
