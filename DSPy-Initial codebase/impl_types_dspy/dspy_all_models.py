import os
import sys
import time

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

# ── 3. DSPy Signature ─────────────────────────────────────────────────────────
class QA(dspy.Signature):
    """Answer the question with reasoning."""
    question: str = dspy.InputField()
    reasoning: str = dspy.OutputField(desc="Step-by-step thought process")
    answer: str = dspy.OutputField(desc="Final concise answer")

# ── 4. Define tools for ReAct ─────────────────────────────────────────────────
def calculator_tool(expression: str) -> str:
    """Simple tool for ReAct to evaluate mathematical expressions."""
    try:
        result = eval(expression, {'__builtins__': None}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# ── 5. Pipeline Instances ────────────────────────────────────────────────────
cot_pipeline = dspy.ChainOfThought(QA)
react_pipeline = dspy.ReAct(QA, tools=[calculator_tool])

# ── 6. Methods for different modes ────────────────────────────────────────────

def normal_mode(question):
    """Query OpenAI directly without DSPy."""
    prompt = f"Answer the question: {question}"
    start_time = time.time()
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    
    end_time = time.time()
    answer = response.choices[0].message.content.strip()
    tokens = response.usage.total_tokens if hasattr(response, 'usage') else 0
    
    return {
        'answer': answer,
        'prompt': prompt,
        'time': end_time - start_time,
        'tokens': tokens,
        'mode': 'Normal (No DSPy)'
    }

def dspy_cot_mode(question):
    """Query using DSPy ChainOfThought."""
    start_time = time.time()
    result = cot_pipeline(question=question)
    end_time = time.time()
    
    # Get prompt from DSPy history
    prompt = "Prompt not available"
    if lm.history:
        try:
            messages = lm.history[-1].get('messages', [])
            prompt = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages])
        except:
            pass
    
    # Estimate tokens
    tokens = len(prompt.split()) + len(result.answer.split()) if result.answer else 0
    
    return {
        'answer': result.answer if hasattr(result, 'answer') else result,
        'reasoning': result.reasoning if hasattr(result, 'reasoning') else '',
        'prompt': prompt,
        'time': end_time - start_time,
        'tokens': tokens,
        'mode': 'DSPy ChainOfThought'
    }

def dspy_react_mode(question):
    """Query using DSPy ReAct."""
    start_time = time.time()
    result = react_pipeline(question=question)
    end_time = time.time()
    
    # Get prompt from DSPy history
    prompt = "Prompt not available"
    if lm.history:
        try:
            messages = lm.history[-1].get('messages', [])
            prompt = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages])
        except:
            pass
    
    # Estimate tokens
    tokens = len(prompt.split()) + len(result.answer.split()) if result.answer else 0
    
    return {
        'answer': result.answer if hasattr(result, 'answer') else result,
        'prompt': prompt,
        'time': end_time - start_time,
        'tokens': tokens,
        'mode': 'DSPy ReAct'
    }

# ── 7. Statistics Collection ──────────────────────────────────────────────────

def run_comparison(questions):
    """Run all three modes on given questions and collect statistics."""
    results = {}
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"Question {i}: {question}")
        print('='*70)
        
        results[question] = {}
        
        # Normal Mode
        try:
            print("\n[1] NORMAL MODE (No DSPy)")
            print("-" * 70)
            normal_result = normal_mode(question)
            results[question]['normal'] = normal_result
            print(f"Prompt: {normal_result['prompt']}")
            print(f"Answer: {normal_result['answer']}")
            print(f"Time: {normal_result['time']:.3f}s | Tokens: {normal_result['tokens']}")
        except Exception as e:
            print(f"Error in Normal Mode: {e}")
            results[question]['normal'] = {'error': str(e)}
        
        # DSPy CoT Mode
        try:
            print("\n[2] DSPy ChainOfThought Mode")
            print("-" * 70)
            cot_result = dspy_cot_mode(question)
            results[question]['cot'] = cot_result
            print(f"Prompt: {cot_result['prompt']}")
            if cot_result.get('reasoning'):
                print(f"Reasoning: {cot_result['reasoning']}")
            print(f"Answer: {cot_result['answer']}")
            print(f"Time: {cot_result['time']:.3f}s | Tokens: {cot_result['tokens']}")
        except Exception as e:
            print(f"Error in CoT Mode: {e}")
            results[question]['cot'] = {'error': str(e)}
        
        # DSPy ReAct Mode
        try:
            print("\n[3] DSPy ReAct Mode")
            print("-" * 70)
            react_result = dspy_react_mode(question)
            results[question]['react'] = react_result
            print(f"Prompt: {react_result['prompt'].strip()}")
            print(f"Answer: {react_result['answer']}")
            print(f"Time: {react_result['time']:.3f}s | Tokens: {react_result['tokens']}")
        except Exception as e:
            print(f"Error in ReAct Mode: {e}")
            results[question]['react'] = {'error': str(e)}
    
    return results

def print_statistics(results):
    """Print aggregated statistics across all questions."""
    print(f"\n\n{'='*70}")
    print("STATISTICS SUMMARY")
    print('='*70)
    
    modes = ['normal', 'cot', 'react']
    stats = {mode: {'time': 0, 'tokens': 0, 'count': 0} for mode in modes}
    
    for question, mode_results in results.items():
        for mode in modes:
            if mode in mode_results and 'error' not in mode_results[mode]:
                stats[mode]['time'] += mode_results[mode]['time']
                stats[mode]['tokens'] += mode_results[mode]['tokens']
                stats[mode]['count'] += 1
    
    print(f"\n{'Mode':<25} {'Total Time':<15} {'Total Tokens':<15} {'Queries':<10}")
    print("-" * 65)
    
    for mode in modes:
        mode_label = {
            'normal': 'Normal (No DSPy)',
            'cot': 'DSPy ChainOfThought',
            'react': 'DSPy ReAct'
        }[mode]
        
        if stats[mode]['count'] > 0:
            avg_time = stats[mode]['time'] / stats[mode]['count']
            print(f"{mode_label:<25} {stats[mode]['time']:<14.3f}s {stats[mode]['tokens']:<14} {stats[mode]['count']:<10}")
    
    # Determine best mode based on time
    valid_modes = {m: stats[m]['time'] for m in modes if stats[m]['count'] > 0}
    if valid_modes:
        best_mode = min(valid_modes, key=valid_modes.get)
        best_label = {
            'normal': 'Normal (No DSPy)',
            'cot': 'DSPy ChainOfThought',
            'react': 'DSPy ReAct'
        }[best_mode]
        print("\n" + "-" * 65)
        print(f"✓ Best by Speed: {best_label}")

# ── 8. Main Execution ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Sample questions for testing
    questions = [
        "What happens if I drink coffee at night?",
        "Explain possible reasons for laptop heating.",
        "What famous people are from Hyderabad?"
    ]
    
    print("\n🚀 DSPy Comparison: Normal vs ChainOfThought vs ReAct")
    print("=" * 70)
    
    # Run comparison
    results = run_comparison(questions)
    
    # Print statistics
    print_statistics(results)
    
    print("\n✓ Comparison complete!")

