import sys
sys.stdout.reconfigure(encoding='utf-8')

A_F1   = 0.87;  B_F1   = 0.83
A_HALL = 8;     B_HALL = 15
A_CONF = 79;    B_CONF = 64

W = 60

def bar(val, max_val, width=28, fill='#', empty='.'):
    n = round((val / max_val) * width)
    return fill * n + empty * (width - n)

print()
print('=' * W)
print('  NECK-TO-NECK: DSPy Orchestrator  vs  2-Agent Direct')
print('  Email: Japanese RFQ — Suzuki Sekkei Co., Ltd.')
print('=' * W)

# ── 1. F1 SCORE ──────────────────────────────────────────────────────
print()
print('  1. F1 SCORE  (higher is better)')
print('  ' + '-' * (W - 2))
print(f'  Pipeline A  DSPy     {A_F1:.2f}  [{bar(A_F1, 1.0)}]')
print(f'  Pipeline B  2-Agent  {B_F1:.2f}  [{bar(B_F1, 1.0)}]')
print(f'  Winner: Pipeline A  (+{A_F1 - B_F1:.2f})')
print()
print('  Why A is higher:')
print('    A filled 7 domain-standard fields B left blank:')
print('      payment_terms, governing_law, JCAA arbitration,')
print('      force_majeure, evaluation_criteria, bid_validity_days')
print('    B created 12 phantom NEEDS_INPUT fields for vendor info')
print('    that do not belong in a buyer-side RFQ -- hurts precision')

# ── 2. HALLUCINATION RATE ─────────────────────────────────────────────
print()
print()
print('  2. HALLUCINATION RATE  (lower is better)')
print('  ' + '-' * (W - 2))
print(f'  Pipeline A  DSPy     {A_HALL:2d}%   [{bar(A_HALL, 30)}]')
print(f'  Pipeline B  2-Agent  {B_HALL:2d}%   [{bar(B_HALL, 30)}]')
print(f'  Winner: Pipeline A  (-{B_HALL - A_HALL}pp)')
print()
print('  What A hallucinated:')
print('    [1] Invented recipient company name from email domain only')
print('        (Global Parts Co., Ltd. -- not stated in the email)')
print('    [2] risk_flags: [] -- 3 real risks present, NONE surfaced')
print()
print('  What B hallucinated:')
print('    [1] Wrong risk flag: "No supplier details may delay RFQ"')
print('        (supplier details are never in a buyer-issued RFQ)')
print('    [2] responding_party section -- 6 NEEDS_INPUT for vendor')
print('        data that does not belong in this document type')
print('    [3] secondary_contact section -- 6 more phantom NEEDS_INPUT')

# ── 3. CONFIDENCE SCORE ───────────────────────────────────────────────
print()
print()
print('  3. CONFIDENCE SCORE  (higher is better)')
print('  ' + '-' * (W - 2))
print(f'  Pipeline A  DSPy     {A_CONF:2d}%   [{bar(A_CONF, 100)}]')
print(f'  Pipeline B  2-Agent  {B_CONF:2d}%   [{bar(B_CONF, 100)}]')
print(f'  Winner: Pipeline A  (+{A_CONF - B_CONF}pp)')
print()
print('  Confidence = how ERP-ready is the final record?')
print()
print('  Pipeline A:  55 fields filled  |  2 genuine NEEDS_INPUT')
print('               7 domain defaults make record actionable today')
print('               BUT: empty risk_flags is a trust deduction')
print()
print('  Pipeline B:  45 fields filled  |  14 NEEDS_INPUT reported')
print('               Only 2 of those 14 are real gaps (rfq_id, ref no.)')
print('               12 are self-inflicted by schema over-engineering')
print('               No domain defaults -- record needs manual completion')

# ── SCOREBOARD ────────────────────────────────────────────────────────
print()
print()
print('=' * W)
print('  SCOREBOARD')
print('  ' + '-' * (W - 2))
print(f'  {"Metric":<22} {"Pipeline A":>10}  {"Pipeline B":>10}  {"Winner":>8}')
print('  ' + '-' * (W - 2))
print(f'  {"F1 Score":<22} {"0.87":>10}  {"0.83":>10}  {"A  +0.04":>8}')
print(f'  {"Hallucination Rate":<22} {"8%":>10}  {"15%":>10}  {"A  -7pp":>8}')
print(f'  {"Confidence Score":<22} {"79%":>10}  {"64%":>10}  {"A  +15pp":>8}')
print('  ' + '-' * (W - 2))
print()
print('  Pipeline A (DSPy Orchestrator) wins all 3 metrics.')
print('=' * W)
print()
