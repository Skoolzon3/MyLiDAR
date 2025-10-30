# --- General imports ---
from .report_data import ReportData
from datetime import datetime

# --- PDF generation imports ---
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# --- Graph generation imports ---
from ..utils import generate_pie_chart_from_counts, generate_return_bar_chart, generate_density_heatmap

# ------------------------------------
# --- Global Classification Mapping ---
# ------------------------------------

CLASS_INFO = {
    0: ("Created, Never Classified", "#A0A0A0"),
    1: ("Unclassified", "#B0B0B0"),
    2: ("Ground", "#8B4513"),
    3: ("Low Vegetation", "#ADFF2F"),
    4: ("Medium Vegetation", "#32CD32"),
    5: ("High Vegetation", "#006400"),
    6: ("Building", "#FF4500"),
    7: ("Low Point (Noise)", "#D3D3D3"),
    8: ("Model Key-point", "#FFD700"),
    9: ("Water", "#1E90FF"),
    10: ("Rail", "#8B0000"),
    11: ("Road Surface", "#A0522D"),
    12: ("Overlap", "#C0C0C0"),
    13: ("Wire Guard", "#00CED1"),
    14: ("Wire Conductor", "#20B2AA"),
    15: ("Transmission Tower", "#000080"),
    16: ("Wire-structure Connector", "#708090"),
    17: ("Bridge Deck", "#A9A9A9"),
    18: ("High Noise", "#800080"),
}

# ------------------------------
# --- Text Report Generation ---
# ------------------------------

def generate_txt_report(self, path, data: ReportData, tr):
    with open(path, "w", encoding="utf-8") as f:
        f.write("==================\n")
        f.write(tr("LiDAR File Report") + "\n")
        f.write("==================\n\n")

        current_time = datetime.now()
        f.write(f"{tr('Report date')}: {current_time}\n")

        if data.file_name:
            f.write(f"{tr('Name')}: {data.file_name}\n")
            f.write("\n")

        # -- File Metadata --
        if (data.file_source or data.global_encoding or data.system_id or
            data.gen_software or data.version or data.point_format or data.creation_date):
            f.write(f"--- {tr('File Metadata')} ---\n")
            if data.file_source:
                f.write(f"{tr('File Source ID')}: {data.file_source}\n")
            if data.global_encoding:
                f.write(f"{tr('Global Encoding')}:\n{data.global_encoding}")
            if data.system_id:
                f.write(f"{tr('System ID')}: {data.system_id}\n")
            if data.gen_software:
                f.write(f"{tr('Generating Software')}: {data.gen_software}\n")
            if data.version:
                f.write(f"{tr('Version')}: {data.version}\n")
            if data.point_format:
                f.write(f"{tr('Point Format')}:\n{data.point_format}")

            if data.creation_date:
                f.write(f"{tr('Creation Date')}: {data.creation_date}\n")
            f.write("\n")

        # -- Intensity --
        if (data.min_intensity or data.max_intensity or data.mean_intensity or data.sd_intensity):
            f.write(f"--- {tr('Intensity')} ---\n")
            if data.min_intensity:
                f.write(f"{tr('Min Intensity')}: {data.min_intensity}\n")
            if data.max_intensity:
                f.write(f"{tr('Max Intensity')}: {data.max_intensity}\n")
            if data.mean_intensity:
                f.write(f"{tr('Mean Intensity')}: {data.mean_intensity:.2f}\n")
            if data.sd_intensity:
                f.write(f"{tr('Standard deviation')}: {data.sd_intensity:.2f}\n")
            f.write("\n")

        # -- Spatial Measures --
        if (data.num_points or data.area or data.density or
            data.bounds or data.x_axis_bounds or data.y_axis_bounds):
            f.write(f"--- {tr('Spatial Measures')} ---\n")
            if data.num_points:
                f.write(f"{tr('Number of Points')}: {data.num_points}\n")
            if data.area:
                f.write(f"{tr('Area')}: {data.area}\n")
            if data.density:
                f.write(f"{tr('Density')}: {data.density}\n")
            if data.bounds:
                f.write(f"{tr('Bounds Min')}: {data.bounds[0]}\n")
                f.write(f"{tr('Bounds Max')}: {data.bounds[1]}\n")
            if data.x_axis_bounds:
                f.write(f"{tr('X-Axis Bounds')}: {data.x_axis_bounds}\n")
            if data.y_axis_bounds:
                f.write(f"{tr('Y-Axis Bounds')}: {data.y_axis_bounds}\n")
            if data.z_axis_bounds:
                f.write(f"{tr('Z-Axis Bounds')}: {data.z_axis_bounds}\n")
            f.write("\n")

        # -- GPS Time --
        if (data.min_time or data.max_time):
            f.write(f"--- {tr('GPS Time')} ---\n")
            if data.min_time:
                f.write(f"{tr('Min GPS Time')}: {data.min_time}\n")
            if data.max_time:
                f.write(f"{tr('Max GPS Time')}: {data.max_time}\n")
            f.write("\n")

        # -- Classifications --
        if data.unique_classes is not None and data.class_counts is not None:
            from .report_functions import CLASS_INFO

            f.write(f"--- {tr('Classification Counts')} ---\n")
            for cls, count in zip(data.unique_classes, data.class_counts):
                class_name_raw = CLASS_INFO.get(cls, ("Unknown", "#000000"))[0]
                class_name = tr(class_name_raw)
                f.write(f" - {tr('Class')} {cls} ({class_name}): {count}\n")
            f.write("\n")

        # -- Returns --
        if data.unique_returns is not None and data.return_counts is not None:
            f.write(f"--- {tr('Return Number Counts')} ---\n")
            for ret, count in zip(data.unique_returns, data.return_counts):
                f.write(f" - {tr('Return')} {ret}: {count}\n")
            f.write("\n")


# --------------------------------------
# --- Dock Report Content Generation ---
# --------------------------------------

def generate_dock_content(self, data: ReportData, tr) -> str:
    lines = []
    lines.append("==================")
    lines.append(tr("LiDAR File Report"))
    lines.append("==================\n")

    current_time = datetime.now()
    lines.append(f"{tr('Report date')}: {current_time}\n")

    if data.file_name:
        lines.append(f"{tr('Name')}: {data.file_name}\n")

    # -- File Metadata --
    if (data.file_source or data.global_encoding or data.system_id or
        data.gen_software or data.version or data.point_format or data.creation_date):
        lines.append(f"--- {tr('File Metadata')} ---")
        if data.file_source:
            lines.append(f"{tr('File Source ID')}: {data.file_source}")
        if data.global_encoding:
            lines.append(f"{tr('Global Encoding')}:\n{data.global_encoding.strip()}")
        if data.system_id:
            lines.append(f"{tr('System ID')}: {data.system_id}")
        if data.gen_software:
            lines.append(f"{tr('Generating Software')}: {data.gen_software}")
        if data.version:
            lines.append(f"{tr('Version')}: {data.version}")
        if data.point_format:
            lines.append(f"{tr('Point Format')}:\n{data.point_format.strip()}")
        if data.creation_date:
            lines.append(f"{tr('Creation Date')}: {data.creation_date}")
        lines.append("")

    # -- Intensity --
    if (data.min_intensity or data.max_intensity or data.mean_intensity or data.sd_intensity):
        lines.append(f"--- {tr('Intensity')} ---")
        if data.min_intensity:
            lines.append(f"{tr('Min Intensity')}: {data.min_intensity}")
        if data.max_intensity:
            lines.append(f"{tr('Max Intensity')}: {data.max_intensity}")
        if data.mean_intensity:
            lines.append(f"{tr('Mean Intensity')}: {data.mean_intensity:.2f}")
        if data.sd_intensity:
            lines.append(f"{tr('Standard deviation')}: {data.sd_intensity:.2f}")
        lines.append("")

    # -- Spatial Measures --
    if (data.num_points or data.area or data.density or
        data.bounds or data.x_axis_bounds or data.y_axis_bounds):
        lines.append(f"--- {tr('Spatial Measures')} ---")
        if data.num_points:
            lines.append(f"{tr('Number of Points')}: {data.num_points}")
        if data.area:
            lines.append(f"{tr('Area')}: {data.area}")
        if data.density:
            lines.append(f"{tr('Density')}: {data.density}")
        if data.bounds:
            lines.append(f"{tr('Bounds Min')}: {data.bounds[0]}")
            lines.append(f"{tr('Bounds Max')}: {data.bounds[1]}")
        if data.x_axis_bounds:
            lines.append(f"{tr('X-Axis Bounds')}: {data.x_axis_bounds}")
        if data.y_axis_bounds:
            lines.append(f"{tr('Y-Axis Bounds')}: {data.y_axis_bounds}")
        if data.z_axis_bounds:
            lines.append(f"{tr('Z-Axis Bounds')}: {data.z_axis_bounds}")
        lines.append("")

    # -- GPS Time --
    if (data.min_time or data.max_time):
        lines.append(f"--- {tr('GPS Time')} ---")
        if data.min_time:
            lines.append(f"{tr('Min GPS Time')}: {data.min_time}")
        if data.max_time:
            lines.append(f"{tr('Max GPS Time')}: {data.max_time}")
        lines.append("")

    # -- Classifications --
    if data.unique_classes is not None and data.class_counts is not None:
        from .report_functions import CLASS_INFO

        lines.append(f"--- {tr('Classification Counts')} ---")
        for cls, count in zip(data.unique_classes, data.class_counts):
            class_name_raw = CLASS_INFO.get(cls, ("Unknown", "#000000"))[0]
            class_name = tr(class_name_raw)
            lines.append(f" - {tr('Class')} {cls} ({class_name}): {count}")

    # -- Returns --
    if data.unique_returns is not None and data.return_counts is not None:
        lines.append(f"\n--- {tr('Return Number Counts')} ---")
        for ret, count in zip(data.unique_returns, data.return_counts):
            lines.append(f" - {tr('Return')} {ret}: {count}")
        lines.append("")

    return "\n".join(lines)


# ----------------------------------
# --- Markdown Report Generation ---
# ----------------------------------

def generate_markdown_report(self, path, data: ReportData, tr):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {tr('LiDAR File Report')}\n\n")

        current_time = datetime.now()
        f.write(f"**{tr('Report date')}**: `{current_time}`\n")

        if data.file_name:
            f.write(f"\n**{tr('File')}:** `{data.file_name}`\n\n")

        # -- File Metadata --
        if (data.file_source or data.global_encoding or data.system_id or
            data.gen_software or data.version or data.point_format or data.creation_date):
            f.write(f"## {tr('File Metadata')}\n")
            if data.file_source:
                f.write(f"- **{tr('File Source ID')}:** `{data.file_source}`\n")
            if data.global_encoding:
                f.write(f"- **{tr('Global Encoding')}:**\n{data.global_encoding}")
            if data.system_id:
                f.write(f"- **{tr('System ID')}:** `{data.system_id}`\n")
            if data.gen_software:
                f.write(f"- **{tr('Generating Software')}:** `{data.gen_software}`\n")
            if data.version:
                f.write(f"- **{tr('Version')}:** `{data.version}`\n")
            if data.point_format:
                f.write(f"- **{tr('Point Format')}:**\n{data.point_format}")
            if data.creation_date:
                f.write(f"- **{tr('Creation Date')}:** `{data.creation_date}`\n")
            f.write("\n")

        # -- Intensity --
        if data.min_intensity or data.max_intensity:
            f.write(f"## {tr('Intensity')}\n")
            if data.min_intensity:
                f.write(f"- **{tr('Min Intensity')}:** `{data.min_intensity}`\n")
            if data.max_intensity:
                f.write(f"- **{tr('Max Intensity')}:** `{data.max_intensity}`\n")
            if data.mean_intensity:
                f.write(f"- **{tr('Mean Intensity')}:** `{data.mean_intensity:.2f}`\n")
            if data.sd_intensity:
                f.write(f"- **{tr('Standard deviation')}:** `{data.sd_intensity:.2f}`\n")
            f.write("\n")

        # -- Spatial Measures --
        if (data.num_points or data.area or data.density or
            data.bounds or data.x_axis_bounds or data.y_axis_bounds):
            f.write(f"## {tr('Spatial Measures')}\n")
            if data.num_points:
                f.write(f"- **{tr('Number of Points')}:** `{data.num_points}`\n")
            if data.area:
                f.write(f"- **{tr('Area')}:** `{data.area}`\n")
            if data.density:
                f.write(f"- **{tr('Density')}:** `{data.density}`\n")
            if data.bounds:
                f.write(f"- **{tr('Bounds Min')}:** `{data.bounds[0]}`\n")
                f.write(f"- **{tr('Bounds Max')}:** `{data.bounds[1]}`\n")
            if data.x_axis_bounds:
                f.write(f"- **{tr('X-Axis Bounds')}:** `{data.x_axis_bounds}`\n")
            if data.y_axis_bounds:
                f.write(f"- **{tr('Y-Axis Bounds')}:** `{data.y_axis_bounds}`\n")
            if data.z_axis_bounds:
                f.write(f"- **{tr('Z-Axis Bounds')}:** `{data.z_axis_bounds}`\n")
            f.write("\n")

        # -- GPS Time --
        if (data.min_time or data.max_time):
            f.write(f"## {tr('GPS Time')}\n")
            if data.min_time:
                f.write(f"- **{tr('Min GPS Time')}:** `{data.min_time}`\n")
            if data.max_time:
                f.write(f"- **{tr('Max GPS Time')}:** `{data.max_time}`\n")
            f.write("\n")

        # -- Classifications --
        if data.unique_classes is not None and data.class_counts is not None:
            from .report_functions import CLASS_INFO

            f.write(f"## {tr('Classification Counts')}\n")
            for cls, count in zip(data.unique_classes, data.class_counts):
                class_name_raw = CLASS_INFO.get(cls, ("Unknown", "#000000"))[0]
                class_name = tr(class_name_raw)
                f.write(f" - **{tr('Class')} {cls}** ({class_name}): `{count}`\n")
            f.write("\n")

        # -- Returns --
        if data.unique_returns is not None and data.return_counts is not None:
            f.write(f"## {tr('Return Number Counts')}\n")
            for ret, count in zip(data.unique_returns, data.return_counts):
                f.write(f" - **{tr('Return')} {ret}**: `{count}`\n")
            f.write("\n")


# -----------------------------
# --- PDF Report Generation ---
# -----------------------------

def generate_pdf_report(self, path, data: ReportData, tr):
    canvas = Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 2 * cm

    def draw_page_number():
        canvas.setFont("Helvetica", 10)
        page_num_text = f"{canvas.getPageNumber()}"
        canvas.drawRightString(width - 2 * cm, 1.5 * cm, page_num_text)

    def check_page_space(lines_needed=1):
        nonlocal y
        if y < lines_needed * 1.2 * cm:

            draw_page_number()
            canvas.showPage()
            y = height - 2 * cm

            y = height - 2 * cm
            canvas.setFont("Helvetica", 12)

    def write_spacing(lines=1):
        nonlocal y
        y -= lines * 0.6 * cm
        check_page_space()

    def write_heading(text, level=1):
        nonlocal y
        size = {1: 16, 2: 14}.get(level, 12)
        write_spacing(1.5 if level == 1 else 1.2)
        canvas.setFont("Helvetica-Bold", size)
        canvas.drawString(2 * cm, y, text)
        y -= 0.7 * cm
        check_page_space()

    def write_item(label, value):
        nonlocal y
        canvas.setFont("Helvetica-Bold", 12)
        label_text = f"- {label}:"
        canvas.drawString(2 * cm, y, label_text)

        label_width = canvas.stringWidth(label_text, "Helvetica-Bold", 12)
        value_x = 2 * cm + label_width + 0.3 * cm

        if value_x > width - 6 * cm:
            value_x = 7 * cm

        canvas.setFont("Courier", 12)
        canvas.drawString(value_x, y, str(value))

        y -= 0.6 * cm
        check_page_space()

    def write_item_filename(label, value):
        nonlocal y
        canvas.setFont("Helvetica-Bold", 12)
        label_text = f"- {label}:"
        canvas.drawString(2 * cm, y, label_text)

        label_width = canvas.stringWidth(label_text, "Helvetica-Bold", 12)
        value_x = 2 * cm + label_width + 0.3 * cm
        max_width = width - value_x - 2 * cm

        value_str = str(value)
        canvas.setFont("Courier", 12)

        lines = simpleSplit(value_str, "Courier", 12, max_width)

        if len(lines) == 1:
            line = lines[0]
            line_width = canvas.stringWidth(line, "Courier", 12)
            if line_width > max_width:
                avg_char_width = canvas.stringWidth("M", "Courier", 12)
                max_chars = int(max_width // avg_char_width)
                lines = [line[i:i + max_chars] for i in range(0, len(line), max_chars)]

        for line in lines:
            canvas.drawString(value_x, y, line)
            y -= 0.6 * cm
            check_page_space()

    write_heading(tr("LiDAR File Report"), level=1)

    current_time = datetime.now()
    write_item(tr("Report date"), current_time)
    if data.file_name:
        write_item_filename(tr("File"), data.file_name)

    # -- File Metadata --
    if (data.file_source or data.global_encoding or data.system_id or
        data.gen_software or data.version or data.point_format or data.creation_date):
        write_heading(tr("File Metadata"), level=2)
        if data.file_source:
            write_item(tr("File Source ID"), data.file_source)

        if data.global_encoding:
            write_item(tr("Global Encoding"), "")
            for line in str(data.global_encoding).splitlines():
                cleaned_line = line.lstrip("- ").strip()
                canvas.setFont("Courier", 12)
                canvas.drawString(3 * cm, y, f"• {cleaned_line}")
                y -= 0.6 * cm
                check_page_space()

        if data.system_id:
            write_item(tr("System ID"), data.system_id)
        if data.gen_software:
            write_item(tr("Generating Software"), data.gen_software)
        if data.version:
            write_item(tr("Version"), data.version)

        if data.point_format:
            write_item(tr("Point Format"), "")
            for line in str(data.point_format).splitlines():
                cleaned_line = line.lstrip("- ").strip()
                canvas.setFont("Courier", 12)
                canvas.drawString(3 * cm, y, f"• {cleaned_line}")
                y -= 0.6 * cm
                check_page_space()

        if data.creation_date:
            write_item(tr("Creation Date"), data.creation_date)

    # -- Intensity --
    if data.min_intensity or data.max_intensity or data.mean_intensity or data.sd_intensity:
        write_heading(tr("Intensity"), level=2)
        if data.min_intensity:
            write_item(tr("Min Intensity"), data.min_intensity)
        if data.max_intensity:
            write_item(tr("Max Intensity"), data.max_intensity)
        if data.mean_intensity:
            write_item(tr("Mean Intensity"), f"{data.mean_intensity:.2f}")
        if data.sd_intensity:
            write_item(tr("Standard deviation"), f"{data.sd_intensity:.2f}")

    # -- Spatial Measures --
    if (data.num_points or data.area or data.density or
        data.bounds or data.x_axis_bounds or data.y_axis_bounds):
        write_heading(tr("Spatial Measures"), level=2)
        if data.num_points:
            write_item(tr("Number of Points"), data.num_points)
        if data.area:
            write_item(tr("Area"), data.area)
        if data.density:
            write_item(tr("Density"), data.density)
        if data.bounds:
            write_item(tr("Bounds Min"), data.bounds[0])
            write_item(tr("Bounds Max"), data.bounds[1])
        if data.x_axis_bounds:
            write_item(tr("X-Axis Bounds"), data.x_axis_bounds)
        if data.y_axis_bounds:
            write_item(tr("Y-Axis Bounds"), data.y_axis_bounds)
        if data.z_axis_bounds:
            write_item(tr("Z-Axis Bounds"), data.z_axis_bounds)

    # -- GPS Time --
    if (data.min_time or data.max_time):
        write_heading(tr("GPS Time"), level=2)
        if data.min_time:
            write_item(tr("Min GPS Time"), data.min_time)
        if data.max_time:
            write_item(tr("Max GPS Time"), data.max_time)

    # -- Classifications --
    if data.unique_classes is not None and data.class_counts is not None:
        from .report_functions import CLASS_INFO

        draw_page_number()
        canvas.showPage()
        canvas.setFont("Helvetica", 12)
        y = height - 2 * cm

        write_heading(tr("Classification Counts"), level=2)

        # -- Classification distribution pie chart --
        chart_buf = generate_pie_chart_from_counts(data.unique_classes, data.class_counts, self.tr)
        chart_img = ImageReader(chart_buf)
        chart_width, chart_height = 15 * cm, 12 * cm
        center_x = (width - chart_width) / 2
        if y - chart_height < 2 * cm:
            canvas.showPage()
            y = height - 2 * cm
        canvas.drawImage(chart_img, center_x, y - chart_height, width=chart_width, height=chart_height)
        y -= chart_height + 0.5 * cm

        for cls, count in zip(data.unique_classes, data.class_counts):
            class_name_raw = CLASS_INFO.get(cls, ("Unknown", "#000000"))[0]
            class_name = tr(class_name_raw)
            write_item(f"{tr('Class')} {cls} ({class_name})", count)

    # -- Return number --
    if data.unique_returns is not None and data.return_counts is not None:
        draw_page_number()
        canvas.showPage()
        canvas.setFont("Helvetica", 12)
        y = height - 2 * cm

        write_heading(tr("Return Number Counts"), level=2)

        # -- Return number distribution bar chart --
        return_chart_buf = generate_return_bar_chart(data.unique_returns, data.return_counts, self.tr)
        return_chart_img = ImageReader(return_chart_buf)
        chart_width, chart_height = 14 * cm, 12 * cm
        center_x = (width - chart_width) / 2
        if y - chart_height < 2 * cm:
            canvas.showPage()
            y = height - 2 * cm
        canvas.drawImage(return_chart_img, center_x, y - chart_height, width=chart_width, height=chart_height)
        y -= chart_height + 0.5 * cm

        for ret, count in zip(data.unique_returns, data.return_counts):
            write_item(f"{tr('Return')} {ret}", count)

    # -- Point density --
    if getattr(data, "density", None) is not None and hasattr(data, "x") and hasattr(data, "y") and data.x is not None and data.y is not None:
        draw_page_number()
        canvas.showPage()
        canvas.setFont("Helvetica", 12)
        y = height - 2 * cm

        write_heading(tr("Point Density Heatmap"), level=2)

        # -- Point density heatmap --
        heatmap_buf = generate_density_heatmap(data.x, data.y, tr)
        heatmap_img = ImageReader(heatmap_buf)
        chart_width, chart_height = 18 * cm, 14 * cm
        center_x = (width - chart_width) / 2
        if y - chart_height < 2 * cm:
            canvas.showPage()
            y = height - 2 * cm
        canvas.drawImage(heatmap_img, center_x, y - chart_height, width=chart_width, height=chart_height)
        y -= chart_height + 0.5 * cm

    draw_page_number()
    canvas.save()

# ----------------------------------
# --- LaTeX Report Generation ---
# ----------------------------------

def generate_latex_report(self, path, data: ReportData, tr):
    def tex_escape(s):
        """Escape special LaTeX characters."""
        if s is None:
            return ""
        return (
            str(s)
            .replace("\\", "\\textbackslash{}")
            .replace("&", "\\&")
            .replace("%", "\\%")
            .replace("$", "\\$")
            .replace("#", "\\#")
            .replace("_", "\\_")
            .replace("{", "\\{")
            .replace("}", "\\}")
            .replace("~", "\\textasciitilde{}")
            .replace("^", "\\textasciicircum{}")
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\\documentclass{article}\n")
        f.write("\\usepackage{graphicx}\n")
        f.write("\\usepackage[margin=1in]{geometry}\n")
        f.write("\\usepackage{longtable}\n")
        f.write("\\usepackage{booktabs}\n")
        f.write("\\title{%s}\n" % tex_escape(tr("LiDAR File Report")))
        f.write("\\author{}\n")
        current_time = datetime.now()
        f.write("\\date{%s: %s}\n" % (tex_escape(tr("Report date")), tex_escape(current_time)))
        f.write("\\begin{document}\n")
        f.write("\\maketitle\n")

        if data.file_name:
            f.write("\\textbf{%s}: \\texttt{%s}\n" % (tex_escape(tr("File")), tex_escape(data.file_name)))

        # -- File Metadata --
        if (data.file_source or data.global_encoding or data.system_id or
            data.gen_software or data.version or data.point_format or data.creation_date):
            f.write("\\section*{%s}\n" % tex_escape(tr("File Metadata")))
            if data.file_source:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("File Source ID")), tex_escape(data.file_source)))

            if data.global_encoding:
                f.write("\\textbf{%s}:\n" % tex_escape(tr("Global Encoding")))
                lines = str(data.global_encoding).splitlines()
                items = [line.strip(" -") for line in lines if line.strip()]
                if items:
                    f.write("\\begin{enumerate}\n")
                    for item in items:
                        f.write("\\item %s\n" % tex_escape(item))
                    f.write("\\end{enumerate}\n")
                else:
                    f.write("\\texttt{%s}\\\\\n" % tex_escape(data.global_encoding))

            if data.system_id:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("System ID")), tex_escape(data.system_id)))
            if data.gen_software:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Generating Software")), tex_escape(data.gen_software)))
            if data.version:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Version")), tex_escape(data.version)))

            if data.point_format:
                # f.write("\\textbf{%s}:\\\\\\texttt{%s}\\\\\n" % (tex_escape(tr("Point Format")), tex_escape(data.point_format)))
                f.write("\\textbf{%s}:\n" % tex_escape(tr("Point Format")))
                lines = str(data.point_format).splitlines()
                items = [line.strip(" -") for line in lines if line.strip()]
                if items:
                    f.write("\\begin{enumerate}\n")
                    for item in items:
                        f.write("\\item %s\n" % tex_escape(item))
                    f.write("\\end{enumerate}\n")
                else:
                    f.write("\\texttt{%s}\\\\\n" % tex_escape(data.point_format))

            if data.creation_date:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Creation Date")), tex_escape(data.creation_date)))
            f.write("\n")

        # -- Intensity --
        if data.min_intensity or data.max_intensity:
            f.write("\\section*{%s}\n" % tex_escape(tr("Intensity")))
            if data.min_intensity:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Min Intensity")), data.min_intensity))
            if data.max_intensity:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Max Intensity")), data.max_intensity))
            if data.mean_intensity:
                f.write("\\textbf{%s}: \\texttt{%.2f}\\\\\n" % (tex_escape(tr("Mean Intensity")), data.mean_intensity))
            if data.sd_intensity:
                f.write("\\textbf{%s}: \\texttt{%.2f}\\\\\n" % (tex_escape(tr("Standard deviation")), data.sd_intensity))
            f.write("\n")

        # -- Spatial Measures --
        if (data.num_points or data.area or data.density or
            data.bounds or data.x_axis_bounds or data.y_axis_bounds):
            f.write("\\section*{%s}\n" % tex_escape(tr("Spatial Measures")))
            if data.num_points:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Number of Points")), data.num_points))
            if data.area:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Area")), data.area))
            if data.density:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Density")), data.density))
            if data.bounds:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Bounds Min")), data.bounds[0]))
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Bounds Max")), data.bounds[1]))
            if data.x_axis_bounds:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("X-Axis Bounds")), data.x_axis_bounds))
            if data.y_axis_bounds:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Y-Axis Bounds")), data.y_axis_bounds))
            if data.z_axis_bounds:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Z-Axis Bounds")), data.z_axis_bounds))
            f.write("\n")

        # -- GPS Time --
        if data.min_time or data.max_time:
            f.write("\\section*{%s}\n" % tex_escape(tr("GPS Time")))
            if data.min_time:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Min GPS Time")), data.min_time))
            if data.max_time:
                f.write("\\textbf{%s}: \\texttt{%s}\\\\\n" % (tex_escape(tr("Max GPS Time")), data.max_time))
            f.write("\n")

        # -- Classifications --
        if data.unique_classes is not None and data.class_counts is not None:
            from .report_functions import CLASS_INFO
            f.write("\\section*{%s}\n" % tex_escape(tr("Classification Counts")))
            f.write("\\begin{longtable}{ll}\n\\toprule\n")
            f.write(f"{tex_escape(tr('Class ID'))} & {tex_escape(tr('Count'))} \\\\\n\\midrule\n")
            for cls, count in zip(data.unique_classes, data.class_counts):
                class_name_raw = CLASS_INFO.get(cls, ("Unknown", "#000000"))[0]
                class_name = tr(class_name_raw)
                f.write(f"{cls} ({tex_escape(class_name)}) & {count} \\\\\n")
            f.write("\\bottomrule\n\\end{longtable}\n\n")

        # -- Returns --
        if data.unique_returns is not None and data.return_counts is not None:
            f.write("\\section*{%s}\n" % tex_escape(tr("Return Number Counts")))
            f.write("\\begin{longtable}{ll}\n\\toprule\n")
            f.write(f"{tex_escape(tr('Return'))} & {tex_escape(tr('Count'))} \\\\\n\\midrule\n")
            for ret, count in zip(data.unique_returns, data.return_counts):
                f.write(f"{ret} & {count} \\\\\n")
            f.write("\\bottomrule\n\\end{longtable}\n\n")

        # --- End of Document ---
        f.write("\\end{document}\n")
