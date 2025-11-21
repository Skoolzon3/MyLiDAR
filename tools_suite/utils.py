from datetime import datetime, timedelta, timezone
from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------
# --- Auxiliary Formatting Functions ---
# --------------------------------------

def gps_time_to_datetime(gps_time: float) -> datetime:
    gps_epoch = datetime(1980, 1, 6, tzinfo=timezone.utc)
    return gps_epoch + timedelta(seconds=gps_time)

def format_global_encoding(ge, tr):
    return (
        f"  - {tr('GPS Time Type')}: {ge.gps_time_type}\n"
        f"  - {tr('Waveform Internal')}: {ge.waveform_data_packets_internal}\n"
        f"  - {tr('Waveform External')}: {ge.waveform_data_packets_external}\n"
        f"  - {tr('Synthetic Returns')}: {ge.synthetic_return_numbers}\n"
        f"  - {tr('WKT')}: {ge.wkt}\n"
    )

def format_point_format(pf, tr):
    return (
        f"  - {tr('Point Format ID')}: {pf.id}\n"
        f"  - {tr('Size')}: {pf.size} {tr('bytes')}\n"
    )

# -------------------------------------------------
# --- Graph generation functions for LiDAR data ---
# -------------------------------------------------

# --- Classification Pie Chart ---

def generate_pie_chart_from_counts(classes, counts, tr, as_buffer=True, title=None, figsize=(6, 6)):
    class_info = {
        0: (tr("Created, Never Classified"), "#A0A0A0"),
        1: (tr("Unclassified"), "#AAAAAA"),
        2: (tr("Ground"), "#AA5500"),
        3: (tr("Low Vegetation"), "#00AAAA"),
        4: (tr("Medium Vegetation"), "#55FF55"),
        5: (tr("High Vegetation"), "#00AA00"),
        6: (tr("Building"), "#FF5555"),
        7: (tr("Low Point (Noise)"), "#AA0000"),
        8: (tr("Model Key-point"), "#FFD700"),
        9: (tr("Water"), "#55FFFF"),
        10: (tr("Rail"), "#AA00AA"),
        11: (tr("Road Surface"), "#A0522D"),
        12: (tr("Overlap"), "#555555"),
        13: (tr("Wire Guard"), "#00CED1"),
        14: (tr("Wire Conductor"), "#20B2AA"),
        15: (tr("Transmission Tower"), "#000080"),
        16: (tr("Wire-structure Connector"), "#708090"),
        17: (tr("Bridge Deck"), "#5555FF"),
        18: (tr("High Noise"), "#646464"),
    }

    labels = [class_info.get(c, (f"{tr('Class')} {c}", "#CCCCCC"))[0] for c in classes]
    colors = [class_info.get(c, (tr("Unknown"), "#CCCCCC"))[1] for c in classes]

    fig, ax = plt.subplots(figsize=figsize)
    ax.pie(
        counts,
        labels=labels,
        colors=colors,
        autopct=lambda pct: f'{pct:.1f}%',
        startangle=140,
        textprops={'fontsize': 10, 'fontweight': 'bold'}
    )

    if title:
        ax.set_title(title, fontweight="bold")

    if as_buffer:
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf
    else:
        return fig

# --- Return Count Histogram ---

def generate_return_bar_chart(unique_returns, return_counts, tr, as_buffer=True, title=None, figsize=(6, 4)):
    labels = [f"{r}" for r in unique_returns]

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(labels, return_counts, color='lightgreen')

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f'{height:,}',
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 5),
            textcoords="offset points",
            ha='center',
            va='bottom',
            fontsize=10
        )

    ax.set_yscale('log')

    min_positive = min([v for v in return_counts if v > 0])
    ax.set_ylim(bottom=max(min_positive * 0.8, 1e-1))
    max_height = max(return_counts)
    ax.set_ylim(top=max_height * 10)

    ax.set_xlabel(tr("Return Number"), fontname='Arial')
    ax.set_ylabel(tr("Count"), fontname='Arial')
    if title:
        ax.set_title(title, fontweight='bold')
    plt.xticks(rotation=45)

    if as_buffer:
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf
    else:
        return fig

# -- Point Density Heatmap

def generate_density_heatmap(x, y, tr, bins=500, as_buffer=True, title=None, figsize=(7, 5)):
    fig, ax = plt.subplots(figsize=figsize)
    bins = min(bins, max(50, int(np.sqrt(len(x))))) if len(x) > 0 else 50
    h = ax.hist2d(x, y, bins=bins, cmap="viridis")
    cbar = fig.colorbar(h[3], ax=ax, label=tr("Point Count"))
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    if title:
        ax.set_title(title, fontweight="bold")

    if as_buffer:
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf
    else:
        return fig
