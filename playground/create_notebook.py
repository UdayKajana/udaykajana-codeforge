"""
Generates dspy_vs_direct_handoff.ipynb
Two cases, same Agent-1, same Agent-2, only the handoff layer differs.

Case 1:  Agent-1 --> DSPy --> Agent-2 --> Output
Case 2:  Agent-1 --> System Instructions --> Agent-2 --> Output
"""
import json

def md(src):
    return {"cell_type": "markdown", "id": f"m{abs(hash(src[:20])):x}", "metadata": {}, "source": [src]}

def code(src):
    return {"cell_type": "code", "id": f"c{abs(hash(src[:20])):x}", "metadata": {},
            "outputs": [], "execution_count": None, "source": [src]}

cells = []

# ─────────────────────────────────────────────────────────────────────────────
# Title
# ─────────────────────────────────────────────────────────────────────────────
cells.append(md("""\
# Procurement Email Pipeline — Two Handoff Strategies

```
Case 1:   Email  ──►  Agent-1  ──►  DSPy  ──►  Agent-2  ──►  Output
Case 2:   Email  ──►  Agent-1  ──►  System Instructions  ──►  Agent-2  ──►  Output
```

**Agent-1** is identical in both cases.
It reads the email and produces a structured JSON where every required field is present —
stated values are filled in, missing fields are left as `""`.

**The handoff layer is the only difference:**
- **Case 1 — DSPy:** Receives Agent-1's JSON, scans every `""` field,
  and writes a targeted `fill_instructions` map telling Agent-2 *exactly*
  how to fill each gap (derive, domain-knowledge, or needs-input).
- **Case 2 — System Instructions:** A static instruction string is appended
  to Agent-1's JSON and passed directly to Agent-2.

**Agent-2** is identical in both cases.
It receives the handoff payload and fills every empty field.
"""))

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────
cells.append(md("## Setup"))

cells.append(code("!pip install openai-agents dspy -q"))

cells.append(code("""\
import json, asyncio, dspy
from openai import AsyncAzureOpenAI
from agents import (Agent, Runner, ModelSettings,
                    set_default_openai_client, set_default_openai_api,
                    set_tracing_disabled)
import nest_asyncio
nest_asyncio.apply()
set_tracing_disabled(True)
"""))

cells.append(code("""\
AZURE_API_KEY     = ""
AZURE_ENDPOINT    = ""
AZURE_API_VERSION = ""
AZURE_DEPLOYMENT  = ""

_client = AsyncAzureOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version=AZURE_API_VERSION,
)
set_default_openai_client(_client)
set_default_openai_api("chat_completions")

dspy.configure(lm=dspy.LM(
    model       = f"azure/{AZURE_DEPLOYMENT}",
    api_key     = AZURE_API_KEY,
    api_base    = AZURE_ENDPOINT,
    api_version = AZURE_API_VERSION,
    max_tokens  = 2500,
    temperature = 0.0,
))
print("Ready.")
"""))

# ─────────────────────────────────────────────────────────────────────────────
# Load emails
# ─────────────────────────────────────────────────────────────────────────────
cells.append(md("## Load Emails"))

cells.append(code("""\
with open("/content/bidding_emails.json", encoding="utf-8") as f:
    emails = json.load(f)
print(f"Loaded {len(emails)} emails.")
for k, v in emails.items():
    print(f"  {k}  {v[:90].strip()}...")
"""))

# ─────────────────────────────────────────────────────────────────────────────
# Agent-1  (shared — identical for both cases)
# ─────────────────────────────────────────────────────────────────────────────
cells.append(md("""\
---
## Agent-1 — Extractor  *(shared by both cases)*

Reads the email and produces a JSON with two sections:
- `extracted_values` — only facts the email explicitly states (exact wording, no inference)
- `field_inventory`  — every field a standard record of this domain requires.
  Stated values are copied in; required-but-missing fields are set to `""`.
"""))

cells.append(code("""\
AGENT1_INSTRUCTIONS = \"\"\"
You are a FORENSIC DOCUMENT EXTRACTOR for procurement records.

Read the incoming email and output a single JSON with exactly 5 top-level keys.

────────────────────────────────────────────
1. document_meta
────────────────────────────────────────────
Keys: sender, recipient, date, title_or_subject, document_type
Fill from email headers. Use null for absent fields.

────────────────────────────────────────────
2. context
────────────────────────────────────────────
Your classification (not the email's words):
  domain       -- subject area: "procurement", "manufacturing", "it", "fleet", etc.
  record_type  -- "rfq", "inquiry", "contract", "tender", "order"
  summary      -- 1-2 sentences: what is this email asking for?
  tone         -- "formal" | "informal" | "urgent"
  intent       -- "request" | "inform" | "propose" | "instruct"

────────────────────────────────────────────
3. extracted_values
────────────────────────────────────────────
Every concrete fact the email explicitly states:
  names, quantities, dates, amounts, specs, locations, contacts,
  certifications, preferences, constraints.
Use the email's exact wording. Never paraphrase. Never invent.

────────────────────────────────────────────
4. field_inventory
────────────────────────────────────────────
A complete checklist of ALL fields a standard record of this domain/record_type needs.
Rules:
  (a) Derive the required fields from domain + record_type -- no hardcoded lists.
  (b) Where the email states a value: copy it from extracted_values.
  (c) Where the email does NOT state a value: set to "" (empty string).
  (d) All keys snake_case. Group under: identifiers, subject_item, scope_quantity,
      financial, timeline, parties, location, requirements, contacts.
  (e) Add domain-specific fields (e.g. certifications_required for manufacturing,
      warranty_years for IT hardware, amc_terms for fleet).

────────────────────────────────────────────
5. open_items
────────────────────────────────────────────
Array of strings: ambiguities, contradictions, or missing clarifications.
Quote the email where possible. [] if nothing to flag.

STRICT RULES:
  - Raw JSON only. No markdown fences. No prose.
  - extracted_values: only what the email explicitly states.
  - field_inventory: every standard field present; stated values filled; missing = "".
\"\"\"

agent1 = Agent(
    name           = "Agent1_Extractor",
    model          = AZURE_DEPLOYMENT,
    model_settings = ModelSettings(max_tokens=2500, temperature=0.0),
    instructions   = AGENT1_INSTRUCTIONS,
)
print("Agent-1 ready.")
"""))

# ─────────────────────────────────────────────────────────────────────────────
# Agent-2  (shared — identical for both cases)
# ─────────────────────────────────────────────────────────────────────────────
cells.append(md("""\
---
## Agent-2 — Enricher  *(shared by both cases)*

Receives the handoff payload (Agent-1 JSON + handoff instructions) and fills every `""` field.
In Case 1 the instructions come from DSPy (targeted, field-specific).
In Case 2 the instructions are a static string prepended by Python.
The agent itself is identical either way.
"""))

cells.append(code("""\
AGENT2_INSTRUCTIONS = \"\"\"
You are a DATA ENRICHMENT AGENT for procurement records.

You receive a JSON that was extracted from a procurement email.
The field_inventory contains required fields — some are filled, some are "".
Your job: fill every empty field and validate the final record.

────────────────────────────────────────────
TASK 1 — FILL every "" field in field_inventory
────────────────────────────────────────────
If the handoff includes fill_instructions, read them first — they tell you
exactly how to handle each empty field (derive / domain-knowledge / needs-input).

For each empty field, apply in order:
  STEP 1 — DERIVE: compute from other filled fields.
           Examples: total_value = quantity x unit_price
                     lead_time_days = delivery_date - today
                     contract_end = contract_start + duration
  STEP 2 — DOMAIN KNOWLEDGE: fill with the standard or typical value for this domain.
           Be specific. State the basis.
           Examples: "Net 30 (industry standard for procurement)"
                     "ISO 9001 (standard for manufacturing quality)"
                     "UN38.3 (mandatory for EV battery transport)"
  STEP 3 — LAST RESORT: set "__NEEDS_INPUT__" only if genuinely unknowable.

────────────────────────────────────────────
TASK 2 — VALIDATE
────────────────────────────────────────────
Add a validation section:
  completeness    -- "complete" | "mostly_complete" | "incomplete"
  missing_inputs  -- array of field_inventory keys still "__NEEDS_INPUT__"
  inconsistencies -- contradictions or mismatches between fields
  risk_flags      -- specific concerns a reviewer would escalate (never leave empty if issues exist)
  summary         -- one sentence on overall record quality and readiness

────────────────────────────────────────────
OUTPUT RULES
────────────────────────────────────────────
Return exactly these top-level keys:
  document_meta, context, extracted_values, field_inventory, open_items, validation
Every field_inventory value must be filled or "__NEEDS_INPUT__" -- no "" remaining.
Raw JSON only. No markdown fences.
\"\"\"

agent2 = Agent(
    name           = "Agent2_Enricher",
    model          = AZURE_DEPLOYMENT,
    model_settings = ModelSettings(max_tokens=4000, temperature=0.0),
    instructions   = AGENT2_INSTRUCTIONS,
)
print("Agent-2 ready.")
"""))

# ─────────────────────────────────────────────────────────────────────────────
# Case 1 — DSPy handoff
# ─────────────────────────────────────────────────────────────────────────────
cells.append(md("""\
---
## Case 1 — Agent-1  ──►  DSPy  ──►  Agent-2

```
Email
  |
  v
Agent-1          reads email, extracts facts, marks missing fields as ""
  |
  v  [DSPy HandoffSignature]
DSPy             scans every "" in field_inventory
                 writes fill_instructions: for each empty field, specifies
                 whether to DERIVE / use DOMAIN KNOWLEDGE / mark NEEDS_INPUT
                 passes the original JSON + fill_instructions to Agent-2
  |
  v
Agent-2          reads fill_instructions, fills every field, validates
  |
  v
Final JSON
```

DSPy adds intelligence to the handoff — instead of passing raw JSON,
it pre-computes the fill strategy per field so Agent-2 has a clear roadmap.
"""))

cells.append(code("""\
class HandoffSignature(dspy.Signature):
    \"\"\"
    You receive a structured JSON extracted from a procurement email.
    The field_inventory has "" for fields that are required but not yet filled.

    Your job — analyse the JSON and write fill_instructions for Agent-2:
      For EVERY field in field_inventory where value is "":
        - Decide the fill strategy:
            DERIVE         -- can be computed from other filled fields (show the formula)
            DOMAIN_DEFAULT -- standard/typical value exists for this domain (state the value and basis)
            NEEDS_INPUT    -- genuinely unknowable without the sender
        - Write a one-line instruction per field.

    Output the original JSON unchanged, with one new top-level key added:
      fill_instructions -- object mapping each empty field_inventory key to its instruction string.

    Example fill_instructions entry:
      "total_value":    "DERIVE: quantity (15) x unit_price when provided",
      "payment_terms":  "DOMAIN_DEFAULT: Net 30 -- standard for manufacturing procurement",
      "rfq_id":         "NEEDS_INPUT: buyer must supply a reference number"

    Raw JSON only. No markdown fences. Preserve all existing keys exactly.
    \"\"\"
    agent1_json  : str = dspy.InputField(
        desc="JSON output from Agent-1: document_meta, context, extracted_values, field_inventory, open_items"
    )
    handoff_json : str = dspy.OutputField(
        desc="Same JSON with fill_instructions object added at the top level"
    )

dspy_handoff = dspy.Predict(HandoffSignature)
print("DSPy HandoffSignature ready.")
"""))

cells.append(code("""\
def strip_fences(text: str) -> str:
    return text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

async def run_case1(email_key: str, email_text: str) -> dict:
    sep = "-" * 56
    print(f"\\n{sep}")
    print(f"  Case 1 | {email_key}")
    print(sep)

    # ── Step 1: Agent-1 extracts ──────────────────────────────────
    print("  [Agent-1]  Reading email and extracting...")
    r1 = await Runner.run(agent1, input=email_text)
    a1_out = r1.final_output
    print(f"             Done -- {len(a1_out)} chars")

    # ── Step 2: DSPy builds the handoff payload ───────────────────
    print("  [DSPy]     Analysing gaps and building fill_instructions...")
    dspy_result = dspy_handoff(agent1_json=a1_out)
    handoff_payload = dspy_result.handoff_json
    print(f"             Done -- {len(handoff_payload)} chars")

    # Show what DSPy added (fill_instructions only)
    try:
        hp = json.loads(strip_fences(handoff_payload))
        fi = hp.get("fill_instructions", {})
        print(f"             fill_instructions: {len(fi)} fields annotated")
        for field, instruction in list(fi.items())[:4]:
            print(f"               {field}: {instruction}")
        if len(fi) > 4:
            print(f"               ... and {len(fi)-4} more")
    except Exception:
        pass

    # ── Step 3: Agent-2 fills using DSPy's instructions ──────────
    print("  [Agent-2]  Filling fields using DSPy instructions...")
    r2 = await Runner.run(agent2, input=handoff_payload)
    a2_out = r2.final_output
    print(f"             Done -- {len(a2_out)} chars")

    # Parse
    try:
        parsed = json.loads(strip_fences(a2_out))
    except json.JSONDecodeError as e:
        parsed = {"raw_output": a2_out, "parse_error": str(e)}

    return {
        "email_key"       : email_key,
        "case"            : "case1_dspy_handoff",
        "agent1_out"      : a1_out,
        "dspy_handoff_out": handoff_payload,
        "final"           : parsed,
    }


async def run_all_case1(emails: dict) -> list:
    results = []
    for key, body in emails.items():
        result = await run_case1(key, body)
        results.append(result)
        print(f"\\n[FINAL -- {key}]")
        print(json.dumps(result["final"], indent=2, ensure_ascii=False))
    return results

results_case1 = await run_all_case1(emails)
print(f"\\nCase 1 complete -- {len(results_case1)} emails processed.")
"""))

# ─────────────────────────────────────────────────────────────────────────────
# Case 2 — System Instructions handoff
# ─────────────────────────────────────────────────────────────────────────────
cells.append(md("""\
---
## Case 2 — Agent-1  ──►  System Instructions  ──►  Agent-2

```
Email
  |
  v
Agent-1          reads email, extracts facts, marks missing fields as ""
                 (identical to Case 1)
  |
  v  [Python — static instruction string appended]
  Agent-1 JSON
  +
  \"The field_inventory above has empty fields.
   Fill each one using derivation or domain knowledge.
   Validate the final record.\"
  |
  v
Agent-2          fills fields, validates
                 (same agent as Case 1, different input)
  |
  v
Final JSON
```

No DSPy. The handoff is a static instruction block Python appends to Agent-1's output.
Agent-2 must figure out the fill strategy for each field itself.
"""))

cells.append(code("""\
# Static handoff instruction — appended to Agent-1's JSON by Python
HANDOFF_INSTRUCTION = \"\"\"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HANDOFF INSTRUCTIONS FOR AGENT-2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The JSON above was extracted from a procurement email.
Fields set to "" in field_inventory are required but not stated in the email.

Your tasks:
1. Fill every "" field:
   - DERIVE from other fields where possible (e.g. total = qty x price)
   - Apply domain-standard values where applicable (state the basis)
   - Set "__NEEDS_INPUT__" only as a last resort

2. Add a validation section:
   completeness, missing_inputs, inconsistencies, risk_flags, summary

Return the completed JSON.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
\"\"\"

async def run_case2(email_key: str, email_text: str) -> dict:
    sep = "-" * 56
    print(f"\\n{sep}")
    print(f"  Case 2 | {email_key}")
    print(sep)

    # ── Step 1: Agent-1 extracts (same as Case 1) ─────────────────
    print("  [Agent-1]  Reading email and extracting...")
    r1 = await Runner.run(agent1, input=email_text)
    a1_out = r1.final_output
    print(f"             Done -- {len(a1_out)} chars")

    # ── Step 2: Python builds the handoff payload (static) ────────
    handoff_payload = a1_out + HANDOFF_INSTRUCTION
    print(f"  [Python]   Appended static instructions (+{len(HANDOFF_INSTRUCTION)} chars)")

    # ── Step 3: Agent-2 fills using the static instructions ───────
    print("  [Agent-2]  Filling fields using static instructions...")
    r2 = await Runner.run(agent2, input=handoff_payload)
    a2_out = r2.final_output
    print(f"             Done -- {len(a2_out)} chars")

    # Parse
    try:
        parsed = json.loads(strip_fences(a2_out))
    except json.JSONDecodeError as e:
        parsed = {"raw_output": a2_out, "parse_error": str(e)}

    return {
        "email_key"  : email_key,
        "case"       : "case2_system_instructions",
        "agent1_out" : a1_out,
        "final"      : parsed,
    }


async def run_all_case2(emails: dict) -> list:
    results = []
    for key, body in emails.items():
        result = await run_case2(key, body)
        results.append(result)
        print(f"\\n[FINAL -- {key}]")
        print(json.dumps(result["final"], indent=2, ensure_ascii=False))
    return results

results_case2 = await run_all_case2(emails)
print(f"\\nCase 2 complete -- {len(results_case2)} emails processed.")
"""))

# ─────────────────────────────────────────────────────────────────────────────
# Comparison
# ─────────────────────────────────────────────────────────────────────────────
cells.append(md("""\
---
## Comparison — Case 1 vs Case 2
"""))

cells.append(code("""\
def analyse(result: dict) -> dict:
    final = result["final"]
    if "parse_error" in final:
        return {**result, "parse_ok": False, "filled": 0,
                "needs_input": 0, "risk_flags": 0, "completeness": "PARSE ERROR"}

    def walk(obj):
        filled = needs = 0
        if isinstance(obj, dict):
            for v in obj.values():
                f, n = walk(v)
                filled += f; needs += n
        elif isinstance(obj, list):
            for v in obj:
                f, n = walk(v)
                filled += f; needs += n
        elif isinstance(obj, str):
            if obj == "__NEEDS_INPUT__": needs += 1
            elif obj not in ("", None):  filled += 1
        return filled, needs

    filled, needs = walk(final.get("field_inventory", {}))
    val   = final.get("validation", {})
    flags = val.get("risk_flags", [])

    return {
        "email_key"   : result["email_key"],
        "case"        : result["case"],
        "parse_ok"    : True,
        "filled"      : filled,
        "needs_input" : needs,
        "risk_flags"  : len(flags) if isinstance(flags, list) else 0,
        "completeness": val.get("completeness", "—"),
    }

m1 = [analyse(r) for r in results_case1]
m2 = [analyse(r) for r in results_case2]

# Table
H = f"{'Email':<10}  {'Case1 Filled':>12} {'Needs':>6} {'Flags':>6} {'Completeness':<18}  " \
    f"{'Case2 Filled':>12} {'Needs':>6} {'Flags':>6} {'Completeness':<18}"
print("=" * len(H))
print(H)
print("-" * len(H))

for a, b in zip(m1, m2):
    def row(m):
        return f"{m['filled']:>12} {m['needs_input']:>6} {m['risk_flags']:>6} {m['completeness']:<18}"
    print(f"{a['email_key']:<10}  {row(a)}  {row(b)}")

print("=" * len(H))

# Totals
t1_f = sum(m["filled"]      for m in m1 if m["parse_ok"])
t1_n = sum(m["needs_input"] for m in m1 if m["parse_ok"])
t1_r = sum(m["risk_flags"]  for m in m1 if m["parse_ok"])
t2_f = sum(m["filled"]      for m in m2 if m["parse_ok"])
t2_n = sum(m["needs_input"] for m in m2 if m["parse_ok"])
t2_r = sum(m["risk_flags"]  for m in m2 if m["parse_ok"])

print(f"\\n{'TOTAL':<10}  {t1_f:>12} {t1_n:>6} {t1_r:>6} {'':18}  {t2_f:>12} {t2_n:>6} {t2_r:>6}")
print(f"\\nCase 1 (DSPy handoff)        : {t1_f} fields filled  |  {t1_n} needs-input  |  {t1_r} risk flags")
print(f"Case 2 (System instructions) : {t2_f} fields filled  |  {t2_n} needs-input  |  {t2_r} risk flags")
"""))

cells.append(md("""\
---
## Why the handoff layer matters

| | Case 1 — DSPy Handoff | Case 2 — System Instructions |
|---|---|---|
| **Handoff content** | Agent-1 JSON + per-field `fill_instructions` written by DSPy | Agent-1 JSON + static instruction block |
| **Instructions for Agent-2** | Targeted — DSPy tells Agent-2 *how* to fill each specific field | Generic — Agent-2 figures out the strategy itself |
| **Failure mode** | If DSPy misclassifies a field's strategy, Agent-2 follows the wrong hint | If Agent-2 misses a field's domain context, it guesses generically |
| **Optimisable?** | Yes — `HandoffSignature` can be compiled with `BootstrapFewShot` | No — static string cannot be automatically improved |
| **LLM calls** | 3 (Agent-1, DSPy, Agent-2) | 2 (Agent-1, Agent-2) |
| **Best for** | Pipelines where field-level guidance improves fill accuracy (complex domains) | Simple, fast deployments with well-understood domains |
"""))

# ─────────────────────────────────────────────────────────────────────────────
# Assemble
# ─────────────────────────────────────────────────────────────────────────────
nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
        "colab": {"provenance": []}
    },
    "cells": cells,
}

OUT = "dspy_vs_direct_handoff.ipynb"
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Saved: {OUT}  ({len(cells)} cells)")
