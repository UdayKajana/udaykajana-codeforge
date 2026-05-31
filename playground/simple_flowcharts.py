import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def draw_box(ax, x, y, w, h, text, color='#1f6feb', textcolor='white', fontsize=11):
    box = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                   boxstyle="round,pad=0.05",
                                   linewidth=2, edgecolor=color,
                                   facecolor=color)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center',
            fontsize=fontsize, color=textcolor, fontweight='bold')

def draw_arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color='#555', lw=2, mutation_scale=18))

# ── Chart 1: With DSPy ────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 3))
ax.set_xlim(0, 10); ax.set_ylim(0, 3)
ax.axis('off')
fig.patch.set_facecolor('white')

nodes = [
    (1.0,  1.5, 'Email'),
    (3.0,  1.5, 'Agent 1\n(Extractor)'),
    (5.5,  1.5, 'DSPy\n(Auditor)'),
    (8.0,  1.5, 'Agent 2\n(Enricher)'),
]
colors = ['#555', '#1f6feb', '#e36209', '#1f6feb']

for (x, y, label), color in zip(nodes, colors):
    draw_box(ax, x, y, 1.5, 0.85, label, color=color)

for i in range(len(nodes) - 1):
    draw_arrow(ax, nodes[i][0] + 0.75, 1.5, nodes[i+1][0] - 0.75, 1.5)

ax.text(5, 2.8, 'Pipeline A — With DSPy', ha='center', fontsize=13, fontweight='bold', color='#222')

plt.tight_layout()
plt.savefig('playground/simple_dspy.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: simple_dspy.png")

# ── Chart 2: Without DSPy ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 3))
ax.set_xlim(0, 10); ax.set_ylim(0, 3)
ax.axis('off')
fig.patch.set_facecolor('white')

nodes = [
    (1.0,  1.5, 'Email'),
    (3.2,  1.5, 'Agent 1\n(Extractor\n+ Auditor)'),
    (5.8,  1.5, 'Handoff\n(Static\nInstructions)'),
    (8.5,  1.5, 'Agent 2\n(Enricher)'),
]
colors = ['#555', '#238636', '#9e6a03', '#238636']

for (x, y, label), color in zip(nodes, colors):
    draw_box(ax, x, y, 1.7, 0.9, label, color=color)

for i in range(len(nodes) - 1):
    draw_arrow(ax, nodes[i][0] + 0.85, 1.5, nodes[i+1][0] - 0.85, 1.5)

ax.text(5, 2.8, 'Pipeline B — Without DSPy', ha='center', fontsize=13, fontweight='bold', color='#222')

plt.tight_layout()
plt.savefig('playground/simple_no_dspy.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: simple_no_dspy.png")
