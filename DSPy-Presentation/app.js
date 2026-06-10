/* app.js — no nested template literals; safe for all browsers */

const BACKEND = { available: false, email: null, results: null };

// ── Fallback data (matches the real data/email.json) ──────────────────────

const EMAIL_DATA = {
  email: [
    '件名：Re: Re: 入札書の件 ご確認【製品Aシリーズ 2026年度】',
    '',
    '田中様',
    '',
    'いつもお世話になっております。株式会社サクラ電機 購買部の橋本でございます。',
    '先日のお電話にてご説明いただいた内容を踏まえ、改めてご入札書をお送りいたします。',
    '',
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━',
    '【ご参考：前回(2025年10月)入札実績】※ 比較のため掲載',
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━',
    '会社名: 株式会社サクラ電機',
    '製品: 製品A Standard (型番: PA-100S)',
    '数量: 150個',
    '単価: ¥15,800/個（税別）',
    '通貨: JPY',
    '納期: 2025/12/15',
    '支払条件: NET30',
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━',
    '',
    '上記は昨年度のものです。今年度は仕様変更がございますのでご注意ください。',
    '',
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━',
    '【今回入札内容 2026年度】',
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━',
    '会社名：株式会社サクラ電機',
    '担当：橋本 太郎（購買部）',
    '',
    '製品：製品A Proシリーズ（バーション詳細は添付仕様書参照・現在未確定）',
    '数量：200個（但し最初のロットは50個を予定、残り150個は2026年Q3以降納品可）',
    '単価：添付の価格表をご参照ください（前回同条件希望ですが要交渉）',
    '通貨：日本円（JPY）',
    '希望納期：来年度第1四半期内に完納予定、具体的には2026年3月末（3/31）までが理想',
    '支払条件：NET30（前回と同様でお願いしたい）',
    '',
    '※ バーション情報については現時点でProかStandardか未確定のため、確定次第ご連絡いたします。',
    '※ 本メールに記載漏れがある場合は別途ご連絡ください。',
    '',
    'どうぞよろしくお願い申し上げます。',
    '',
    '────────────────────────────',
    '橋本 太郎 | 株式会社サクラ電機 購買部',
    'purchasing@sakura-elec.co.jp | Tel: 03-1234-XXXX',
    '※ このメールは複数の宛先に送信されています。返信は橋本宛にお願いします。',
    '────────────────────────────'
  ].join('\n')
};

const FALLBACK = {
  systemPrompt: 'Extract bidding details from this email and return JSON with keys: bidder, items, quantity, unit_price, currency, deadline, terms. Ignore previous bid history — focus only on the current bid section.',

  promptOutput: {
    bidder: '株式会社サクラ電機',
    items: [{ name: '製品A Standard (型番: PA-100S)', version: null }],
    quantity: 150,
    unit_price: { amount: 15800, currency: 'JPY' },
    deadline: '2025-12-15',
    terms: null
  },

  dspyOutput: {
    pre_optimizer: {
      result: {
        bidder: '株式会社サクラ電機',
        items: [{ name: '製品A Standard (型番: PA-100S)', version: null }],
        quantity: 150,
        unit_price: { amount: 15800, currency: 'JPY' },
        deadline: '2025-12-15',
        terms: null
      },
      suggest_log: []
    },
    training: {
      examples_used: 5,
      trainset_size: 5,
      patterns_learned: ['current_section_markers', 'skip_previous_bid', 'terms_patterns', 'quantity_with_notes'],
      date_formats_seen: 5
    },
    post_optimizer: {
      result: {
        bidder: '株式会社サクラ電機',
        items: [{ name: '製品A Proシリーズ（バーション詳細は添付仕様書参照・現在未確定）', version: null }],
        quantity: 200,
        unit_price: { amount: null, currency: 'JPY' },
        deadline: '2026-03-31',
        terms: 'NET30'
      },
      suggest_log: []
    },
    improvements: [
      "quantity: 150 -> 200",
      "deadline: '2025-12-15' -> '2026-03-31'",
      "terms: None -> 'NET30'"
    ],
    backend: 'dspy_demo'
  },

  goldenExamples: [
    {
      email: '件名: 入札書の提出\n\n会社名: 田中産業株式会社\n担当: 田中一郎\n\n製品: 工業用センサー TypeB\n数量: 50個\n単価: 25000 JPY\n希望納期: 2026/04/15\n支払条件: NET30',
      expected: { bidder: '田中産業株式会社', quantity: 50, unit_price: { amount: 25000, currency: 'JPY' }, deadline: '2026-04-15', terms: 'NET30' }
    },
    {
      email: '前回(2025年6月)のご注文実績：数量100個、単価¥8,000\n\n今回入札:\n会社名: 山本製作所\n製品: 電動バルブ V-200\n数量: 75個\n単価: 9500 JPY\n納期: 2026/05/30',
      expected: { bidder: '山本製作所', quantity: 75, unit_price: { amount: 9500, currency: 'JPY' }, deadline: '2026-05-30', terms: null }
    },
    {
      email: '会社名: 鈴木エレクトロニクス\n製品: 圧力センサー PS-300\n数量: 120個\n単価: 別途見積もり\n通貨: JPY\n納期: 2026/06/01\n支払: NET60',
      expected: { bidder: '鈴木エレクトロニクス', quantity: 120, unit_price: { amount: null, currency: 'JPY' }, deadline: '2026-06-01', terms: 'NET60' }
    },
    {
      email: '会社名: 佐藤機械工業\n製品: 油圧ポンプ HP-500\n数量: 30台\n単価: 45000 JPY\n希望納期: 2026年7月上旬（7月10日目安）\n支払い条件: NET30',
      expected: { bidder: '佐藤機械工業', quantity: 30, unit_price: { amount: 45000, currency: 'JPY' }, deadline: '2026-07-10', terms: 'NET30' }
    },
    {
      email: '前回受注実績: 数量200個, 単価3200円（参考）\n\n今回ご発注内容:\n会社名: 渡辺産業株式会社\n品名: LEDライトユニット LU-100\n発注数量: 500個（最小ロット100個、3回分納）\n単価: 3500 JPY/個\n納期: 2026/09/30\n条件: NET45',
      expected: { bidder: '渡辺産業株式会社', quantity: 500, unit_price: { amount: 3500, currency: 'JPY' }, deadline: '2026-09-30', terms: 'NET45' }
    }
  ]
};

// ── Helpers ───────────────────────────────────────────────────────────────

function esc(s) {
  return String(s).replace(/[&<>"]/g, function(c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}

function codeBlock(src, lang) {
  lang = lang || 'python';
  return '<pre><code class="hlcode language-' + lang + '">' + esc(src) + '</code></pre>';
}

function label(text) {
  return '<div class="sec-label">' + text + '</div>';
}

function inputBadge() {
  return label('User Input') +
    '<div class="user-input-row">' +
    '<div class="user-input-pill">&#9993; Bidding Email</div>' +
    '</div>';
}

function desc(html) {
  return '<p class="stage-desc">' + html + '</p>';
}

function suggestBox(title, items) {
  var lis = items.map(function(i) { return '<li>' + i + '</li>'; }).join('');
  return '<div class="suggest-box"><div class="suggest-title">' + title + '</div><ul>' + lis + '</ul></div>';
}

function compareBox(title, rows) {
  var trs = rows.map(function(r) {
    return '<tr><td class="cmp-field">' + r[0] + '</td>' +
      '<td class="cmp-before">' + r[1] + '</td>' +
      '<td class="cmp-after">'  + r[2] + '</td></tr>';
  }).join('');
  return '<div class="compare-box">' +
    '<div class="suggest-title">' + title + '</div>' +
    '<table class="cmp-table"><thead>' +
    '<tr><th>Field</th><th>Pre-Optimizer</th><th>Post-Optimizer</th></tr>' +
    '</thead><tbody>' + trs + '</tbody></table></div>';
}

// ── Stage content ─────────────────────────────────────────────────────────

var STAGE = {
  A: {
    initialization: function() {
      var sysPrompt = (BACKEND.available && BACKEND.results &&
        BACKEND.results.prompt_pipeline && BACKEND.results.prompt_pipeline.prompt)
        ? BACKEND.results.prompt_pipeline.prompt
        : FALLBACK.systemPrompt;

      var src =
        '# Without DSPy — plain system prompt passed to the LLM\n\n' +
        'SYSTEM_PROMPT = """\n' + sysPrompt + '\n"""\n\n' +
        'messages = [\n' +
        '    {"role": "system", "content": SYSTEM_PROMPT},\n' +
        '    {"role": "user",   "content": bidding_email},\n' +
        ']\n' +
        'response = llm.chat(messages)';

      return label('System Prompt') + codeBlock(src) + inputBadge() +
        desc('A static string written by the engineer. The bidding email is the user message. ' +
             'No typed contract — the LLM must infer field names and formats entirely from the prompt wording. ' +
             '<strong>Notice:</strong> this email contains a previous-bid section with different numbers — a naive prompt has no way to reliably ignore it.');
    },

    agent: function() {
      var sysSrc = 'SYSTEM_PROMPT = "Extract bidding details from this email and return JSON. ' +
        'Ignore previous bid history — focus only on the current bid section."';
      var src =
        '# Without DSPy — plain function wrapping the LLM call\n' +
        'import json\n\n' +
        'def extract_bid_agent(email: str) -> dict:\n' +
        '    SYSTEM_PROMPT = "Extract bidding details and return JSON."\n\n' +
        '    resp = llm.chat([\n' +
        '        {"role": "system", "content": SYSTEM_PROMPT},\n' +
        '        {"role": "user",   "content": email},\n' +
        '    ])\n\n' +
        '    # Fragile: if the LLM adds prose before/after the JSON this breaks.\n' +
        '    # Also: with no structured contract, the LLM may pick up the PREVIOUS\n' +
        '    # bid quantity (150) instead of the current one (200).\n' +
        '    return json.loads(resp.choices[0].message.content)';

      return label('System Prompt') + codeBlock(sysSrc) +
        inputBadge() +
        label('Agent Code') + codeBlock(src) +
        desc('No typed contract — output format depends entirely on prompt wording. ' +
             'The agent sees both the previous-bid section and the current-bid section with no way to differentiate them.');
    },

    assert: function() {
      var src =
        '# Without DSPy — manual validation after the LLM responds\n' +
        'import json\n\n' +
        'def validate_bid(llm_output: str):\n' +
        '    result = json.loads(llm_output)\n' +
        '    warnings = []\n\n' +
        '    if not result.get("deadline"):\n' +
        '        warnings.append("deadline is missing — flag for human review")\n\n' +
        '    if not result.get("quantity"):\n' +
        '        warnings.append("quantity missing")\n\n' +
        '    # No auto-retry: engineer must update the prompt manually\n' +
        '    # and re-run the whole pipeline to fix missing fields.\n' +
        '    return result, warnings';

      return label('Validation Code') + codeBlock(src) + inputBadge() +
        desc('Assertions are external checks — no automatic retry. When a field is wrong or missing, ' +
             'the engineer must manually update the prompt and rerun.');
    },

    optimizer: function() {
      var src =
        '# Without DSPy — few-shot examples written by hand in the prompt\n' +
        'SYSTEM_PROMPT = """Extract bidding details and return JSON.\n\n' +
        '# Engineer must MANUALLY write and maintain every example:\n\n' +
        'Example 1:\n' +
        'Input:  会社名: ABC商事, 数量: 50, 納期: 2026/08/01\n' +
        'Output: {"bidder":"ABC商事","quantity":50,"deadline":"2026-08-01"}\n\n' +
        'Example 2 (with previous-bid noise):\n' +
        'Input:  前回: 数量100。今回: 会社名: XYZ, 数量: 75\n' +
        'Output: {"bidder":"XYZ","quantity":75}  # engineer manually clarified\n\n' +
        '# Adding a new edge case = editing this string manually.\n' +
        '# No versioning, no metric, no automated selection.\n' +
        'Now extract from:"""';

      return label('Manual Few-Shot Prompt') + codeBlock(src) + inputBadge() +
        desc('Every edge case must be manually added to the prompt string. ' +
             'There is no automated selection of the most effective examples.');
    },

    output: function() {
      var out = (BACKEND.available && BACKEND.results &&
        BACKEND.results.prompt_pipeline && BACKEND.results.prompt_pipeline.parsed)
        ? BACKEND.results.prompt_pipeline.parsed
        : FALLBACK.promptOutput;

      var note = '<code>quantity</code> = <strong>' + esc(String(out.quantity)) +
        '</strong> — naive extractor hit the previous-bid section (150) instead of the current bid (200). ' +
        '<code>deadline</code> = <strong>' + esc(String(out.deadline)) +
        '</strong> — could not parse the mixed Japanese/slash date format. ' +
        '<code>terms</code> = <strong>null</strong> — not extracted.';

      return label('Pipeline A Output (Without DSPy)') +
        codeBlock(JSON.stringify(out, null, 2), 'json') +
        desc(note);
    }
  },

  B: {
    initialization: function() {
      var src =
        '# With DSPy — typed Signature defines the extraction contract\n' +
        'import dspy\n\n' +
        'class BidExtractor(dspy.Signature):\n' +
        '    """Extract structured bid info from a Japanese bidding email.\n' +
        '    Ignore previous bid history — focus only on the current bid section."""\n\n' +
        '    email: str = dspy.InputField(desc="Raw bidding email text")\n\n' +
        '    bidder:     str  = dspy.OutputField(desc="Bidder company name")\n' +
        '    quantity:   int  = dspy.OutputField(desc="Current bid quantity (NOT from previous bids)")\n' +
        '    deadline:   str  = dspy.OutputField(desc="Delivery deadline in ISO format YYYY-MM-DD")\n' +
        '    unit_price: dict = dspy.OutputField(desc="Price as {amount: number|null, currency: str}")\n' +
        '    terms:      str  = dspy.OutputField(desc="Payment terms e.g. NET30")\n\n' +
        '# DSPy auto-generates the system prompt from the Signature.\n' +
        'pipeline = dspy.ChainOfThought(BidExtractor)';

      var notice = (BACKEND.available && BACKEND.results &&
        BACKEND.results.dspy_pipeline && BACKEND.results.dspy_pipeline.backend)
        ? 'Backend: ' + BACKEND.results.dspy_pipeline.backend
        : 'Simulation mode — no live DSPy backend connected.';

      return label('DSPy Signature (typed contract)') + codeBlock(src) + inputBadge() +
        desc('The <code>desc=</code> on <code>quantity</code> explicitly says ' +
             '"NOT from previous bids" — this constraint is part of the typed contract ' +
             'and gets compiled into the prompt automatically. <em>' + esc(notice) + '</em>');
    },

    agent: function() {
      var autoSrc =
        '# Auto-generated by DSPy from BidExtractor Signature\n' +
        '# (no hardcoded string — built from field descriptions at compile time)';
      var agentSrc =
        '# With DSPy — agent is a dspy.Module with typed forward()\n' +
        'import dspy\n\n' +
        'class BidExtractionModule(dspy.Module):\n' +
        '    def __init__(self):\n' +
        '        self.extract = dspy.ChainOfThought(BidExtractor)\n\n' +
        '    def forward(self, email: str):\n' +
        '        result = self.extract(email=email)\n' +
        '        return result\n\n' +
        '# Usage\n' +
        'agent  = BidExtractionModule()\n' +
        'result = agent(email=bidding_email)\n\n' +
        'print(result.bidder)    # 株式会社サクラ電機\n' +
        'print(result.quantity)  # 200\n' +
        'print(result.deadline)  # 2026-03-31\n' +
        'print(result.terms)     # NET30';

      return label('System Prompt') + codeBlock(autoSrc) +
        inputBadge() +
        label('Agent Code (DSPy Module)') + codeBlock(agentSrc) +
        desc('<code>dspy.ChainOfThought</code> adds a reasoning step before each output field. ' +
             'DSPy parses and validates the response into typed Python objects automatically.');
    },

    assert: function() {
      var src =
        '# With DSPy — dspy.Suggest adds soft constraints with auto-retry\n' +
        'import dspy\n\n' +
        'class BidExtractionModule(dspy.Module):\n' +
        '    def __init__(self):\n' +
        '        self.extract = dspy.ChainOfThought(BidExtractor)\n\n' +
        '    def forward(self, email: str):\n' +
        '        result = self.extract(email=email)\n\n' +
        '        # dspy.Suggest — SOFT constraint\n' +
        '        # If condition is False, DSPy appends the hint to the prompt\n' +
        '        # and retries the LLM call automatically.\n' +
        '        # This email has "2026年3月末（3/31）" — not a simple date:\n' +
        '        dspy.Suggest(\n' +
        '            result.deadline is not None,\n' +
        '            "Deadline is missing. Re-read the email and extract the "\n' +
        '            "delivery date in ISO format (YYYY-MM-DD). The date may "\n' +
        '            "appear as a year + month/day combination."\n' +
        '        )\n\n' +
        '        dspy.Suggest(\n' +
        '            result.quantity is not None,\n' +
        '            "Quantity is missing. Focus on the current bid section "\n' +
        '            "and ignore any previous bid reference numbers."\n' +
        '        )\n\n' +
        '        # dspy.Assert — HARD constraint\n' +
        '        dspy.Assert(\n' +
        '            result.bidder is not None,\n' +
        '            "Bidder name (会社名) is required — cannot continue."\n' +
        '        )\n\n' +
        '        return result';

      return label('dspy.Suggest — Soft Constraint with Auto-Retry') +
        codeBlock(src) + inputBadge() +
        suggestBox('How dspy.Suggest works', [
          '<code>dspy.Suggest(condition, hint)</code> — when <code>condition</code> is <code>False</code>, DSPy <strong>retries</strong> the LLM call with <code>hint</code> appended automatically.',
          'For this email: <code>deadline</code> is initially <code>null</code> (parser fails on "2026年3月末（3/31）") → Suggest fires → retry resolves it to <code>"2026-03-31"</code>.',
          '<code>dspy.Suggest</code> is a <strong>soft</strong> constraint — pipeline continues even if retry still fails.',
          '<code>dspy.Assert</code> is the <strong>hard</strong> version — raises <code>SuggestionFailed</code> if not met after all retries.'
        ]);
    },

    optimizer: function() {
      var examples = (BACKEND.available && BACKEND.results) ? null : FALLBACK.goldenExamples;

      var trainsetSrc =
        '# With DSPy — BootstrapFewShot trains on golden examples\n' +
        'import dspy\n' +
        'from dspy.teleprompt import BootstrapFewShot\n\n' +
        '# 5 golden examples cover key edge cases:\n' +
        '#  1. Clean complete email              -> baseline extraction\n' +
        '#  2. Email with previous-bid noise     -> teaches: skip old data\n' +
        '#  3. Email with missing price          -> teaches: null is ok for amount\n' +
        '#  4. Email with messy date format      -> teaches: date normalisation\n' +
        '#  5. Quantity with minimum-lot note    -> teaches: take TOTAL not lot size\n\n' +
        'trainset = [\n' +
        '    dspy.Example(\n' +
        '        email="...",\n' +
        '        bidder="田中産業株式会社", quantity=50,\n' +
        '        deadline="2026-04-15", terms="NET30"\n' +
        '    ).with_inputs("email"),\n\n' +
        '    dspy.Example(\n' +
        '        email="前回: 数量100 ... 今回: 数量75 ...",  # has noise\n' +
        '        bidder="山本製作所", quantity=75,  # NOT 100\n' +
        '        deadline="2026-05-30", terms=None\n' +
        '    ).with_inputs("email"),\n\n' +
        '    # ... 3 more examples\n' +
        ']\n\n' +
        'optimizer = BootstrapFewShot(metric=bid_accuracy_metric)\n' +
        'compiled  = optimizer.compile(BidExtractionModule(), trainset=trainset)';

      var html = label('BootstrapFewShot — Training') + codeBlock(trainsetSrc) + inputBadge();

      // Show actual golden examples if available
      var exList = examples || FALLBACK.goldenExamples;
      var exRows = exList.map(function(ex, i) {
        return '<tr><td class="ex-idx">#' + (i+1) + '</td>' +
          '<td class="ex-email">' + esc(ex.email.substring(0, 80)) + '…</td>' +
          '<td class="ex-out">' + esc(JSON.stringify({
            bidder: ex.expected.bidder,
            qty: ex.expected.quantity,
            deadline: ex.expected.deadline,
            terms: ex.expected.terms
          })) + '</td></tr>';
      }).join('');
      html += '<div class="golden-table-wrap">' +
        '<div class="sec-label">Golden Training Dataset (5 examples)</div>' +
        '<table class="golden-table">' +
        '<thead><tr><th>#</th><th>Email (excerpt)</th><th>Expected output</th></tr></thead>' +
        '<tbody>' + exRows + '</tbody></table></div>';

      var training = (BACKEND.available && BACKEND.results && BACKEND.results.dspy_pipeline &&
        BACKEND.results.dspy_pipeline.training)
        ? BACKEND.results.dspy_pipeline.training
        : FALLBACK.dspyOutput.training;

      html += suggestBox('Patterns Learned by Optimizer', [
        '<strong>skip_previous_bid</strong> — found "前回" noise in examples 2 & 5 → learned to focus on current-bid section only.',
        '<strong>current_section_markers</strong> — identified "今回" as the boundary between old and new bid data.',
        '<strong>terms_patterns</strong> — learned NET\\d+ payment term pattern from examples 1, 3, 4, 5.',
        '<strong>quantity_with_notes</strong> — example 5 teaches: "500個（最小ロット100個）" → quantity = 500 not 100.',
        '<strong>date_formats_seen: ' + training.date_formats_seen + '</strong> — diverse date formats in training set improve deadline parsing.',
        'Total examples compiled: <strong>' + training.examples_used + '</strong> | Patterns learned: <strong>' + training.patterns_learned.length + '</strong>'
      ]);

      return html;
    },

    output: function() {
      var dspyResult = (BACKEND.available && BACKEND.results && BACKEND.results.dspy_pipeline)
        ? BACKEND.results.dspy_pipeline
        : FALLBACK.dspyOutput;

      var pre  = dspyResult.pre_optimizer  || FALLBACK.dspyOutput.pre_optimizer;
      var post = dspyResult.post_optimizer || FALLBACK.dspyOutput.post_optimizer;
      var imps = dspyResult.improvements   || FALLBACK.dspyOutput.improvements;
      var tr   = dspyResult.training       || FALLBACK.dspyOutput.training;

      var html = label('Step 1 — Pre-Optimizer Extraction (Before Training)') +
        codeBlock(JSON.stringify(pre.result, null, 2), 'json');

      var sugLog = (pre.suggest_log || []).map(function(s) {
        return '<code>' + esc(s.field) + '</code> (attempt ' + s.attempt + ') → hint: <em>' + esc(s.hint) + '</em>';
      });
      if (sugLog.length) {
        html += suggestBox('dspy.Suggest triggered (pre-optimizer)', sugLog);
      }

      html += label('Step 2 — BootstrapFewShot Training') +
        '<div class="training-badge">' +
        '&#9654; Compiled <strong>' + tr.examples_used + '</strong> golden examples &nbsp;|&nbsp; ' +
        'Patterns learned: <strong>' + (tr.patterns_learned || []).join(', ') + '</strong>' +
        '</div>';

      html += label('Step 3 — Post-Optimizer Extraction (After Training)') +
        codeBlock(JSON.stringify(post.result, null, 2), 'json');

      var sugLog2 = (post.suggest_log || []).map(function(s) {
        return '<code>' + esc(s.field) + '</code> → <em>' + esc(s.hint) + '</em> (price is in attachment — expected)';
      });
      if (sugLog2.length) {
        html += suggestBox('dspy.Suggest (post-optimizer — fewer issues)', sugLog2);
      }

      var impRows = imps.map(function(imp) {
        var parts = imp.split(' -> ');
        var fieldPart = parts[0].split(': ');
        return [fieldPart[0], '<span class="bad">' + esc(fieldPart[1] || '') + '</span>',
          '<span class="good">' + esc(parts[1] || '') + '</span>'];
      });
      if (impRows.length) {
        html += compareBox('Improvements from BootstrapFewShot Training', impRows);
      }

      return html;
    }
  }
};

// ── Backend ───────────────────────────────────────────────────────────────

async function loadBackend() {
  try {
    var er = await fetch('/api/email');
    var rr = await fetch('/api/results');
    if (!er.ok || !rr.ok) throw new Error('API error');
    BACKEND.email   = (await er.json()).email;
    BACKEND.results = await rr.json();
    BACKEND.available = true;
  } catch (e) {
    BACKEND.available = false;
    console.warn('Backend unavailable, using fallback data:', e.message);
  }
}

// ── Render ────────────────────────────────────────────────────────────────

function renderEmail() {
  var el = document.getElementById('email-view');
  if (el) el.textContent = (BACKEND.available && BACKEND.email) ? BACKEND.email : EMAIL_DATA.email;
}

function highlight(container) {
  if (!window.hljs) return;
  container.querySelectorAll('code.hlcode').forEach(function(el) {
    hljs.highlightElement(el);
  });
}

function renderStage(stage) {
  var emailPanel   = document.getElementById('email-panel');
  var pipelinesDiv = document.getElementById('pipelines-panel');
  var panelA       = document.getElementById('panel-A');
  var panelB       = document.getElementById('panel-B');

  if (stage === 'email') {
    emailPanel.style.display   = '';
    pipelinesDiv.style.display = 'none';
    return;
  }

  emailPanel.style.display   = 'none';
  pipelinesDiv.style.display = '';

  var fnA = STAGE.A[stage];
  var fnB = STAGE.B[stage];

  if (!fnA || !fnB) {
    panelA.innerHTML = '<p class="stage-desc">Unknown stage: ' + esc(stage) + '</p>';
    panelB.innerHTML = panelA.innerHTML;
    return;
  }

  try {
    panelA.innerHTML = fnA();
  } catch (e) {
    panelA.innerHTML = '<div class="error-box">Error (A): ' + esc(e.message) + '</div>';
    console.error('STAGE.A.' + stage, e);
  }

  try {
    panelB.innerHTML = fnB();
  } catch (e) {
    panelB.innerHTML = '<div class="error-box">Error (B): ' + esc(e.message) + '</div>';
    console.error('STAGE.B.' + stage, e);
  }

  highlight(panelA);
  highlight(panelB);
}

function wire() {
  var items = document.querySelectorAll('.menu li');
  items.forEach(function(li) {
    li.addEventListener('click', function() {
      items.forEach(function(i) { i.classList.remove('active'); });
      li.classList.add('active');
      renderStage(li.dataset.stage);
    });
  });
  var first = document.querySelector('.menu li[data-stage="email"]');
  if (first) first.click();
}

window.addEventListener('DOMContentLoaded', async function() {
  renderEmail();
  wire();
  await loadBackend();
  renderEmail();
  var active = document.querySelector('.menu li.active');
  if (active) renderStage(active.dataset.stage);
});
