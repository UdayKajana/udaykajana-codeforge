"""
InputAgent — collects and validates all trip details from the user.

A plain while-loop conversation: ask one question, get one answer, repeat until
all 10 fields are confirmed. No internal LangGraph needed.

The LLM speaks through two Pydantic models (AgentDecision / TravelDataUpdate)
so it always returns structured, typed data rather than free text.
"""
import json
import os
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

# ── LLM Factory ───────────────────────────────────────────────────────────────

def create_llm(model: str = "gpt-4o-mini", temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

# ── Constants ──────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = [
    "travel_type",
    "num_travelers",
    "source_location",
    "destination",
    "travel_dates",
    "places_to_visit",
    "transportation_preferences",
    "food_preferences",
    "trip_budget_luxury",
    "budget",
]

SYSTEM_PROMPT = """
You are a warm, friendly travel planner assistant. Today's date is {today}.
Collect trip details one question at a time in a natural, conversational way.

────────────────────────────────────────────────
QUESTION ORDER & HOW TO ASK
────────────────────────────────────────────────
Ask fields in this order, skipping already-collected ones:

  1. travel_type       — "Are you travelling Solo, as a Couple, with Family, or with Friends/Group?"
  2. num_travelers     — Ask based on travel_type context:
                         Solo → confirm it's just them (num=1)
                         Couple → confirm 2, or ask if more
                         Family/Friends → "How many people in total, including yourself?"
  3. source_location   — "Which city or town are you starting from?"
  4. destination       — "Where are you heading? (city, region, or country)"
  5. travel_dates      — "When are you planning to travel?"
                         Accept ANY natural language: "next Monday to Friday",
                         "last week of June", "26th to 30th July", "next weekend" etc.
                         Resolve relative dates using today's date and store as "YYYY-MM-DD to YYYY-MM-DD".
  6. places_to_visit   — "Any specific places, landmarks, or attractions you'd like to cover?"
                         These can be anywhere within the COUNTRY of the destination — not limited to the city.
                         Example: destination = Mumbai → places can include Goa, Pune, Ajanta Caves (all in India).
                         Only flag if a place is in a completely different country.
  7. transportation_preferences — "How would you prefer to travel? (Flight / Train / Bus / Road trip / Mixed)"
  8. food_preferences  — "Any food preferences or dietary needs? (Veg / Non-veg / Vegan / Halal / No preference)"
  9. trip_budget_luxury — "What's your comfort level? (Budget / Standard / Luxury / Ultra-Luxury)"
  10. budget           — "What's your total budget for this trip? (please include currency, e.g. ₹50,000 or $2,000)"

────────────────────────────────────────────────
INLINE VALIDATION (reject and re-ask immediately)
────────────────────────────────────────────────
  ✗ source_location == destination → "Looks like source and destination are the same — where are you heading?"
  ✗ num_travelers ≤ 0 → "That doesn't seem right — how many people are travelling?"
  ✗ travel_dates fully in the past → "Those dates have already passed — when are you planning to go?"
  ✗ budget < ~₹500 / $10 for any trip → "That budget seems too low for travel — could you share a realistic number?"
  Keep all rejection messages to one friendly sentence.

────────────────────────────────────────────────
HOLISTIC VALIDATION (run once ALL fields are collected)
────────────────────────────────────────────────
Check and add a short note to validation_issues for each problem found:

  • Budget reality    — Is budget reasonable for destination + duration + num_travelers + luxury tier?
  • Luxury mismatch  — Does trip_budget_luxury match the budget?
  • Geographic outlier — Are places_to_visit within the destination COUNTRY?
  • Travel type mismatch — Does travel_type match num_travelers?
  • Duration check   — Is the trip long enough to cover all listed places?

If issues found → status = "validating", list issues briefly, ask user to confirm or correct.
If all clear    → status = "confirmed", say: "All good — ready to plan your trip! ✈️"

────────────────────────────────────────────────
RE-COLLECTION (if user fixes something)
────────────────────────────────────────────────
- Ask only for the fields that need correction.
- Re-run holistic validation after each correction.
- Repeat until confirmed.

RULES:
- One short message at a time — never ask two questions together.
- Sound like a helpful friend, not a form.
- Accept casual / shorthand answers and extract the right value.
- Only put newly provided/updated values in field_updates.
- Never echo back all collected data unless the user asks.
- Don't ask the questions repeatedly if the correct answer is already provided.
"""

# ── Structured LLM Output Models ──────────────────────────────────────────────
# These tell the LLM exactly what shape to return.
# travel_data dict uses these field names as keys.

class TravelDataUpdate(BaseModel):
    """Fields the user just provided — only set the ones answered in this turn."""
    travel_type: Optional[str] = None
    num_travelers: Optional[int] = None
    source_location: Optional[str] = None
    destination: Optional[str] = None
    travel_dates: Optional[str] = None
    places_to_visit: Optional[list[str]] = None
    transportation_preferences: Optional[str] = None
    food_preferences: Optional[str] = None
    trip_budget_luxury: Optional[str] = None
    budget: Optional[str] = None


class AgentDecision(BaseModel):
    message_to_user: str = Field(
        description="The next question or validation message to show the user"
    )
    field_updates: TravelDataUpdate = Field(
        default_factory=TravelDataUpdate,
        description="Fields extracted from the user's latest reply — only set ones just provided"
    )
    validation_issues: list[str] = Field(
        default_factory=list,
        description="Holistic issues found (empty if none)"
    )
    status: str = Field(
        description="'collecting' | 'validating' | 'confirmed'"
    )


# ── InputAgent ────────────────────────────────────────────────────────────────

class InputAgent:
    """
    Conversational agent that collects all 10 trip fields from the user.

    Internally just a while loop:
        ask → print question → get user input → update travel_data → repeat

    Returns a single dict:
        {
            "travel_data":  { field: value, ... },   ← all 10 answers
            "status":       "confirmed",
            "issues":       [],
            "summary":      "one-line description of the trip"
        }
    """

    def __init__(self):
        self._llm = create_llm().with_structured_output(AgentDecision)

    def run(
        self,
        initial_data: dict = None,
        orchestrator_feedback: str = None,
        fields_to_recollect: list[str] = None,
    ) -> dict:
        # Start from existing data; drop any fields that need re-collecting
        travel_data = dict(initial_data or {})
        for field in (fields_to_recollect or []):
            travel_data.pop(field, None)

        # Build the opening message
        is_rework = bool(orchestrator_feedback or fields_to_recollect)
        if is_rework:
            fields_str = ", ".join(fields_to_recollect or ["some details"])
            opening = (
                f"Hi again! Our planner flagged an issue: {orchestrator_feedback}. "
                f"Could we revisit {fields_str}?"
            )
        else:
            opening = "Hi, I want to plan a trip."

        print("\n" + "=" * 55)
        print("   INPUT AGENT — Collecting Your Trip Details")
        if is_rework:
            print("   (Rework requested by Orchestrator)")
        print("=" * 55)

        # Conversation history: list of HumanMessage / AIMessage
        history = [HumanMessage(content=opening)]
        last_response = None

        while True:
            missing = [f for f in REQUIRED_FIELDS if f not in travel_data]

            system = SystemMessage(content=(
                f"{SYSTEM_PROMPT.format(today=date.today().strftime('%A, %d %B %Y'))}\n\n"
                f"--- CURRENT DATA ---\n{json.dumps(travel_data, indent=2)}\n\n"
                f"--- MISSING ---\n"
                f"{missing if missing else 'None — run holistic validation now.'}"
            ))

            last_response: AgentDecision = self._llm.invoke([system] + history)

            # Merge newly confirmed fields into travel_data
            new_fields = {
                k: v
                for k, v in last_response.field_updates.model_dump().items()
                if v is not None
            }
            travel_data.update(new_fields)

            print(f"\nPlanner: {last_response.message_to_user}\n")

            if last_response.status == "confirmed":
                break

            user_input = input("You: ").strip()
            history.append(AIMessage(content=last_response.message_to_user))
            history.append(HumanMessage(content=user_input))

        print("\n" + "=" * 55)
        print("   INPUT AGENT — Collection Complete")
        print("=" * 55)

        return {
            "travel_data": travel_data,
            "status": "confirmed",
            "issues": last_response.validation_issues if last_response else [],
            "summary": f"Trip: {travel_data.get('travel_type', '')} | "
                       f"{travel_data.get('source_location', '')} → {travel_data.get('destination', '')} | "
                       f"{travel_data.get('travel_dates', '')} | "
                       f"{travel_data.get('num_travelers', '')} traveller(s) | "
                       f"Budget: {travel_data.get('budget', '')}",
        }
