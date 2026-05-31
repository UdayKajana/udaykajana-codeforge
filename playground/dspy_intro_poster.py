import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
import numpy as np

BG    = "#0a0e1a"
CARD  = "#0f1829"
CYAN  = "#00cfff"
BLUE  = "#4c8eff"
DIM   = "#6b7db3"
WHITE = "#f0f4ff"
DIMMER= "#2a3558"

fig = plt.figure(figsize=(10, 10))
fig.patch.set_facecolor(BG)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 10); ax.set_ylim(0, 10)
ax.axis('off')

# subtle grid
for v in np.arange(0, 10.1, 1):
    ax.plot([v, v], [0, 10], color=DIMMER, lw=0.2, alpha=0.3)
    ax.plot([0, 10], [v, v], color=DIMMER, lw=0.2, alpha=0.3)

# top glow
for i in range(120):
    ax.axhspan(10-(i+1)*0.07, 10-i*0.07, color=BLUE, alpha=0.06*(1-i/120))

# ── title ─────────────────────────────────────────────────────────────────────
for dx, dy, a in [(-0.04,-0.04,0.1),(0,0,1.0)]:
    ax.text(5+dx, 9.18+dy, "DSPy", ha='center', va='center',
            fontsize=52, color=CYAN, fontweight='bold', alpha=a, zorder=7)

ax.text(5, 8.55, "Declarative Self-improving Language Programs in Python",
        ha='center', va='center', fontsize=9.5, color=DIM, zorder=7)

ax.plot([0.5, 9.5], [8.22, 8.22], color=DIMMER, lw=0.9, zorder=4)

# ── definition card ────────────────────────────────────────────────────────────
ax.add_patch(FancyBboxPatch((0.45, 7.08), 9.1, 0.95,
    boxstyle="round,pad=0.12", lw=1.2, edgecolor=BLUE, facecolor=CARD, zorder=3))
ax.text(5, 7.62,
        "A Python framework that lets you  program  language models",
        ha='center', va='center', fontsize=10.5, color=WHITE,
        fontweight='bold', zorder=8)
ax.text(5, 7.24,
        "instead of prompting them — using composable modules that compile into optimized prompts automatically.",
        ha='center', va='center', fontsize=8.5, color=DIM, zorder=8)

ax.plot([0.5, 9.5], [6.88, 6.88], color=DIMMER, lw=0.5, alpha=0.5, zorder=4)

# ── bullet points ─────────────────────────────────────────────────────────────
points = [
    (CYAN,  "No prompt engineering",
             "You define the task signature (inputs/outputs). DSPy figures out the best prompt."),
    (BLUE,  "Auto-optimization",
             "The BootstrapFewShot optimizer tunes prompts and few-shot examples automatically."),
    ("#a855f7", "Composable modules",
             "Chain dspy.Predict, ChainOfThought, and ReAct just like PyTorch layers."),
    ("#10b981","Model-agnostic",
             "Plug in GPT-4, Claude, Gemini, Llama — swap models without rewriting anything."),
    ("#f59e0b","Metric-driven",
             "Define an evaluation metric; DSPy compiles your program to maximise it."),
]

for i, (color, title, body) in enumerate(points):
    y = 6.32 - i * 1.18
    # dot
    ax.add_patch(Circle((0.82, y + 0.12), 0.09, color=color, zorder=6))
    # title
    ax.text(1.08, y + 0.12, title,
            fontsize=10, color=color, fontweight='bold', va='center', zorder=8)
    # body
    ax.text(1.08, y - 0.25, body,
            fontsize=8.3, color=DIM, va='center', zorder=8, linespacing=1.5)
    # divider (skip last)
    if i < len(points) - 1:
        ax.plot([0.6, 9.4], [y - 0.58, y - 0.58], color=DIMMER, lw=0.5, alpha=0.4, zorder=4)

# ── outer border ──────────────────────────────────────────────────────────────
for lw, a in [(6,0.03),(3,0.08),(1.2,0.5)]:
    ax.add_patch(FancyBboxPatch((0.04,0.04), 9.92, 9.92,
        boxstyle="round,pad=0.1", lw=lw, edgecolor=BLUE,
        facecolor='none', alpha=a, zorder=10))

plt.savefig("playground/dspy_intro.png", dpi=160,
            bbox_inches='tight', facecolor=BG, pad_inches=0.08)
plt.close()
print("Saved: playground/dspy_intro.png")
