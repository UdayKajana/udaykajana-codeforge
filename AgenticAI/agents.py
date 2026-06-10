"""
DSPy Agents for the Technical Notes Multi-Agent System.

Agent hierarchy:
  MasterAgent
    └── CurriculumAgent        → builds the syllabus
    └── TopicWriterAgent (x N) → writes each chapter
          └── SubTopicAgent (x M) → deep-dives each subtopic
    └── AssemblerAgent          → assembles the final HTML doc
"""

import json
import dspy
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from signatures import (
    CurriculumSignature,
    TopicWriterSignature,
    SubTopicDeepDiveSignature,
    AssemblerSignature,
)

console = Console()

# ---------------------------------------------------------------------------
# Style guide injected into every writing agent for visual consistency
# ---------------------------------------------------------------------------
STYLE_GUIDE = """
Use ONLY these CSS class names (already defined in the document <style>):
  .chapter-heading   → h2 for chapter titles
  .section-heading   → h3 for subtopic headings
  .subsection        → h4 for deeper breakdowns
  .definition-box    → <div class="definition-box"> for crisp one-line definitions
  .highlight         → <span class="highlight"> for key terms
  .code-block        → <pre><code class="code-block"> for code/commands
  .note-box          → <div class="note-box"> for gotchas/tips
  .comparison-table  → <table class="comparison-table"> for comparison grids
  .bullet-list       → <ul class="bullet-list">
  .numbered-list     → <ol class="numbered-list">

Heading hierarchy: h2 > h3 > h4. Never skip levels.
Always wrap chapter content in: <section class="chapter">...</section>
"""


# ---------------------------------------------------------------------------
# Individual DSPy modules (agents)
# ---------------------------------------------------------------------------

class CurriculumAgent(dspy.Module):
    """Generates the full topic curriculum as structured JSON."""

    def __init__(self, log_fn=None):
        super().__init__()
        self.generate = dspy.ChainOfThought(CurriculumSignature)
        self.log_fn = log_fn or (lambda msg: None)

    def _log(self, plain: str, rich: str = None):
        console.print(rich or plain)
        self.log_fn(plain)

    def forward(self, query: str) -> list[dict]:
        self._log(f"Analyzing topic: {query}", f"[bold cyan][ Curriculum Agent ][/] Analyzing topic: [yellow]{query}[/]")
        result = self.generate(query=query)
        raw = result.curriculum_json.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            curriculum = json.loads(raw)
        except json.JSONDecodeError as e:
            console.print(f"[red]JSON parse error in curriculum: {e}[/]")
            console.print(f"[dim]Raw output: {raw[:500]}[/]")
            raise

        self._log(f"Curriculum ready: {len(curriculum)} chapters", f"[green]Curriculum built:[/] {len(curriculum)} chapters")
        for i, ch in enumerate(curriculum, 1):
            self._log(f"  {i}. {ch['chapter']} ({len(ch['subtopics'])} subtopics)")
        return curriculum


class SubTopicAgent(dspy.Module):
    """Deep-dives into a single subtopic and returns an HTML block."""

    def __init__(self, log_fn=None):
        super().__init__()
        self.deepdive = dspy.ChainOfThought(SubTopicDeepDiveSignature)
        self.log_fn = log_fn or (lambda msg: None)

    def forward(self, subtopic: str, parent_chapter: str, overall_topic: str) -> str:
        self.log_fn(f"    Writing subtopic: {subtopic}")
        console.print(f"    [dim]-> SubTopic Agent:[/] {subtopic}")
        result = self.deepdive(
            subtopic=subtopic,
            parent_chapter=parent_chapter,
            overall_topic=overall_topic,
            html_style_guide=STYLE_GUIDE,
        )
        return result.html_content


class TopicWriterAgent(dspy.Module):
    """
    Writes a complete chapter section.
    For each subtopic it spawns a SubTopicAgent for a deep-dive,
    then stitches the results into a chapter HTML block.
    """

    def __init__(self, log_fn=None):
        super().__init__()
        self.writer = dspy.ChainOfThought(TopicWriterSignature)
        self.log_fn = log_fn or (lambda msg: None)
        self.subtopic_agent = SubTopicAgent(log_fn=self.log_fn)

    def _log(self, plain: str, rich: str = None):
        console.print(rich or plain)
        self.log_fn(plain)

    def forward(self, chapter: dict, overall_topic: str) -> str:
        title = chapter["chapter"]
        subtopics = chapter["subtopics"]

        self._log(f"Writing chapter: {title}", f"  [bold blue][ Topic Agent ][/] Writing chapter: [cyan]{title}[/]")

        subtopic_html_parts = []
        for st in subtopics:
            st_html = self.subtopic_agent(
                subtopic=st,
                parent_chapter=title,
                overall_topic=overall_topic,
            )
            subtopic_html_parts.append(st_html)

        combined_subtopic_content = "\n\n".join(subtopic_html_parts)
        result = self.writer(
            chapter_title=title,
            subtopics=", ".join(subtopics),
            overall_topic=overall_topic,
            html_style_guide=STYLE_GUIDE,
        )

        chapter_html = f"""
<section class="chapter" id="ch-{title.lower().replace(' ', '-').replace('/', '-')}">
  <h2 class="chapter-heading">{title}</h2>
  {result.html_content}
  <!-- Deep-dive subsections -->
  {combined_subtopic_content}
</section>
"""
        self._log(f"Chapter done: {title}", f"  [green]Done:[/] {title}")
        return chapter_html


class AssemblerAgent(dspy.Module):
    """Combines all chapter HTML blocks into one polished document."""

    def __init__(self, log_fn=None):
        super().__init__()
        self.assemble = dspy.ChainOfThought(AssemblerSignature)
        self.log_fn = log_fn or (lambda msg: None)

    def forward(self, overall_topic: str, chapters_html: str, curriculum: list[dict]) -> str:
        console.print("[bold magenta][ Assembler Agent ][/] Composing final document ...")
        self.log_fn("Assembling final document...")
        result = self.assemble(
            overall_topic=overall_topic,
            chapters_html=chapters_html,
            curriculum_json=json.dumps(curriculum, indent=2),
        )
        return result.final_html


# ---------------------------------------------------------------------------
# Master Agent — orchestrates the full pipeline
# ---------------------------------------------------------------------------

class MasterAgent(dspy.Module):
    """
    Orchestrates the full multi-agent note-generation pipeline:
      1. CurriculumAgent  → build syllabus
      2. TopicWriterAgent → one per chapter (with nested SubTopicAgents)
      3. AssemblerAgent   → final HTML document

    Returns a tuple: (final_html: str, curriculum: list[dict])
    Pass log_fn to receive plain-text status messages as generation progresses.
    """

    def __init__(self, log_fn=None):
        super().__init__()
        self.log_fn = log_fn or (lambda msg: None)
        self.curriculum_agent = CurriculumAgent(log_fn=self.log_fn)
        self.topic_writer = TopicWriterAgent(log_fn=self.log_fn)
        self.assembler = AssemblerAgent(log_fn=self.log_fn)

    def _log(self, plain: str, rich: str = None):
        console.print(rich or plain)
        self.log_fn(plain)

    def forward(self, query: str) -> tuple[str, list[dict]]:
        console.rule("[bold green]Technical Notes Generator[/]")
        self._log(f"Starting pipeline for: {query}", f"[bold]Query:[/] {query}\n")

        self._log("Phase 1: Building curriculum...", "[bold]Phase 1:[/] Building curriculum ...")
        curriculum = self.curriculum_agent(query=query)

        overall_topic = (
            query
            .replace("write a note on", "")
            .replace("write notes on", "")
            .replace("explain", "")
            .replace("What is", "")
            .strip()
            .title()
        )

        self._log(f"Phase 2: Writing {len(curriculum)} chapters...", f"\n[bold]Phase 2:[/] Writing {len(curriculum)} chapters ...\n")
        chapter_html_blocks = []
        for i, chapter in enumerate(curriculum, 1):
            self._log(f"Chapter {i}/{len(curriculum)}: {chapter['chapter']}")
            html = self.topic_writer(chapter=chapter, overall_topic=overall_topic)
            chapter_html_blocks.append(html)

        self._log("Phase 3: Assembling final document...")
        full_chapters_html = "\n\n".join(chapter_html_blocks)
        final_html = self.assembler(
            overall_topic=overall_topic,
            chapters_html=full_chapters_html,
            curriculum=curriculum,
        )

        self._log("Done! Notes are ready.")
        console.rule("[bold green]Done![/]")
        return final_html, curriculum
