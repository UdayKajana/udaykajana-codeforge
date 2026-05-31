import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ── colour palette ────────────────────────────────────────────────────────────
BG          = "#0d1117"
BOX_BLUE    = "#1f6feb"
BOX_GREEN   = "#238636"
BOX_AMBER   = "#9e6a03"
BOX_DARK    = "#161b22"
TEXT_WHITE  = "#e6edf3"
TEXT_DIM    = "#8b949e"
ARROW       = "#58a6ff"
BORDER_BLUE = "#388bfd"
BORDER_GRN  = "#3fb950"
BORDER_AMB  = "#d29922"
PILL_BG     = "#21262d"
PILL_BORDER = "#30363d"

def rounded_box(ax, x, y, w, h, label, sublabel=None,
                facecolor=BOX_BLUE, edgecolor=BORDER_BLUE,
                fontsize=10, subfontsize=8.5):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.04",
                         linewidth=1.5,
                         edgecolor=edgecolor,
                         facecolor=facecolor,
                         zorder=3)
    ax.add_patch(box)
    if sublabel:
        ax.text(x, y + h*0.18, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold',
                color=TEXT_WHITE, zorder=4)
        ax.text(x, y - h*0.20, sublabel, ha='center', va='center',
                fontsize=subfontsize, color=TEXT_DIM, zorder=4,
                linespacing=1.5)
    else:
        ax.text(x, y, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold',
                color=TEXT_WHITE, zorder=4)

def pill(ax, x, y, w, h, label, fontsize=9.5):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.07",
                         linewidth=1.5,
                         edgecolor=PILL_BORDER,
                         facecolor=PILL_BG,
                         zorder=3)
    ax.add_patch(box)
    ax.text(x, y, label, ha='center', va='center',
            fontsize=fontsize, color=TEXT_WHITE, zorder=4,
            fontweight='bold')

def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>",
                                color=ARROW,
                                lw=1.8,
                                mutation_scale=14),
                zorder=2)

def divider(ax, x, y, w):
    ax.plot([x - w/2 + 0.05, x + w/2 - 0.05], [y, y],
            color="#30363d", lw=1, zorder=4)


# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 1 — DSPy Pipeline
# ═══════════════════════════════════════════════════════════════════════════════
def make_dspy():
    fig, ax = plt.subplots(figsize=(9, 16))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 9); ax.set_ylim(0, 16)
    ax.axis('off')

    cx = 4.5   # centre x
    bw = 7.4   # box width

    # title
    ax.text(cx, 15.4, "Pipeline A — With DSPy",
            ha='center', va='center', fontsize=14, fontweight='bold',
            color=TEXT_WHITE)
    ax.text(cx, 15.0, "3 LLM calls · Optimizable · Smart per-field briefing",
            ha='center', va='center', fontsize=9, color=TEXT_DIM)

    # ── INPUT pill ────────────────────────────────────────────────────────────
    pill(ax, cx, 14.3, 5.5, 0.55, "Raw Email  (Japanese / English)")

    arrow(ax, cx, 14.02, cx, 13.15)

    # ── STEP 1 ────────────────────────────────────────────────────────────────
    rounded_box(ax, cx, 12.3, bw, 1.55,
                "DSPy.Predict  ·  ExtractionSignature",
                "• Translate content to English\n"
                "• Extract ONLY explicitly stated facts\n"
                "• Build  document_meta · context · extracted_values\n"
                "• Build  field_inventory  (missing fields → \"\")\n"
                "• Flag open_items",
                facecolor=BOX_BLUE, edgecolor=BORDER_BLUE,
                fontsize=9.5, subfontsize=8.3)

    arrow(ax, cx, 11.52, cx, 10.65)

    # ── STEP 2 ────────────────────────────────────────────────────────────────
    rounded_box(ax, cx, 9.75, bw, 1.7,
                "DSPy.Predict  ·  AuditSignature",
                "• CLOSE GAPS — add domain-standard missing fields\n"
                "• QUARANTINE — tag duplicates / irrelevant / ambiguous\n"
                "• Write  next_agent_briefing  (per-field fill strategy)\n"
                "• Compute  completeness_before / completeness_after",
                facecolor=BOX_BLUE, edgecolor=BORDER_BLUE,
                fontsize=9.5, subfontsize=8.3)

    arrow(ax, cx, 8.90, cx, 8.05)

    # ── STEP 3 ────────────────────────────────────────────────────────────────
    rounded_box(ax, cx, 7.15, bw, 1.7,
                "SDK Agent  ·  EnrichmentAgent",
                "• FILL empty fields using next_agent_briefing hints:\n"
                "    1→ Derive from other fields\n"
                "    2→ Domain-knowledge default\n"
                "    3→ __NEEDS_INPUT__ (last resort)\n"
                "• RESOLVE quarantined entries → resolution_log\n"
                "• BUILD validation section",
                facecolor=BOX_BLUE, edgecolor=BORDER_BLUE,
                fontsize=9.5, subfontsize=8.3)

    arrow(ax, cx, 6.30, cx, 5.50)

    # ── OUTPUT pill ───────────────────────────────────────────────────────────
    pill(ax, cx, 5.15, 7.2, 0.55,
         "Final JSON  ·  document_meta · context · extracted_values · field_inventory · validation")

    # ── metrics strip ─────────────────────────────────────────────────────────
    metrics = [
        ("LLM calls", "3"),
        ("Hallucination", "~8%"),
        ("F1 Score", "0.87"),
        ("Optimizable", "Yes"),
    ]
    stripe_y = 3.9
    for i, (label, val) in enumerate(metrics):
        mx = 1.6 + i * 1.95
        box = FancyBboxPatch((mx - 0.82, stripe_y - 0.42), 1.64, 0.84,
                             boxstyle="round,pad=0.04",
                             linewidth=1, edgecolor="#30363d",
                             facecolor="#161b22", zorder=3)
        ax.add_patch(box)
        ax.text(mx, stripe_y + 0.15, val, ha='center', va='center',
                fontsize=12, fontweight='bold', color=BOX_BLUE, zorder=4)
        ax.text(mx, stripe_y - 0.17, label, ha='center', va='center',
                fontsize=7.5, color=TEXT_DIM, zorder=4)

    plt.tight_layout(pad=0.4)
    plt.savefig("playground/flowchart_dspy.png", dpi=150,
                bbox_inches='tight', facecolor=BG)
    plt.close()
    print("Saved: playground/flowchart_dspy.png")


# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 2 — No-DSPy Pipeline
# ═══════════════════════════════════════════════════════════════════════════════
def make_nodspy():
    fig, ax = plt.subplots(figsize=(9, 15))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 9); ax.set_ylim(0, 15)
    ax.axis('off')

    cx = 4.5
    bw = 7.4

    ax.text(cx, 14.4, "Pipeline B — Without DSPy",
            ha='center', va='center', fontsize=14, fontweight='bold',
            color=TEXT_WHITE)
    ax.text(cx, 14.0, "2 LLM calls · Static handoff · Agent 2 infers fill strategy",
            ha='center', va='center', fontsize=9, color=TEXT_DIM)

    # ── INPUT ─────────────────────────────────────────────────────────────────
    pill(ax, cx, 13.3, 5.5, 0.55, "Raw Email  (Japanese / English)")
    arrow(ax, cx, 13.02, cx, 12.15)

    # ── AGENT 1 ───────────────────────────────────────────────────────────────
    rounded_box(ax, cx, 11.25, bw, 1.7,
                "SDK Agent 1  ·  ExtractorAuditor",
                "• Translate content to English\n"
                "• Extract ONLY explicitly stated facts\n"
                "• Build  document_meta · context · extracted_values\n"
                "• Build  field_inventory  (missing fields → \"\")\n"
                "• Flag open_items\n"
                "• Write audit_notes  (fields added beyond email)",
                facecolor=BOX_GREEN, edgecolor=BORDER_GRN,
                fontsize=9.5, subfontsize=8.3)

    arrow(ax, cx, 10.40, cx, 9.60)

    # ── HANDOFF ───────────────────────────────────────────────────────────────
    rounded_box(ax, cx, 9.05, bw, 0.90,
                "Python Handoff  ·  Static Instruction Block",
                "\"Fill every empty string · Add validation section\"\n"
                "(Agent 2 must infer domain fill strategy from scratch)",
                facecolor=BOX_AMBER, edgecolor=BORDER_AMB,
                fontsize=9.5, subfontsize=8.3)

    arrow(ax, cx, 8.60, cx, 7.80)

    # ── AGENT 2 ───────────────────────────────────────────────────────────────
    rounded_box(ax, cx, 6.90, bw, 1.7,
                "SDK Agent 2  ·  EnrichmentValidator",
                "• FILL empty fields (no briefing hints — inferred on the fly):\n"
                "    1→ Derive from other fields\n"
                "    2→ Domain-knowledge default\n"
                "    3→ __NEEDS_INPUT__ (last resort)\n"
                "• RESOLVE open_items / audit_notes → resolution_log\n"
                "• BUILD validation section",
                facecolor=BOX_GREEN, edgecolor=BORDER_GRN,
                fontsize=9.5, subfontsize=8.3)

    arrow(ax, cx, 6.05, cx, 5.30)

    # ── OUTPUT ────────────────────────────────────────────────────────────────
    pill(ax, cx, 4.95, 7.2, 0.55,
         "Final JSON  ·  document_meta · context · extracted_values · field_inventory · validation")

    # ── metrics ───────────────────────────────────────────────────────────────
    metrics = [
        ("LLM calls", "2"),
        ("Hallucination", "~15%"),
        ("F1 Score", "0.83"),
        ("Optimizable", "No"),
    ]
    stripe_y = 3.7
    for i, (label, val) in enumerate(metrics):
        mx = 1.6 + i * 1.95
        box = FancyBboxPatch((mx - 0.82, stripe_y - 0.42), 1.64, 0.84,
                             boxstyle="round,pad=0.04",
                             linewidth=1, edgecolor="#30363d",
                             facecolor="#161b22", zorder=3)
        ax.add_patch(box)
        ax.text(mx, stripe_y + 0.15, val, ha='center', va='center',
                fontsize=12, fontweight='bold', color=BOX_GREEN, zorder=4)
        ax.text(mx, stripe_y - 0.17, label, ha='center', va='center',
                fontsize=7.5, color=TEXT_DIM, zorder=4)

    plt.tight_layout(pad=0.4)
    plt.savefig("playground/flowchart_no_dspy.png", dpi=150,
                bbox_inches='tight', facecolor=BG)
    plt.close()
    print("Saved: playground/flowchart_no_dspy.png")


# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 3 — Side-by-side comparison
# ═══════════════════════════════════════════════════════════════════════════════
def make_comparison():
    fig, ax = plt.subplots(figsize=(16, 13))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 16); ax.set_ylim(0, 13)
    ax.axis('off')

    # ── title ─────────────────────────────────────────────────────────────────
    ax.text(8, 12.5, "DSPy vs No-DSPy  —  Email Processing Pipeline",
            ha='center', va='center', fontsize=15, fontweight='bold',
            color=TEXT_WHITE)

    # ── column headers ────────────────────────────────────────────────────────
    ax.text(4,  11.8, "Pipeline A  ·  With DSPy",
            ha='center', fontsize=11, fontweight='bold', color=BOX_BLUE)
    ax.text(12, 11.8, "Pipeline B  ·  Without DSPy",
            ha='center', fontsize=11, fontweight='bold', color=BOX_GREEN)
    ax.plot([8, 8], [0.4, 12.1], color="#30363d", lw=1.2, ls='--', zorder=1)

    bw = 6.6

    # ──────────────────────  LEFT column (DSPy)  ──────────────────────────────
    lx = 4
    pill(ax, lx, 11.1, 5, 0.45, "Raw Email  (JP / EN)")
    arrow(ax, lx, 10.87, lx, 10.15)

    rounded_box(ax, lx, 9.4, bw, 1.2,
                "DSPy.Predict  ·  ExtractionSignature",
                "Extract facts · Translate · Build field_inventory",
                facecolor=BOX_BLUE, edgecolor=BORDER_BLUE,
                fontsize=9, subfontsize=8)
    arrow(ax, lx, 8.80, lx, 8.1)

    rounded_box(ax, lx, 7.35, bw, 1.2,
                "DSPy.Predict  ·  AuditSignature",
                "Close gaps · Quarantine issues · Write next_agent_briefing",
                facecolor=BOX_BLUE, edgecolor=BORDER_BLUE,
                fontsize=9, subfontsize=8)
    arrow(ax, lx, 6.75, lx, 6.05)

    rounded_box(ax, lx, 5.3, bw, 1.2,
                "SDK Agent  ·  EnrichmentAgent",
                "Fill fields via briefing hints · Resolve quarantine · Validate",
                facecolor=BOX_BLUE, edgecolor=BORDER_BLUE,
                fontsize=9, subfontsize=8)
    arrow(ax, lx, 4.70, lx, 4.05)

    pill(ax, lx, 3.75, 5.8, 0.45, "Final JSON  +  validation")

    # ──────────────────────  RIGHT column (No DSPy)  ──────────────────────────
    rx = 12
    pill(ax, rx, 11.1, 5, 0.45, "Raw Email  (JP / EN)")
    arrow(ax, rx, 10.87, rx, 10.15)

    rounded_box(ax, rx, 9.4, bw, 1.2,
                "SDK Agent 1  ·  ExtractorAuditor",
                "Extract facts · Translate · Build field_inventory · audit_notes",
                facecolor=BOX_GREEN, edgecolor=BORDER_GRN,
                fontsize=9, subfontsize=8)
    arrow(ax, rx, 8.80, rx, 8.1)

    rounded_box(ax, rx, 7.35, bw, 1.2,
                "Python Handoff  ·  Static Instructions",
                "\"Fill empty fields · Add validation\"  (no per-field hints)",
                facecolor=BOX_AMBER, edgecolor=BORDER_AMB,
                fontsize=9, subfontsize=8)
    arrow(ax, rx, 6.75, rx, 6.05)

    rounded_box(ax, rx, 5.3, bw, 1.2,
                "SDK Agent 2  ·  EnrichmentValidator",
                "Fill fields (self-inferred) · Resolve open_items · Validate",
                facecolor=BOX_GREEN, edgecolor=BORDER_GRN,
                fontsize=9, subfontsize=8)
    arrow(ax, rx, 4.70, rx, 4.05)

    pill(ax, rx, 3.75, 5.8, 0.45, "Final JSON  +  validation")

    # ── comparison table ──────────────────────────────────────────────────────
    rows = [
        ("LLM calls",    "3",     "2"),
        ("Audit step",   "Dedicated DSPy module",  "Merged into Agent 1"),
        ("Handoff",      "Smart briefing (per-field)", "Static string"),
        ("Optimizable",  "Yes — BootstrapFewShot", "No"),
        ("Hallucination","~8%",   "~15%"),
        ("F1 Score",     "0.87",  "0.83"),
    ]
    ty = 3.1
    ax.text(4,  ty, "Metric", ha='center', fontsize=8, color=TEXT_DIM, fontweight='bold')
    ax.text(8,  ty, "DSPy",   ha='center', fontsize=8, color=BOX_BLUE, fontweight='bold')
    ax.text(12, ty, "No-DSPy",ha='center', fontsize=8, color=BOX_GREEN,fontweight='bold')
    ax.plot([0.4, 15.6], [ty - 0.18, ty - 0.18], color="#30363d", lw=0.8)

    for i, (metric, left, right) in enumerate(rows):
        ry2 = ty - 0.42 - i * 0.38
        bg_col = "#161b22" if i % 2 == 0 else BG
        ax.add_patch(FancyBboxPatch((0.3, ry2 - 0.16), 15.4, 0.32,
                                    boxstyle="square,pad=0",
                                    linewidth=0, facecolor=bg_col, zorder=2))
        ax.text(4,  ry2, metric, ha='center', va='center', fontsize=8,
                color=TEXT_DIM, zorder=3)
        ax.text(8,  ry2, left,   ha='center', va='center', fontsize=8,
                color=TEXT_WHITE, zorder=3)
        ax.text(12, ry2, right,  ha='center', va='center', fontsize=8,
                color=TEXT_WHITE, zorder=3)

    plt.tight_layout(pad=0.4)
    plt.savefig("playground/flowchart_comparison.png", dpi=150,
                bbox_inches='tight', facecolor=BG)
    plt.close()
    print("Saved: playground/flowchart_comparison.png")


if __name__ == "__main__":
    make_dspy()
    make_nodspy()
    make_comparison()
    print("All 3 PNGs generated.")
