from datetime import datetime, timedelta, timezone
from io import BytesIO
from matplotlib import pyplot as plt
import numpy as np

# --- Formatting functions for LiDAR data processing ---

def gps_time_to_datetime(gps_time: float) -> datetime:
    gps_epoch = datetime(1980, 1, 6, tzinfo=timezone.utc)
    return gps_epoch + timedelta(seconds=gps_time)

def format_global_encoding(ge, tr):
    return (
        f"  - {tr("GPS Time Type")}: {ge.gps_time_type}\n"
        f"  - {tr("Waveform Internal")}: {ge.waveform_data_packets_internal}\n"
        f"  - {tr("Waveform External")}: {ge.waveform_data_packets_external}\n"
        f"  - {tr("Synthetic Returns")}: {ge.synthetic_return_numbers}\n"
        f"  - {tr("WKT")}: {ge.wkt}\n"
    )

def format_point_format(pf, tr):
    return (
        f"  - {tr("Point Format ID")}: {pf.id}\n"
        f"  - {tr("Size")}: {pf.size} {tr("bytes")}\n"
    )

# --- Graph generation functions for LiDAR data ---

def generate_pie_chart_from_counts(classes, counts, tr):
    class_info = {
        0: (tr("Created, Never Classified"), "#A0A0A0"),
        1: (tr("Unclassified"), "#B0B0B0"),
        2: (tr("Ground"), "#8B4513"),
        3: (tr("Low Vegetation"), "#ADFF2F"),
        4: (tr("Medium Vegetation"), "#32CD32"),
        5: (tr("High Vegetation"), "#006400"),
        6: (tr("Building"), "#FF4500"),
        7: (tr("Low Point (Noise)"), "#D3D3D3"),
        8: (tr("Model Key-point"), "#FFD700"),
        9: (tr("Water"), "#1E90FF"),
        10: (tr("Rail"), "#8B0000"),
        11: (tr("Road Surface"), "#A0522D"),
        12: (tr("Overlap"), "#C0C0C0"),
        13: (tr("Wire Guard"), "#00CED1"),
        14: (tr("Wire Conductor"), "#20B2AA"),
        15: (tr("Transmission Tower"), "#000080"),
        16: (tr("Wire-structure Connector"), "#708090"),
        17: (tr("Bridge Deck"), "#A9A9A9"),
        18: (tr("High Noise"), "#800080")
    }

    labels = [class_info.get(c, (f"{tr('Class')} {c}", "#CCCCCC"))[0] for c in classes]
    colors = [class_info.get(c, (tr("Unknown"), "#CCCCCC"))[1] for c in classes]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts, labels=labels, colors=colors, autopct=lambda pct: f'{pct:.1f}%', startangle=140, textprops={'fontsize': 10, 'fontweight': 'bold'})

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_return_bar_chart(unique_returns, return_counts, tr):
    from io import BytesIO
    import matplotlib.pyplot as plt

    labels = [f"{tr('Return')} {r}" for r in unique_returns]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, return_counts, color='lightgreen')

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f'{height:,}',
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha='center',
            va='bottom',
            fontsize=10,
            fontweight='bold'
        )

    # Increase y-axis limit to add vertical space above tallest bar
    max_height = max(return_counts)
    ax.set_ylim(0, max_height * 1.10) # Add 15% headroom

    ax.set_xlabel(tr("Return Number"), fontname='Arial')
    ax.set_ylabel(tr("Count"), fontname='Arial')
    plt.xticks(rotation=45)

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_density_heatmap(x, y, tr, bins=500):
    buf = BytesIO()
    fig, ax = plt.subplots(figsize=(7, 5))
    bins = min(bins, max(50, int(np.sqrt(len(x))))) if len(x) > 0 else 50
    h = ax.hist2d(x, y, bins=bins)
    cbar = fig.colorbar(h[3], ax=ax, label=tr("Point Count"))
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
