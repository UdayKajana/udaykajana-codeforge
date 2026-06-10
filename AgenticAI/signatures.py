"""
DSPy Signatures for the Technical Notes Multi-Agent System.
Each signature defines the input/output contract for an agent step.
"""

import dspy


class CurriculumSignature(dspy.Signature):
    """
    Given a technical topic query, generate a comprehensive, structured curriculum
    as a JSON list of major chapters. Each chapter should have a title and a list
    of sub-topics that must be covered. The curriculum must ensure complete 360-degree
    coverage: definition, purpose, architecture, types/variants, internals, configuration,
    best practices, strengths, weaknesses, real-world use cases, and comparisons.
    Return ONLY valid JSON — no prose outside the JSON block.

    Example output format:
    [
      {
        "chapter": "Overview & Core Concepts",
        "subtopics": ["What is X?", "Why X?", "Key terminology", "Architecture overview"]
      },
      ...
    ]
    """
    query: str = dspy.InputField(desc="User's technical topic question, e.g. 'Write a note on GCP BigQuery'")
    curriculum_json: str = dspy.OutputField(desc="JSON array of chapters, each with title and subtopics list")


class TopicWriterSignature(dspy.Signature):
    """
    Write a deeply detailed, straight-to-the-point technical section for a given chapter
    and its subtopics. Every subtopic must be covered. Each explanation must answer:
    - What is it?
    - Why does it exist / why does it matter?
    - How does it work internally?
    - When should you use it?
    - Where is it applicable?

    Rules:
    - Be precise and technical. No padding, no filler sentences.
    - Use bullet points and numbered lists for clarity.
    - For each subtopic, start with a short crisp definition, then go deeper.
    - Include concrete examples where helpful.
    - Return ONLY the HTML content for this chapter section (no full <html> wrapper).
    - Use the heading/color/font conventions provided in html_style_guide.
    """
    chapter_title: str = dspy.InputField(desc="Title of the chapter/section being written")
    subtopics: str = dspy.InputField(desc="Comma-separated list of subtopics that must all be covered")
    overall_topic: str = dspy.InputField(desc="The overarching technical topic (e.g. 'GCP BigQuery')")
    html_style_guide: str = dspy.InputField(desc="CSS class names and heading conventions to use for consistent styling")
    html_content: str = dspy.OutputField(desc="Complete HTML for this chapter section using the provided style guide")


class SubTopicDeepDiveSignature(dspy.Signature):
    """
    Perform an exhaustive deep-dive on a single subtopic within a larger technical chapter.
    Produce a self-contained HTML block that covers every angle:
    - Core definition (1–2 crisp sentences)
    - Internal mechanics / how it works
    - Types / variants / modes (with differences)
    - Configuration options / parameters
    - Practical examples
    - Gotchas, edge cases, anti-patterns
    - When to use vs. when NOT to use

    Return ONLY the HTML block (no full <html> wrapper).
    Follow the html_style_guide strictly for headings, colors, and fonts.
    """
    subtopic: str = dspy.InputField(desc="Specific subtopic to deep-dive into")
    parent_chapter: str = dspy.InputField(desc="The chapter this subtopic belongs to")
    overall_topic: str = dspy.InputField(desc="The overarching technical topic")
    html_style_guide: str = dspy.InputField(desc="CSS conventions to follow")
    html_content: str = dspy.OutputField(desc="Deep-dive HTML block for this subtopic")


class AssemblerSignature(dspy.Signature):
    """
    You are a technical documentation assembler. Combine all chapter HTML sections into
    a single, beautifully formatted, complete HTML document ready to be pasted into a
    Quill rich-text editor.

    Requirements:
    - Start with a prominent title banner for the topic
    - Add a clickable Table of Contents
    - Stitch all chapter sections in order
    - Ensure consistent typography throughout
    - The output must be valid, self-contained HTML with inline <style> in a <head> tag
    - Color palette: professional dark-theme accents on white background
      Primary: #1a73e8 (Google Blue), Accent: #fbbc04 (Amber), Text: #202124,
      Sub-text: #5f6368, Code bg: #f8f9fa
    - Use Google Fonts: Inter for body, Fira Code for code/mono
    - Every heading level must be visually distinct
    """
    overall_topic: str = dspy.InputField(desc="The technical topic the document is about")
    chapters_html: str = dspy.InputField(desc="All chapter HTML sections concatenated, in order")
    curriculum_json: str = dspy.InputField(desc="The original curriculum JSON to build the TOC")
    final_html: str = dspy.OutputField(desc="Complete, self-contained HTML document for Quill")
