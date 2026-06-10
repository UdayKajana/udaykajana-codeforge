"""
HTML + CSS template injected into every assembled document.
Designed for a Quill-compatible rich-text paste experience.
"""

DOCUMENT_STYLES = """
<style>
  /* ── Google Fonts ─────────────────────────────────────── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');

  /* ── CSS Variables ────────────────────────────────────── */
  :root {
    --primary:    #1a73e8;   /* Google Blue */
    --primary-dk: #0d47a1;
    --accent:     #fbbc04;   /* Amber */
    --success:    #34a853;   /* Green */
    --danger:     #ea4335;   /* Red */
    --text:       #202124;
    --subtext:    #5f6368;
    --border:     #dadce0;
    --bg-page:    #ffffff;
    --bg-card:    #f8f9fa;
    --bg-code:    #282c34;
    --code-text:  #abb2bf;
    --shadow:     0 1px 3px rgba(0,0,0,.12), 0 1px 2px rgba(0,0,0,.08);
    --radius:     8px;
  }

  /* ── Base ─────────────────────────────────────────────── */
  body {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    line-height: 1.7;
    color: var(--text);
    background: var(--bg-page);
    max-width: 900px;
    margin: 0 auto;
    padding: 24px 32px 64px;
  }

  /* ── Document Title ───────────────────────────────────── */
  .doc-title {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dk) 100%);
    color: #fff;
    padding: 32px 36px;
    border-radius: var(--radius);
    margin-bottom: 36px;
  }
  .doc-title h1 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 6px;
    letter-spacing: -0.5px;
  }
  .doc-title .doc-subtitle {
    font-size: 0.9rem;
    opacity: 0.85;
    margin: 0;
    font-weight: 400;
  }

  /* ── Table of Contents ────────────────────────────────── */
  .toc {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 4px solid var(--primary);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 40px;
  }
  .toc h2 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--primary);
    margin: 0 0 12px;
    font-weight: 600;
  }
  .toc ol {
    margin: 0;
    padding-left: 20px;
    column-count: 2;
    column-gap: 32px;
  }
  .toc li {
    margin-bottom: 6px;
    font-size: 0.9rem;
  }
  .toc a {
    color: var(--text);
    text-decoration: none;
    font-weight: 500;
  }
  .toc a:hover { color: var(--primary); text-decoration: underline; }

  /* ── Chapter / Section ────────────────────────────────── */
  .chapter {
    margin-bottom: 52px;
    padding-bottom: 24px;
    border-bottom: 2px solid var(--border);
  }
  .chapter:last-of-type { border-bottom: none; }

  /* ── Headings ─────────────────────────────────────────── */
  h2.chapter-heading {
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--primary);
    border-bottom: 3px solid var(--accent);
    padding-bottom: 8px;
    margin: 0 0 20px;
    letter-spacing: -0.3px;
  }
  h3.section-heading {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--primary-dk);
    margin: 28px 0 10px;
    padding-left: 10px;
    border-left: 3px solid var(--accent);
  }
  h4.subsection {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text);
    margin: 18px 0 8px;
  }
  h4.subsection::before {
    content: "▸ ";
    color: var(--primary);
  }

  /* ── Definition Box ───────────────────────────────────── */
  .definition-box {
    background: #e8f0fe;
    border-left: 4px solid var(--primary);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 12px 16px;
    margin: 12px 0 16px;
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--primary-dk);
  }

  /* ── Note / Tip Box ───────────────────────────────────── */
  .note-box {
    background: #fff8e1;
    border-left: 4px solid var(--accent);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 12px 16px;
    margin: 16px 0;
    font-size: 0.9rem;
    color: #5d4037;
  }
  .note-box strong { color: #bf8c00; }

  /* ── Highlight ────────────────────────────────────────── */
  .highlight {
    background: #e8f0fe;
    color: var(--primary-dk);
    padding: 1px 5px;
    border-radius: 3px;
    font-weight: 500;
    font-size: 0.92em;
  }

  /* ── Code Block ───────────────────────────────────────── */
  pre {
    background: var(--bg-code);
    border-radius: var(--radius);
    padding: 16px 20px;
    overflow-x: auto;
    margin: 14px 0;
    box-shadow: var(--shadow);
  }
  code.code-block, pre code {
    font-family: 'Fira Code', monospace;
    font-size: 0.84rem;
    color: var(--code-text);
    line-height: 1.6;
  }
  p code, li code {
    font-family: 'Fira Code', monospace;
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.85em;
    color: #d32f2f;
  }

  /* ── Lists ────────────────────────────────────────────── */
  ul.bullet-list, ol.numbered-list {
    padding-left: 22px;
    margin: 10px 0 14px;
  }
  ul.bullet-list li, ol.numbered-list li {
    margin-bottom: 6px;
    font-size: 0.95rem;
  }
  ul.bullet-list li::marker { color: var(--primary); font-size: 1.1em; }
  ol.numbered-list li::marker { color: var(--primary); font-weight: 600; }

  /* ── Comparison Table ─────────────────────────────────── */
  table.comparison-table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0 24px;
    font-size: 0.9rem;
    box-shadow: var(--shadow);
    border-radius: var(--radius);
    overflow: hidden;
  }
  table.comparison-table thead tr {
    background: var(--primary);
    color: #fff;
  }
  table.comparison-table thead th {
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    letter-spacing: 0.3px;
  }
  table.comparison-table tbody tr:nth-child(even) { background: var(--bg-card); }
  table.comparison-table tbody tr:hover { background: #e8f0fe; }
  table.comparison-table td {
    padding: 9px 14px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }

  /* ── Divider ──────────────────────────────────────────── */
  hr.section-divider {
    border: none;
    border-top: 1px dashed var(--border);
    margin: 24px 0;
  }

  /* ── Print ────────────────────────────────────────────── */
  @media print {
    body { max-width: 100%; padding: 16px; }
    .toc ol { column-count: 1; }
    pre { white-space: pre-wrap; }
  }
</style>
"""


def build_toc(curriculum: list[dict]) -> str:
    """Build a numbered HTML Table of Contents from the curriculum."""
    items = []
    for i, ch in enumerate(curriculum, 1):
        slug = ch["chapter"].lower().replace(" ", "-").replace("/", "-")
        items.append(f'<li><a href="#ch-{slug}">{ch["chapter"]}</a></li>')
    return f"""
<nav class="toc">
  <h2>Table of Contents</h2>
  <ol>
    {"".join(items)}
  </ol>
</nav>
"""


def wrap_final_document(topic: str, toc_html: str, chapters_html: str) -> str:
    """Wrap content in a full HTML document with styles."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{topic} — Technical Notes</title>
  {DOCUMENT_STYLES}
</head>
<body>

  <div class="doc-title">
    <h1>{topic}</h1>
    <p class="doc-subtitle">Comprehensive Technical Reference · All concepts covered in depth</p>
  </div>

  {toc_html}

  <main>
    {chapters_html}
  </main>

</body>
</html>
"""
