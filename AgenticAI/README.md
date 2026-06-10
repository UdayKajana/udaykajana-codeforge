# Technical Notes Generator — DSPy Multi-Agent System

Generate comprehensive, well-formatted single-page technical notes on any topic using a **DSPy-powered multi-agent pipeline**.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────┐
│              MasterAgent                    │
│                                             │
│  1. CurriculumAgent ──► JSON syllabus       │
│                                             │
│  2. TopicWriterAgent (per chapter)          │
│       └── SubTopicAgent (per subtopic)      │
│             deep-dive: what/why/how/when    │
│                                             │
│  3. AssemblerAgent ──► Final HTML doc       │
└─────────────────────────────────────────────┘
    │
    ▼
Quill-ready HTML file
```

### Agents

| Agent | DSPy Signature | Role |
|---|---|---|
| **CurriculumAgent** | `CurriculumSignature` | Builds the full syllabus as structured JSON |
| **TopicWriterAgent** | `TopicWriterSignature` | Writes one chapter, coordinates subtopics |
| **SubTopicAgent** | `SubTopicDeepDiveSignature` | Deep-dives a single subtopic (what/why/how/when/where) |
| **AssemblerAgent** | `AssemblerSignature` | Combines chapters into a styled HTML document |
| **MasterAgent** | — | Orchestrates all agents end-to-end |

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

---

## Usage

### CLI

```bash
python pipeline.py "write a note on GCP BigQuery"
python pipeline.py "explain Kubernetes architecture" --model gpt-4o-mini
python pipeline.py "Apache Kafka deep dive" --output my_notes
```

### Interactive Demo

```bash
python demo.py
```

### Output

Generated HTML files are saved to `output/` (or your `--output` dir).  
Open in browser or use `viewer.html` to preview in a Quill editor.

---

## Quill Preview

Open `viewer.html` in a browser, then:
1. **Load file** → pick the generated `.html` from `output/`
2. Or **Paste HTML** directly from clipboard
3. The left pane shows the Quill-rendered view; right pane shows raw HTML

---

## Example Output Structure

For the query `"write a note on GCP BigQuery"`, the pipeline generates:

```
GCP BigQuery — Technical Notes
├── Overview & Core Concepts
│   ├── What is BigQuery?
│   ├── Why BigQuery? (vs alternatives)
│   └── Architecture overview
├── Schema Objects
│   ├── Tables — types (native, external, wildcard), retention, auto-delete
│   ├── Views — logical, materialized, authorized
│   ├── Routines — UDFs, stored procedures
│   └── Datasets — structure, access control
├── Partitioning
│   ├── Ingestion-time partitioning
│   ├── Column partitioning (DATE/TIMESTAMP/INT64)
│   └── Partition pruning & filters
├── Clustering
├── Query Optimization
├── Security & Access Control
├── Pricing Model
├── Strengths & Weaknesses
└── Real-World Use Cases
```

---

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required. Your OpenAI API key |
| `MODEL_NAME` | `gpt-4o` | Override via `--model` flag |

---

## File Structure

```
AgenticAI/
├── signatures.py      # DSPy Signatures (input/output contracts)
├── agents.py          # All DSPy agents (Curriculum, Writer, SubTopic, Assembler, Master)
├── pipeline.py        # Orchestration + CLI entry point
├── style_template.py  # HTML/CSS template for consistent formatting
├── demo.py            # Interactive demo runner
├── viewer.html        # Quill preview tool (open in browser)
├── requirements.txt
├── .env.example
└── output/            # Generated HTML notes saved here
```
