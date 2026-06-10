import os
import sys

import dspy
from openai import OpenAI

# ── 1. Check API key ──────────────────────────────────────────────────────────
api_key = os.environ.get("OPENAI_API_KEY", "").strip()
if not api_key:
    print("ERROR: Set OPENAI_API_KEY before running.")
    print("  export OPENAI_API_KEY=sk-...")
    sys.exit(1)

client = OpenAI(api_key=api_key)

# ── 2. Configure DSPy with OpenAI ─────────────────────────────────────────────
lm = dspy.LM(model="openai/gpt-4o-mini", api_key=api_key)
dspy.configure(lm=lm)

# ── 3. DSPy Module ────────────────────────────────────────────────────────────
class QA(dspy.Signature):
    """Answer the question with reasoning."""
    question: str = dspy.InputField()
    reasoning: str = dspy.OutputField(desc="Step-by-step thought process")
    answer:    str = dspy.OutputField(desc="Final concise answer")

pipeline = dspy.ChainOfThought(QA)

# ── 4. Main loop ──────────────────────────────────────────────────────────────
print("DSPy - OpenAI — type a question, 'quit' to exit.\n")

while True:
    try:
        question = input("❯ ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
        break

    if not question:
        continue
    if question.lower() in ("quit", "exit", "q"):
        print("\nBye!")
        break

    try:
        # Without DSPy
        prompt_without = f"Answer the question: {question}"
        print("Without DSPy:")
        print(f"Prompt: {prompt_without}")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_without}]
        )
        answer_without = response.choices[0].message.content
        print(f"Answer: {answer_without}")
        print()

        # With DSPy
        print("With DSPy:")
        result = pipeline(question=question)
        # Get the prompt used by DSPy
        if lm.history:
            messages = lm.history[-1].get('messages', [])
            prompt_with = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages])
        else:
            prompt_with = "No history available"
        print(f"Prompt:\n{prompt_with}")
        print(f"Reasoning: {result.reasoning}")
        print(f"Answer: {result.answer}")
        print()

        # Print DSPy trace
        print("\n" + "=" * 60)
        print("DSPy TRACE")
        print("=" * 60)
        for i, item in enumerate(dspy.settings.trace):
            module, inputs, outputs = item
            print(f"Call {i+1}:")
            print(f"  Module: {module}")
            print(f"  Inputs: {inputs}")
            print(f"  Outputs: {outputs}")
            print()

    except Exception as e:
        print(f"\nError: {e}\n")


