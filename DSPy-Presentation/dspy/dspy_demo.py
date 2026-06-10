"""
DSPy pipeline with Azure OpenAI (gpt-4o).
Real LLM calls — ChainOfThought, Suggest, BootstrapFewShot.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ── Bypass local dspy/ shadow so we import the real installed dspy ────────────
_parent_str = str(ROOT.parent)
for _k in [k for k in list(sys.modules) if k == 'dspy' or k.startswith('dspy.')]:
    del sys.modules[_k]
_in_path = _parent_str in sys.path
if _in_path:
    sys.path.remove(_parent_str)
try:
    import dspy
finally:
    if _parent_str not in sys.path:
        sys.path.insert(0, _parent_str)

# ── Azure OpenAI LM configuration ────────────────────────────────────────────
_lm = dspy.LM(
    model='azure/gpt-4o',
    api_key=os.environ.get('AZURE_API_KEY', 'AZURE_API_KEY'),
    api_base=os.environ.get('AZURE_ENDPOINT', 'https://synapt-softbank.openai.azure.com'),
    api_version=os.environ.get('AZURE_API_VERSION', '2025-01-01-preview'),
)
dspy.configure(lm=_lm)


# ── Signature ─────────────────────────────────────────────────────────────────

class BidExtractSignature(dspy.Signature):
    """Extract structured bid information from a Japanese bidding email.
    Focus ONLY on the CURRENT bid. Ignore any previous-bid history sections in the email."""

    email: str = dspy.InputField(
        desc='Raw Japanese bidding email (may contain previous bid history — ignore it)'
    )
    bidder: str = dspy.OutputField(desc='Bidder company name (会社名)')
    item_name: str = dspy.OutputField(desc='Product or item name (製品名 / 品名)')
    quantity: int = dspy.OutputField(
        desc='Current bid quantity as an integer — NOT from any previous-bid section'
    )
    unit_price_amount: float = dspy.OutputField(
        desc='Unit price as a number; use null if price is listed in an attachment'
    )
    unit_price_currency: str = dspy.OutputField(desc='Currency code: JPY, USD, EUR, etc.')
    deadline: str = dspy.OutputField(
        desc='Delivery deadline in ISO format YYYY-MM-DD; null if not found'
    )
    terms: str = dspy.OutputField(
        desc='Payment terms e.g. NET30, NET45, NET60; null if not specified'
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _coerce(pred) -> dict:
    """Normalise a DSPy prediction to the canonical output shape."""
    _null = (None, 'null', 'None', '', 'N/A', 'n/a')

    def _int(v):
        try:
            return int(str(v).replace(',', '').split('.')[0])
        except Exception:
            return None

    def _float(v):
        if v in _null:
            return None
        try:
            return float(str(v).replace(',', ''))
        except Exception:
            return None

    def _str(v):
        return None if v in _null else str(v).strip()

    return {
        'bidder': _str(getattr(pred, 'bidder', None)),
        'items': [{'name': _str(getattr(pred, 'item_name', None)), 'version': None}],
        'quantity': _int(getattr(pred, 'quantity', None)),
        'unit_price': {
            'amount': _float(getattr(pred, 'unit_price_amount', None)),
            'currency': _str(getattr(pred, 'unit_price_currency', None)) or 'JPY',
        },
        'deadline': _str(getattr(pred, 'deadline', None)),
        'terms': _str(getattr(pred, 'terms', None)),
    }


# ── Pipeline A: NaiveExtractor — plain Predict, no CoT, no optimizer ─────────

class NaiveExtractor:
    """Single Predict call — equivalent to a plain prompt without chain-of-thought."""

    def __init__(self):
        self._predict = dspy.Predict(BidExtractSignature)

    def extract(self, email: str) -> dict:
        pred = self._predict(email=email)
        result = _coerce(pred)
        result['__chain_of_thought'] = '[NaiveExtractor] Single direct prediction (no CoT, no optimizer)'
        return result


# ── Pipeline B: DSPy module with ChainOfThought + Suggest ─────────────────────

class DSPyExtractModule(dspy.Module):
    """ChainOfThought extraction with soft Suggest constraints for missing fields."""

    def __init__(self):
        super().__init__()
        self.cot = dspy.ChainOfThought(BidExtractSignature)

    def forward(self, email: str):
        pred = self.cot(email=email)

        dspy.Suggest(
            getattr(pred, 'deadline', None) not in (None, 'null', 'None', ''),
            'Deadline field is missing. Re-read the email and extract '
            'the delivery date in ISO format YYYY-MM-DD.',
        )
        dspy.Suggest(
            getattr(pred, 'quantity', None) not in (None, 'null', 'None', ''),
            'Quantity not found. Look for 数量 or 発注数量 in the CURRENT bid section only.',
        )

        return pred


# ── Training helpers ──────────────────────────────────────────────────────────

def _make_trainset(golden_path: Path):
    raw = json.loads(golden_path.read_text(encoding='utf-8'))
    trainset = []
    for ex in raw:
        e = ex['expected']
        item = (e.get('items') or [{}])[0]
        trainset.append(
            dspy.Example(
                email=ex['email'],
                bidder=str(e.get('bidder') or ''),
                item_name=str(item.get('name') or ''),
                quantity=str(e.get('quantity') or ''),
                unit_price_amount=str((e.get('unit_price') or {}).get('amount') or ''),
                unit_price_currency=str((e.get('unit_price') or {}).get('currency') or 'JPY'),
                deadline=str(e.get('deadline') or ''),
                terms=str(e.get('terms') or ''),
            ).with_inputs('email')
        )
    return trainset


def _accuracy_metric(example, pred, trace=None):  # noqa: ARG001
    score, total = 0, 0
    for field in ('bidder', 'quantity', 'deadline', 'terms'):
        ev = getattr(example, field, None)
        pv = getattr(pred, field, None)
        if ev:
            total += 1
            if str(ev).strip() == str(pv or '').strip():
                score += 1
    return score / total if total else 0.0


# ── Full pipeline: pre-optimizer → train → post-optimizer ────────────────────

def run_full_pipeline(email_text: str) -> dict:
    """Runs DSPyExtractModule before and after BootstrapFewShot compilation."""
    trainset = _make_trainset(ROOT / 'golden_examples.json')

    # Pre-optimizer
    pre_module = DSPyExtractModule()
    pre_pred   = pre_module(email=email_text)
    pre_result = _coerce(pre_pred)
    pre_cot    = str(getattr(pre_pred, 'rationale', '') or '')

    # BootstrapFewShot compilation
    optimizer       = dspy.BootstrapFewShot(metric=_accuracy_metric, max_bootstrapped_demos=3)
    compiled_module = optimizer.compile(DSPyExtractModule(), trainset=trainset)

    training_summary = {
        'examples_used': len(trainset),
        'trainset_size': len(trainset),
        'optimizer': 'BootstrapFewShot',
        'max_bootstrapped_demos': 3,
    }

    # Post-optimizer
    post_pred   = compiled_module(email=email_text)
    post_result = _coerce(post_pred)
    post_cot    = str(getattr(post_pred, 'rationale', '') or '')

    improvements = [
        '%s: %r -> %r' % (f, pre_result.get(f), post_result.get(f))
        for f in ('bidder', 'quantity', 'deadline', 'terms')
        if pre_result.get(f) != post_result.get(f) and post_result.get(f) is not None
    ]

    return {
        'pre_optimizer':  {'result': pre_result,  'chain_of_thought': pre_cot},
        'training':       training_summary,
        'post_optimizer': {'result': post_result, 'chain_of_thought': post_cot},
        'improvements':   improvements,
        'result':         post_result,
        'backend':        'dspy_azure',
    }


# Legacy shim
def dspy_extract(email_text, few_shot_examples=None, max_retries=2):  # noqa: ARG001
    return run_full_pipeline(email_text)['result']


if __name__ == '__main__':
    email_path = ROOT.parent / 'data' / 'email.json'
    with open(email_path, encoding='utf-8') as f:
        email = json.load(f)['email']

    print('=== DSPy pipeline — Azure gpt-4o ===\n')
    results = run_full_pipeline(email)

    print('--- PRE-OPTIMIZER ---')
    print(json.dumps(results['pre_optimizer']['result'], ensure_ascii=False, indent=2))
    print('CoT:', results['pre_optimizer']['chain_of_thought'][:300])

    print('\n--- TRAINING SUMMARY ---')
    print(json.dumps(results['training'], ensure_ascii=False, indent=2))

    print('\n--- POST-OPTIMIZER ---')
    print(json.dumps(results['post_optimizer']['result'], ensure_ascii=False, indent=2))
    print('CoT:', results['post_optimizer']['chain_of_thought'][:300])

    print('\n--- IMPROVEMENTS ---')
    for imp in results['improvements']:
        print('  OK', imp)
