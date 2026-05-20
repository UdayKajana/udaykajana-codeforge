import json
from typing import Optional
from dotenv import load_dotenv
load_dotenv()  # loads OPENAI_API_KEY from .env before any LLM client is created
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from InputAgent import InputAgent, create_llm
from langgraph.graph import StateGraph, START, END

# ── Agent Stubs ────────────────────────────────────────────────────────────────
# Replace each function body with a real agent call once the agent file is ready.
# Contract: (travel_data, feedback) -> dict with a "concerns": list[str] key.

def weather_agent_stub(travel_data: dict, feedback: str = None) -> dict:
    return {
        "status": "placeholder",
        "destination": travel_data.get("destination"),
        "travel_dates": travel_data.get("travel_dates"),
        "received_feedback": feedback,
        "forecast": "Weather agent not yet implemented.",
        "concerns": [],
    }

def accommodation_agent_stub(travel_data: dict, feedback: str = None) -> dict:
    return {
        "status": "placeholder",
        "destination": travel_data.get("destination"),
        "received_feedback": feedback,
        "message": "Accommodation agent not yet implemented.",
        "concerns": [],
    }

def transportation_agent_stub(travel_data: dict, feedback: str = None) -> dict:
    return {
        "status": "placeholder",
        "preference": travel_data.get("transportation_preferences"),
        "received_feedback": feedback,
        "message": "Transportation agent not yet implemented.",
        "concerns": [],
    }

def itinerary_agent_stub(travel_data: dict, feedback: str = None) -> dict:
    return {
        "status": "placeholder",
        "destination": travel_data.get("destination"),
        "travel_dates": travel_data.get("travel_dates"),
        "received_feedback": feedback,
        "message": "Itinerary agent not yet implemented.",
        "concerns": [],
    }

def budget_agent_stub(travel_data: dict, feedback: str = None) -> dict:
    return {
        "status": "placeholder",
        "total_budget": travel_data.get("budget"),
        "received_feedback": feedback,
        "message": "Budget agent not yet implemented.",
        "concerns": [],
    }

# ── Config ─────────────────────────────────────────────────────────────────────

MAX_ITERATIONS_PER_AGENT = 3

# Maps the LLM's next_agent value → the graph node name.
# Update this when new agent nodes are added.
AGENT_NODE_MAP: dict[str, str] = {
    "input_agent":          "input_collection",
    "weather_agent":        "weather_agent",
    "accommodation_agent":  "accommodation_agent",
    "transportation_agent": "transportation_agent",
    "itinerary_agent":      "itinerary_agent",
    "budget_agent":         "budget_agent",
    "finalize":             "finalize",
}

# ── Orchestrator State ─────────────────────────────────────────────────────────
# Single source of truth for the entire workflow.
# Every agent reads travel_data and writes only to its own named output field.

class OrchestratorState(TypedDict):
    # ── Collected trip details (InputAgent writes here) ───────────────────────
    travel_data: dict
    input_summary: Optional[str]           # one-line trip description from InputAgent

    # ── Per-agent outputs (each agent owns exactly one field) ─────────────────
    weather_output: Optional[dict]
    accommodation_output: Optional[dict]
    transportation_output: Optional[dict]
    itinerary_output: Optional[dict]
    budget_output: Optional[dict]

    # ── Orchestrator control (supervisor reads/writes these) ──────────────────
    agent_feedback: dict                   # { agent_name: [feedback_str, ...] }
    iteration_counts: dict                 # { agent_name: int }
    fields_to_recollect: Optional[list[str]]
    next_agent: str
    orchestrator_reasoning: str
    issues_log: list[str]
    is_complete: bool
    final_summary: Optional[str]

# ── Supervisor LLM Output Model ────────────────────────────────────────────────

class OrchestratorDecision(BaseModel):
    reasoning: str = Field(
        description="Step-by-step analysis: what has been done, what quality issues exist, "
                    "and why you chose the next action."
    )
    next_agent: str = Field(
        description=(
            "Exact name of the next agent to call, or 'finalize' to end. "
            "Valid values: input_agent, weather_agent, accommodation_agent, "
            "transportation_agent, itinerary_agent, budget_agent, finalize."
        )
    )
    feedback_for_agent: Optional[str] = Field(
        default=None,
        description="When calling an agent for rework: precise, actionable feedback "
                    "describing what to fix. Leave null for first-time calls."
    )
    fields_to_recollect: Optional[list[str]] = Field(
        default=None,
        description=(
            "Only for input_agent rework: list of field names the user must re-provide. "
            "Valid field names: travel_type, num_travelers, source_location, destination, "
            "travel_dates, places_to_visit, transportation_preferences, food_preferences, "
            "trip_budget_luxury, budget."
        )
    )
    issues_found: list[str] = Field(
        default_factory=list,
        description="Quality issues or inconsistencies identified in this evaluation round."
    )
    final_summary: Optional[str] = Field(
        default=None,
        description="Only when next_agent='finalize': a 4-6 sentence human-readable trip "
                    "plan synthesizing travel_data and all agent outputs."
    )

# ── Supervisor System Prompt ───────────────────────────────────────────────────

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Master Orchestrator for a multi-agent travel planning system.
Your role is to coordinate specialized agents, critically evaluate their outputs, and guide
the system toward a complete, high-quality travel plan.

════════════════════════════════════════════════
AVAILABLE AGENTS  (use exact names in next_agent)
════════════════════════════════════════════════
  input_agent          — Interactive: collects & validates all 10 trip fields from the user.
                         Re-call with feedback + fields_to_recollect if travel_data has issues.
  weather_agent        — Fetches weather forecast for destination + travel dates. (Placeholder)
  accommodation_agent  — Finds accommodation options. (Placeholder)
  transportation_agent — Plans transportation. (Placeholder)
  itinerary_agent      — Builds day-by-day itinerary. (Placeholder)
  budget_agent         — Breaks down budget allocation. (Placeholder)
  finalize             — Ends planning; you MUST provide final_summary.

════════════════════════════════════════════════
CURRENT STATE
════════════════════════════════════════════════
Travel Data:
{travel_data}

Agent Outputs So Far:
{agent_outputs}

Times Each Agent Has Been Called:
{iteration_counts}

Issues Logged So Far:
{issues_log}

════════════════════════════════════════════════
DECISION RULES
════════════════════════════════════════════════
1. ALWAYS start with input_agent if travel_data is empty or incomplete.

2. After input is collected, run agents in this order (skip already-completed ones):
   weather_agent → accommodation_agent → transportation_agent →
   itinerary_agent → budget_agent → finalize

3. After each agent runs, check its output for:
   • Completeness — did it return meaningful data?
   • Consistency with travel_data — dates, destination, budget, traveler count?
   • Internal contradictions with other agent outputs?
   • Any "concerns" listed in the agent's own output?

4. If an agent's output has issues AND iteration_counts[agent] < {max_iter}:
   → Re-call that agent. Set feedback_for_agent to exactly what needs to be fixed.
   → For input_agent rework: also set fields_to_recollect.

5. If iteration_counts[agent] >= {max_iter}: accept output as-is and move on.

6. Call "finalize" only when ALL available agents have run with acceptable outputs.
   In final_summary: write a specific, helpful 4-6 sentence travel plan using
   the collected data and agent outputs.

════════════════════════════════════════════════
IMPORTANT
════════════════════════════════════════════════
- Placeholder agents (status="placeholder") are acceptable — just note them in reasoning.
- Be concise but precise in feedback_for_agent.
- Never loop forever — respect the iteration cap.
"""

# ── Agent Instances (created once at startup) ─────────────────────────────────

_input_agent = InputAgent()
_supervisor_llm = create_llm(temperature=0).with_structured_output(OrchestratorDecision)

# ── Helper ─────────────────────────────────────────────────────────────────────

def _build_supervisor_prompt(state: OrchestratorState) -> str:
    # Collect only the agent outputs that have actually run (non-None)
    agent_outputs = {
        name: state.get(field)
        for name, field in {
            "weather_agent":        "weather_output",
            "accommodation_agent":  "accommodation_output",
            "transportation_agent": "transportation_output",
            "itinerary_agent":      "itinerary_output",
            "budget_agent":         "budget_output",
        }.items()
        if state.get(field) is not None
    }
    return ORCHESTRATOR_SYSTEM_PROMPT.format(
        travel_data=json.dumps(state.get("travel_data", {}), indent=2),
        agent_outputs=json.dumps(agent_outputs, indent=2) if agent_outputs else "None yet",
        iteration_counts=json.dumps(state.get("iteration_counts", {}), indent=2),
        issues_log=json.dumps(state.get("issues_log", []), indent=2),
        max_iter=MAX_ITERATIONS_PER_AGENT,
    )

def _latest_feedback(state: OrchestratorState, agent_name: str) -> Optional[str]:
    history = state.get("agent_feedback", {}).get(agent_name, [])
    return history[-1] if history else None

def _bump_count(state: OrchestratorState, agent_name: str) -> dict:
    counts = dict(state.get("iteration_counts", {}))
    counts[agent_name] = counts.get(agent_name, 0) + 1
    return counts

# ── Supervisor Node ────────────────────────────────────────────────────────────

def orchestrator_supervisor_node(state: OrchestratorState) -> dict:
    """LLM-powered decision node: evaluates current state and decides next action."""
    print("\n[Orchestrator] Evaluating state...")

    decision: OrchestratorDecision = _supervisor_llm.invoke([
        SystemMessage(content=_build_supervisor_prompt(state)),
        HumanMessage(content="Evaluate the current state and decide the next action."),
    ])

    print(f"[Orchestrator] → Next: {decision.next_agent}")
    print(f"[Orchestrator]   Reasoning: {decision.reasoning[:120]}{'...' if len(decision.reasoning) > 120 else ''}")
    if decision.issues_found:
        for issue in decision.issues_found:
            print(f"[Orchestrator]   Issue: {issue}")

    # Append new feedback to the chosen agent's history
    current_feedback = dict(state.get("agent_feedback", {}))
    if decision.feedback_for_agent:
        history = list(current_feedback.get(decision.next_agent, []))
        history.append(decision.feedback_for_agent)
        current_feedback[decision.next_agent] = history

    return {
        "next_agent": decision.next_agent,
        "orchestrator_reasoning": decision.reasoning,
        "issues_log": state.get("issues_log", []) + decision.issues_found,
        "agent_feedback": current_feedback,
        "fields_to_recollect": decision.fields_to_recollect,
        "is_complete": decision.next_agent == "finalize",
        "final_summary": decision.final_summary,
    }

# ── Agent Nodes ────────────────────────────────────────────────────────────────

def input_collection_node(state: OrchestratorState) -> dict:
    result = _input_agent.run(
        initial_data=state.get("travel_data") or {},
        orchestrator_feedback=_latest_feedback(state, "input_agent"),
        fields_to_recollect=state.get("fields_to_recollect"),
    )
    print(f"\n[InputAgent] {result['summary']}")
    return {
        "travel_data":        result["travel_data"],
        "input_summary":      result["summary"],
        "iteration_counts":   _bump_count(state, "input_agent"),
        "fields_to_recollect": None,
    }


def weather_agent_node(state: OrchestratorState) -> dict:
    result = weather_agent_stub(
        state.get("travel_data", {}), _latest_feedback(state, "weather_agent")
    )
    print(f"[WeatherAgent] Done. Status: {result.get('status')}")
    return {"weather_output": result, "iteration_counts": _bump_count(state, "weather_agent")}


def accommodation_agent_node(state: OrchestratorState) -> dict:
    result = accommodation_agent_stub(
        state.get("travel_data", {}), _latest_feedback(state, "accommodation_agent")
    )
    print(f"[AccommodationAgent] Done. Status: {result.get('status')}")
    return {"accommodation_output": result, "iteration_counts": _bump_count(state, "accommodation_agent")}


def transportation_agent_node(state: OrchestratorState) -> dict:
    result = transportation_agent_stub(
        state.get("travel_data", {}), _latest_feedback(state, "transportation_agent")
    )
    print(f"[TransportationAgent] Done. Status: {result.get('status')}")
    return {"transportation_output": result, "iteration_counts": _bump_count(state, "transportation_agent")}


def itinerary_agent_node(state: OrchestratorState) -> dict:
    result = itinerary_agent_stub(
        state.get("travel_data", {}), _latest_feedback(state, "itinerary_agent")
    )
    print(f"[ItineraryAgent] Done. Status: {result.get('status')}")
    return {"itinerary_output": result, "iteration_counts": _bump_count(state, "itinerary_agent")}


def budget_agent_node(state: OrchestratorState) -> dict:
    result = budget_agent_stub(
        state.get("travel_data", {}), _latest_feedback(state, "budget_agent")
    )
    print(f"[BudgetAgent] Done. Status: {result.get('status')}")
    return {"budget_output": result, "iteration_counts": _bump_count(state, "budget_agent")}


def finalize_node(state: OrchestratorState) -> dict:
    print("\n" + "=" * 60)
    print("   TRAVEL PLAN — FINAL SUMMARY")
    print("=" * 60)
    print(f"\n{state.get('final_summary') or 'Trip planning complete.'}\n")

    print("─" * 60)
    print("Trip Details:")
    print(json.dumps(state.get("travel_data", {}), indent=2))

    for label, field in [
        ("Weather",        "weather_output"),
        ("Accommodation",  "accommodation_output"),
        ("Transportation", "transportation_output"),
        ("Itinerary",      "itinerary_output"),
        ("Budget",         "budget_output"),
    ]:
        if state.get(field):
            print(f"\n{label} Output:")
            print(json.dumps(state[field], indent=2))

    if state.get("issues_log"):
        print("\nIssues encountered during planning:")
        for issue in state["issues_log"]:
            print(f"  • {issue}")

    print("=" * 60)
    return {"is_complete": True}

# ── Routing ────────────────────────────────────────────────────────────────────

def route_from_supervisor(state: OrchestratorState) -> str:
    next_agent = state.get("next_agent", "finalize")
    node_name = AGENT_NODE_MAP.get(next_agent, "finalize")

    # Hard safety cap: if an agent has already hit the iteration limit, finalize
    if node_name != "finalize":
        count = state.get("iteration_counts", {}).get(next_agent, 0)
        if count >= MAX_ITERATIONS_PER_AGENT:
            print(
                f"\n[Orchestrator] Safety cap: {next_agent} already called "
                f"{count}×. Forcing finalize."
            )
            return "finalize"

    return node_name

# ── Graph ──────────────────────────────────────────────────────────────────────

def build_orchestrator():
    graph = StateGraph(OrchestratorState)
    # Register all nodes
    graph.add_node("input_collection",    input_collection_node)
    graph.add_node("orchestrator",        orchestrator_supervisor_node)
    graph.add_node("weather_agent",       weather_agent_node)
    graph.add_node("accommodation_agent", accommodation_agent_node)
    graph.add_node("transportation_agent",transportation_agent_node)
    graph.add_node("itinerary_agent",     itinerary_agent_node)
    graph.add_node("budget_agent",        budget_agent_node)
    graph.add_node("finalize",            finalize_node)

    # Input always runs first, then supervisor takes over
    graph.add_edge(START, "input_collection")
    graph.add_edge("input_collection", "orchestrator")

    # Supervisor decides where to go; every agent returns to supervisor
    graph.add_conditional_edges(
        "orchestrator",
        route_from_supervisor,
        {v: v for v in AGENT_NODE_MAP.values()},  # identity mapping for all nodes
    )
    for agent_node in [
        "weather_agent", "accommodation_agent", "transportation_agent",
        "itinerary_agent", "budget_agent",
    ]:
        graph.add_edge(agent_node, "orchestrator")

    # input_collection loops back to supervisor (for rework) as well
    # Note: input_collection already has its edge from START; add the re-entry edge
    graph.add_edge("finalize", END)

    return graph.compile()

# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("   MULTI-AGENT TRAVEL PLANNER")
    print("=" * 60)

    orchestrator = build_orchestrator()

    initial_state: OrchestratorState = {
        # trip details
        "travel_data":           {},
        "input_summary":         None,
        # agent outputs — each starts empty; agents write here
        "weather_output":        None,
        "accommodation_output":  None,
        "transportation_output": None,
        "itinerary_output":      None,
        "budget_output":         None,
        # orchestrator control
        "agent_feedback":        {},
        "iteration_counts":      {},
        "fields_to_recollect":   None,
        "next_agent":            "",
        "orchestrator_reasoning": "",
        "issues_log":            [],
        "is_complete":           False,
        "final_summary":         None,
    }

    final_state = orchestrator.invoke(initial_state, config={"recursion_limit": 100})
    return final_state


if __name__ == "__main__":
    main()
