"""
Single-page web application for the Technical Notes Generator.

Users paste an Azure or OpenRouter API key, type a query, and receive
a fully-rendered HTML notes document in the browser.

Run:
    python app.py
Then open http://localhost:5000
"""

import sys
import threading
import uuid

# Force UTF-8 on Windows terminals that default to CP1252, so Rich's
# Unicode output (✓, ↳, etc.) doesn't crash the server process.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import dspy
from flask import Flask, jsonify, request, render_template_string

from config import detect_provider, get_lm
from agents import MasterAgent
from style_template import build_toc, wrap_final_document

app = Flask(__name__)

# In-memory job store: job_id → {status, html?, error?}
_jobs: dict = {}


# ── HTML ─────────────────────────────────────────────────────────────────────

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>CodeForge · Technical Notes Generator</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet"/>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --blue:    #1a73e8;
    --blue-dk: #1558b0;
    --amber:   #fbbc04;
    --surface: #f8f9fa;
    --card:    #ffffff;
    --border:  #dadce0;
    --text:    #202124;
    --muted:   #5f6368;
    --red:     #d93025;
    --green:   #137333;
    --radius:  10px;
  }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--surface);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* ── Header ─────────────────────────────────────────── */
  header {
    background: var(--blue);
    color: #fff;
    padding: 14px 32px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 2px 6px rgba(0,0,0,.2);
  }
  header svg { flex-shrink: 0; }
  header h1 { font-size: 1.2rem; font-weight: 700; letter-spacing: -.3px; }
  header span { font-size: .85rem; opacity: .85; font-weight: 400; }

  /* ── Layout ──────────────────────────────────────────── */
  main {
    flex: 1;
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 0;
    height: calc(100vh - 56px);
  }

  /* ── Left panel (inputs) ─────────────────────────────── */
  .panel-left {
    background: var(--card);
    border-right: 1px solid var(--border);
    padding: 28px 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    overflow-y: auto;
  }

  .section-label {
    font-size: .72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--muted);
    margin-bottom: 6px;
  }

  label { display: block; }

  .provider-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 6px;
  }
  .badge {
    font-size: .72rem;
    font-weight: 600;
    padding: 2px 9px;
    border-radius: 20px;
    letter-spacing: .03em;
  }
  .badge-azure   { background: #e8f0fe; color: var(--blue); }
  .badge-openrouter { background: #e6f4ea; color: var(--green); }
  .badge-unknown { background: #f1f3f4; color: var(--muted); }

  input[type=password],
  input[type=text],
  textarea {
    width: 100%;
    font-family: inherit;
    font-size: .92rem;
    padding: 10px 12px;
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    outline: none;
    transition: border-color .15s;
    background: #fff;
    color: var(--text);
    resize: vertical;
  }
  input[type=password]:focus,
  input[type=text]:focus,
  textarea:focus { border-color: var(--blue); box-shadow: 0 0 0 3px rgba(26,115,232,.12); }

  .key-input-wrap { position: relative; }
  .toggle-key {
    position: absolute;
    right: 10px; top: 50%;
    transform: translateY(-50%);
    background: none; border: none; cursor: pointer; color: var(--muted);
    font-size: .8rem; padding: 2px 4px;
  }
  .toggle-key:hover { color: var(--blue); }

  textarea { min-height: 110px; }

  .hint { font-size: .78rem; color: var(--muted); margin-top: 5px; line-height: 1.5; }

  /* ── Submit button ───────────────────────────────────── */
  .btn-generate {
    width: 100%;
    padding: 12px;
    background: var(--blue);
    color: #fff;
    font-size: .95rem;
    font-weight: 600;
    border: none;
    border-radius: var(--radius);
    cursor: pointer;
    transition: background .15s, transform .1s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }
  .btn-generate:hover:not(:disabled) { background: var(--blue-dk); }
  .btn-generate:active:not(:disabled) { transform: scale(.98); }
  .btn-generate:disabled { opacity: .55; cursor: not-allowed; }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin .7s linear infinite;
    flex-shrink: 0;
  }

  /* ── Right panel (output) ────────────────────────────── */
  .panel-right {
    background: #f1f3f4;
    display: flex;
    flex-direction: column;
  }

  .output-toolbar {
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 10px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: .84rem;
    color: var(--muted);
  }
  .output-toolbar strong { color: var(--text); font-size: .88rem; }

  .btn-sm {
    padding: 5px 14px;
    border-radius: 6px;
    border: 1.5px solid var(--border);
    background: #fff;
    font-size: .8rem;
    font-weight: 500;
    cursor: pointer;
    color: var(--text);
    transition: border-color .12s;
  }
  .btn-sm:hover { border-color: var(--blue); color: var(--blue); }
  .btn-sm:disabled { opacity: .4; cursor: not-allowed; }

  .output-frame {
    flex: 1;
    border: none;
    background: #fff;
  }

  .placeholder {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: var(--muted);
  }
  .placeholder svg { opacity: .35; }
  .placeholder p { font-size: .9rem; }

  /* ── Log panel ───────────────────────────────────────── */
  .log-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: .82rem;
    font-weight: 600;
    color: var(--blue);
    margin-bottom: 6px;
  }
  .log-list {
    background: #f8f9fa;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    max-height: 220px;
    overflow-y: auto;
    font-size: .78rem;
    font-family: 'Fira Code', monospace;
    line-height: 1.7;
    color: var(--text);
  }
  .log-list .log-line { display: block; }
  .log-list .log-line.active {
    color: var(--blue);
    font-weight: 600;
  }
  .log-list .log-line.done-line { color: var(--green); }
  .log-list .log-line.indent { padding-left: 14px; color: var(--muted); }

  /* ── Responsive ──────────────────────────────────────── */
  @media (max-width: 800px) {
    main { grid-template-columns: 1fr; grid-template-rows: auto 1fr; height: auto; }
    .panel-left { max-height: 60vh; }
    .panel-right { min-height: 55vh; }
  }
</style>
</head>
<body>

<header>
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <rect width="28" height="28" rx="6" fill="white" fill-opacity=".15"/>
    <path d="M7 14h14M14 7v14" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
  </svg>
  <div>
    <h1>CodeForge &mdash; Technical Notes Generator</h1>
    <span>Powered by DSPy multi-agent pipeline</span>
  </div>
</header>

<main>
  <!-- ── Left panel ──────────────────────────────────── -->
  <aside class="panel-left">

    <div>
      <p class="section-label">API Key</p>
      <label>
        <div class="key-input-wrap">
          <input id="apiKey" type="password" placeholder="Paste Azure or OpenRouter key…" autocomplete="off"/>
          <button class="toggle-key" onclick="toggleKeyVisibility()" title="Show/hide key">👁</button>
        </div>
      </label>
      <div class="provider-row">
        <span class="section-label" style="margin:0">Provider:</span>
        <span id="providerBadge" class="badge badge-unknown">— paste key above</span>
      </div>
      <p class="hint">Azure key: long base-64 string &nbsp;|&nbsp; OpenRouter: starts with <code>sk-or-v1-</code></p>
    </div>

    <div>
      <p class="section-label">Query</p>
      <label>
        <textarea id="query" placeholder="e.g.  write a note on Apache Kafka&#10;e.g.  explain Kubernetes networking&#10;e.g.  GCP BigQuery deep dive"></textarea>
      </label>
      <p class="hint">Describe the technical topic you want comprehensive notes on.</p>
    </div>

    <button id="generateBtn" class="btn-generate" onclick="startGenerate()">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M3 8h10M8 3l5 5-5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      Generate Notes
    </button>

    <div id="logPanel" style="display:none">
      <div id="logHeader" class="log-header">
        <span class="spinner" id="logSpinner"></span>
        <span id="logTitle">Working...</span>
      </div>
      <div id="logList" class="log-list"></div>
    </div>

  </aside>

  <!-- ── Right panel ─────────────────────────────────── -->
  <section class="panel-right" id="outputPanel">
    <div class="output-toolbar">
      <strong>Output</strong>
      <span id="outputMeta" style="flex:1"></span>
      <button class="btn-sm" id="downloadBtn" disabled onclick="downloadHtml()">⬇ Download HTML</button>
      <button class="btn-sm" id="openTabBtn" disabled onclick="openInTab()">↗ Open in Tab</button>
    </div>

    <div class="placeholder" id="placeholder">
      <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
        <rect x="8" y="8" width="48" height="48" rx="8" stroke="#5f6368" stroke-width="2"/>
        <path d="M20 24h24M20 32h18M20 40h12" stroke="#5f6368" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <p>Generated notes will appear here</p>
    </div>

    <iframe id="outputFrame" class="output-frame" style="display:none"
            sandbox="allow-same-origin allow-scripts" title="Generated Notes"></iframe>
  </section>
</main>

<script>
  let currentHtml = "";
  let pollTimer   = null;

  // ── Provider detection ──────────────────────────────────
  document.getElementById("apiKey").addEventListener("input", updateProviderBadge);

  function updateProviderBadge() {
    const key   = document.getElementById("apiKey").value.trim();
    const badge = document.getElementById("providerBadge");
    if (!key) {
      badge.className = "badge badge-unknown";
      badge.textContent = "— paste key above";
    } else if (key.startsWith("sk-or-v1-")) {
      badge.className = "badge badge-openrouter";
      badge.textContent = "OpenRouter";
    } else {
      badge.className = "badge badge-azure";
      badge.textContent = "Azure OpenAI";
    }
  }

  function toggleKeyVisibility() {
    const inp = document.getElementById("apiKey");
    inp.type = inp.type === "password" ? "text" : "password";
  }

  // ── Generate ────────────────────────────────────────────
  async function startGenerate() {
    const apiKey = document.getElementById("apiKey").value.trim();
    const query  = document.getElementById("query").value.trim();

    if (!apiKey) { return alert("Please paste an API key."); }
    if (!query)  { return alert("Please enter a query."); }

    // Reset log panel
    document.getElementById("logList").innerHTML = "";
    document.getElementById("logTitle").textContent = "Starting pipeline...";
    document.getElementById("logSpinner").style.display = "inline-block";
    document.getElementById("logPanel").style.display = "block";
    setButtons(true);

    try {
      const resp = await fetch("/generate", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ api_key: apiKey, query }),
      });
      const data = await resp.json();
      if (!resp.ok || data.error) throw new Error(data.error || "Request failed");

      pollLogs(data.job_id);
    } catch (err) {
      appendLog("Error: " + err.message, "active");
      document.getElementById("logTitle").textContent = "Failed";
      document.getElementById("logSpinner").style.display = "none";
      setButtons(false);
    }
  }

  let _renderedCount = 0;

  function pollLogs(jobId) {
    _renderedCount = 0;
    pollTimer = setInterval(async () => {
      try {
        const resp = await fetch(`/logs/${jobId}`);
        const data = await resp.json();

        // Render any new log lines
        const lines = data.logs || [];
        for (let i = _renderedCount; i < lines.length; i++) {
          const msg = lines[i];
          // Style by content
          const cls = msg.startsWith("    ") ? "indent"
                    : msg.startsWith("Done") ? "done-line"
                    : "";
          appendLog(msg, cls);
          // Update header with the latest top-level message
          if (!msg.startsWith("    ") && !msg.startsWith("  ")) {
            document.getElementById("logTitle").textContent = msg;
          }
        }
        _renderedCount = lines.length;

        if (data.status === "done" || data.status === "error") {
          clearInterval(pollTimer);
          document.getElementById("logSpinner").style.display = "none";

          // Fetch full result once done
          if (data.status === "done") {
            const r2 = await fetch(`/result/${jobId}`);
            const d2 = await r2.json();
            currentHtml = d2.html;
            showOutput(d2.html);
            document.getElementById("logTitle").textContent = "Notes ready!";
            document.getElementById("downloadBtn").disabled = false;
            document.getElementById("openTabBtn").disabled  = false;
            document.getElementById("outputMeta").textContent =
              `${Math.round(d2.html.length / 1024)} KB`;
          } else {
            document.getElementById("logTitle").textContent = "Error — see log above";
          }
          setButtons(false);
        }
      } catch (err) {
        clearInterval(pollTimer);
        document.getElementById("logTitle").textContent = "Connection lost";
        document.getElementById("logSpinner").style.display = "none";
        setButtons(false);
      }
    }, 2500);
  }

  function appendLog(msg, extraClass) {
    const list = document.getElementById("logList");
    // Remove "active" class from previous last line
    const prev = list.querySelector(".log-line.active");
    if (prev) prev.classList.remove("active");

    const span = document.createElement("span");
    span.className = "log-line" + (extraClass ? " " + extraClass : " active");
    span.textContent = msg.trim();
    list.appendChild(span);
    list.appendChild(document.createTextNode("\n"));
    list.scrollTop = list.scrollHeight;
  }

  // ── Output helpers ──────────────────────────────────────
  function showOutput(html) {
    const frame = document.getElementById("outputFrame");
    const ph    = document.getElementById("placeholder");
    ph.style.display = "none";
    frame.style.display = "block";
    frame.srcdoc = html;
  }

  function downloadHtml() {
    if (!currentHtml) return;
    const query = document.getElementById("query").value.trim();
    const slug  = query.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "").slice(0, 50);
    const blob  = new Blob([currentHtml], { type: "text/html" });
    const a     = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(blob),
      download: `${slug || "notes"}.html`,
    });
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function openInTab() {
    if (!currentHtml) return;
    const blob = new Blob([currentHtml], { type: "text/html" });
    window.open(URL.createObjectURL(blob), "_blank");
  }

  // ── UI state ────────────────────────────────────────────
  function setButtons(generating) {
    document.getElementById("generateBtn").disabled = generating;
    if (generating) {
      document.getElementById("downloadBtn").disabled = true;
      document.getElementById("openTabBtn").disabled  = true;
    }
  }
</script>
</body>
</html>"""


# ── Background pipeline task ──────────────────────────────────────────────────

def _run_pipeline(job_id: str, api_key: str, query: str) -> None:
    def log_fn(msg: str):
        _jobs[job_id].setdefault("logs", []).append(msg)

    try:
        lm = get_lm(api_key)
        with dspy.context(lm=lm):
            master = MasterAgent(log_fn=log_fn)
            raw_html, curriculum = master(query=query)

        overall_topic = (
            query
            .replace("write a note on", "")
            .replace("write notes on", "")
            .replace("explain", "")
            .replace("What is", "")
            .strip()
            .title()
        )

        toc_html = build_toc(curriculum)

        if raw_html.strip().startswith("<!DOCTYPE") or raw_html.strip().startswith("<html"):
            final_html = raw_html
        else:
            final_html = wrap_final_document(
                topic=overall_topic,
                toc_html=toc_html,
                chapters_html=raw_html,
            )

        _jobs[job_id] = {"status": "done", "html": final_html}

    except Exception as exc:
        _jobs[job_id] = {"status": "error", "error": str(exc)}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/generate", methods=["POST"])
def generate():
    data    = request.get_json(silent=True) or {}
    api_key = data.get("api_key", "").strip()
    query   = data.get("query", "").strip()

    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    if not query:
        return jsonify({"error": "Query is required"}), 400

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running"}

    t = threading.Thread(target=_run_pipeline, args=(job_id, api_key, query), daemon=True)
    t.start()

    return jsonify({"job_id": job_id})


@app.route("/result/<job_id>")
def result(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/logs/<job_id>")
def logs(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({"status": job.get("status", "running"), "logs": job.get("logs", [])})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import webbrowser, threading as _t

    def _open(): webbrowser.open("http://localhost:8080")
    _t.Timer(1.2, _open).start()

    print("CodeForge Notes Generator -> http://localhost:8080")
    app.run(host="127.0.0.1", port=8080, debug=False)
