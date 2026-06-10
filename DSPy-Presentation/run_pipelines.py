#!/usr/bin/env python3
"""
Run both extraction pipelines:
  A — Naive prompt-based (direct Azure OpenAI call, no DSPy)
  B — DSPy with BootstrapFewShot optimizer (Azure gpt-4o)
"""
import os
import re
import json
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent

AZURE_API_KEY     = os.environ.get('AZURE_API_KEY',     'AZURE_API_KEY')
AZURE_ENDPOINT    = os.environ.get('AZURE_ENDPOINT',    'https://synapt-softbank.openai.azure.com')
AZURE_API_VERSION = os.environ.get('AZURE_API_VERSION', '2025-01-01-preview')
AZURE_DEPLOYMENT  = os.environ.get('AZURE_DEPLOYMENT',  'gpt-4o')


def load_email(path):
    return json.loads(Path(path).read_text(encoding='utf-8')).get('email', '')


def run_prompt_pipeline(email_text, api_key=None):
    """Pipeline A — direct Azure OpenAI prompt, no DSPy."""
    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=api_key or AZURE_API_KEY,
            api_version=AZURE_API_VERSION,
            azure_endpoint=AZURE_ENDPOINT,
        )
        system_prompt = (
            'You are a JSON extractor for Japanese bidding emails.\n'
            'Extract ONLY the CURRENT bid (ignore any previous bid history in the email).\n'
            'Return a JSON object with exactly these keys:\n'
            '  bidder       (str)             — company name\n'
            '  items        (list of objects) — [{name, version}]\n'
            '  quantity     (int|null)         — current bid quantity\n'
            '  unit_price   (object)           — {amount: number|null, currency: str}\n'
            '  deadline     (str|null)         — ISO date YYYY-MM-DD or null\n'
            '  terms        (str|null)         — payment terms e.g. NET30\n'
            'If a field is missing or ambiguous, use null.'
        )
        resp = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': email_text},
            ],
            temperature=0,
        )
        content = resp.choices[0].message.content
        try:
            m = re.search(r'\{.*\}', content, re.DOTALL)
            parsed = json.loads(m.group(0) if m else content)
        except Exception:
            parsed = {'raw_text': content}
        return {
            'prompt': system_prompt,
            'response_raw': content,
            'parsed': parsed,
            'backend': 'azure_openai',
        }

    except Exception as e:
        sys.path.insert(0, str(ROOT))
        from dspy.dspy_demo import NaiveExtractor
        extractor = NaiveExtractor()
        result = extractor.extract(email_text)
        cot = result.pop('__chain_of_thought', '')
        return {
            'prompt': 'DSPy Predict (NaiveExtractor — no CoT)',
            'response_raw': json.dumps(result, ensure_ascii=False, indent=2),
            'parsed': result,
            'chain_of_thought': cot,
            'warning': str(e),
            'backend': 'dspy_naive',
        }


def run_dspy_pipeline(email_text):
    """Pipeline B — DSPy with BootstrapFewShot optimizer (Azure gpt-4o)."""
    sys.path.insert(0, str(ROOT))
    from dspy.dspy_demo import run_full_pipeline
    return run_full_pipeline(email_text)


def get_pipeline_results(email_text, api_key=None):
    prompt_out = run_prompt_pipeline(email_text, api_key=api_key)
    dspy_out   = run_dspy_pipeline(email_text)
    return {'prompt_pipeline': prompt_out, 'dspy_pipeline': dspy_out}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', default=str(ROOT / 'data' / 'email.json'))
    args = parser.parse_args()
    email_text = load_email(args.email)

    print('\n=== Pipeline A — Without DSPy (Azure direct prompt) ===')
    a = run_prompt_pipeline(email_text)
    print('Backend:', a['backend'])
    print(json.dumps(a['parsed'], ensure_ascii=False, indent=2))

    print('\n=== Pipeline B — With DSPy + BootstrapFewShot (Azure gpt-4o) ===')
    b = run_dspy_pipeline(email_text)
    print('Backend:', b.get('backend'))
    if 'pre_optimizer' in b:
        print('\n-- Pre-optimizer --')
        print(json.dumps(b['pre_optimizer']['result'], ensure_ascii=False, indent=2))
        print('\n-- Training --')
        print(json.dumps(b['training'], ensure_ascii=False, indent=2))
        print('\n-- Post-optimizer --')
        print(json.dumps(b['post_optimizer']['result'], ensure_ascii=False, indent=2))
        print('\n-- Improvements --')
        for imp in b.get('improvements', []):
            print('  OK', imp)
    else:
        print(json.dumps(b.get('result', b), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
