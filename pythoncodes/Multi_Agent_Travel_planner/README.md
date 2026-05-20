# Multi-Agent Travel Planner

A LangGraph-based multi-agent travel planning system where an **LLM-powered Orchestrator** coordinates specialized agents, validates their outputs, and drives a feedback loop until the plan is ready.

---

## Architecture

```
OrchestratorAgent.py   ← Entry point + LangGraph supervisor loop
                           TravelPlannerState · create_llm · agent stubs (inline)
    │
    └── InputAgent.py  ← Interactive input collection
                           TravelPlannerState · create_llm definitions live here
```

### Agent execution flow

```
START
  │
  ▼
input_collection ──────────────────────────────────────────────────┐
  │                                                                  │ rework
  ▼                                                                  │
orchestrator (LLM supervisor) ◄──── every agent returns here ──────┘
  │
  ├──► weather_agent       ──► orchestrator
  ├──► accommodation_agent ──► orchestrator
  ├──► transportation_agent──► orchestrator
  ├──► itinerary_agent     ──► orchestrator
  ├──► budget_agent        ──► orchestrator
  │
  └──► finalize ──► END
```

### Orchestrator feedback loop

After every agent finishes, the **Orchestrator LLM** evaluates:
- Is the output complete and consistent with the travel data?
- Does it contradict outputs from other agents?
- Are there any concerns flagged by the agent itself?

If issues are found (and the agent has been called fewer than 3 times), the Orchestrator
re-calls the agent with specific `feedback_for_agent`. For `input_agent` rework it also
specifies `fields_to_recollect` so only those fields are re-asked to the user.

---

## File Reference

| File | Purpose |
|---|---|
| `OrchestratorAgent.py` | LangGraph graph + supervisor node + all agent wrapper nodes |
| `InputAgent.py` | Conversational input collection; supports orchestrator rework |
| `InputAgent.py` | `TravelPlannerState`, `create_llm()`, and the `InputAgent` class |
| `README.md` | This file |

---

## Prerequisites

- Python **3.10 or higher**
- An **[OpenAI](https://platform.openai.com/api-keys) API key** (`sk-proj-...`)

---

## Installation

### 1. Create and activate a virtual environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install langchain langchain-core langchain-openai langgraph openai pydantic python-dotenv typing-extensions
```

Pinned versions (tested):

```bash
pip install \
  langchain==0.3.25 \
  langchain-core==0.3.63 \
  langchain-openai==0.3.18 \
  langgraph==0.4.8 \
  openai==1.82.0 \
  pydantic==2.11.4 \
  python-dotenv==1.1.0 \
  typing-extensions==4.13.2
```

---

## Environment Setup

### Option A — `.env` file (recommended)

Create `.env` in `Multi_Agent_Travel_planner/`:

```env
OPENAI_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Add this at the top of `OrchestratorAgent.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Option B — Shell export

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY = "sk-or-v1-xxxx..."

# macOS / Linux
export OPENAI_API_KEY="sk-or-v1-xxxx..."
```

---

## Running

```bash
cd pythoncodes/Multi_Agent_Travel_planner
python OrchestratorAgent.py
```

**What happens:**
1. `InputAgent` greets you and collects 10 trip fields one question at a time.
2. The Orchestrator LLM evaluates the collected data.
3. Each specialized agent runs in sequence; the Orchestrator reviews each output.
4. If issues are found, the relevant agent is re-called with feedback (max 3 times).
5. A final trip plan summary is printed.

---

## Adding a Real Agent

Replace a stub with a real implementation:

**1. Create `WeatherAgent.py`:**

```python
# WeatherAgent.py
from InputAgent import create_llm

def run(travel_data: dict, feedback: str = None) -> dict:
    # Call an LLM / weather API here
    ...
    return {
        "status": "success",
        "forecast": "...",
        "concerns": [],   # ← required key; list any issues the agent detected
    }
```

**2. Update `OrchestratorAgent.py`:**

```python
# Replace the stub import
from WeatherAgent import run as weather_agent_run

# Update weather_agent_node to call it
def weather_agent_node(state: OrchestratorState) -> dict:
    feedback = _latest_feedback(state, "weather_agent")
    result = weather_agent_run(state.get("travel_data", {}), feedback)
    ...
```

> The `"concerns"` key in every agent's output is the signal the Orchestrator uses
> to decide whether to re-call the agent. Always include it (empty list if none).

---

## Required Fields Collected by InputAgent

| Field | What is asked |
|---|---|
| `travel_type` | Solo / Couple / Family / Friends |
| `num_travelers` | Number of travellers |
| `source_location` | Departure city/town |
| `destination` | Destination city / region / country |
| `travel_dates` | Date range (any natural language) |
| `places_to_visit` | Specific landmarks or attractions |
| `transportation_preferences` | Flight / Train / Bus / Road trip / Mixed |
| `food_preferences` | Veg / Non-veg / Vegan / Halal / No preference |
| `trip_budget_luxury` | Budget / Standard / Luxury / Ultra-Luxury |
| `budget` | Total budget with currency (e.g. ₹50,000 or $2,000) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `AuthenticationError` | Verify `OPENAI_API_KEY` is set and valid for OpenRouter |
| Orchestrator loops without finishing | Check `MAX_ITERATIONS_PER_AGENT` in `OrchestratorAgent.py` (default: 3) |
| `RecursionError` in graph | Increase `recursion_limit` in `orchestrator.invoke(...)` (default: 100) |
| `ModuleNotFoundError` | Ensure `.venv` is active and `pip install` completed |
| Agent never produces `"confirmed"` status | Verify the LLM supports `with_structured_output` on your OpenRouter plan |
