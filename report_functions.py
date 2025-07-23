from .report_data import ReportData
from datetime import datetime

# PDF generation imports
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# --- Text Report Generation ---

def generate_txt_report(self, path, data: ReportData):
    with open(path, "w", encoding="utf-8") as f:
        f.write("==================\n")
        f.write("LiDAR File Report\n")
        f.write("==================\n\n")

        current_time = datetime.now()
        f.write(f"Report date: {current_time}\n")

        if data.file_name:
            f.write(f"Name: {data.file_name}\n")
            f.write("\n")

        # -- File Metadata --
        if (data.file_source or data.global_encoding or data.system_id or
            data.gen_software or data.version or data.point_format or data.creation_date):
            f.write("File Metadata:\n")
            if data.file_source:
                f.write(f"File Source ID: {data.file_source}\n")
            if data.global_encoding:
                f.write(f"Global Encoding:\n{data.global_encoding}")
            if data.system_id:
                f.write(f"System ID: {data.system_id}\n")
            if data.gen_software:
                f.write(f"Generating Software: {data.gen_software}\n")
            if data.version:
                f.write(f"Version: {data.version}\n")
            if data.point_format:
                f.write(f"Point Format:\n{data.point_format}")

            if data.creation_date:
                f.write(f"Creation Date: {data.creation_date}\n")
            f.write("\n")

        # -- Intensity --
        if (data.min_intensity or data.max_intensity):
            f.write("Intensity:\n")
            if data.min_intensity:
                f.write(f"Min Intensity: {data.min_intensity}\n")
            if data.max_intensity:
                f.write(f"Max Intensity: {data.max_intensity}\n")
            f.write("\n")

        # -- Spatial Measures --
        if (data.num_points or data.area or data.density or
            data.bounds or data.x_axis_bounds or data.y_axis_bounds):
            f.write("Spatial Measures:\n")
            if data.num_points:
                f.write(f"Number of Points: {data.num_points}\n")
            if data.area:
                f.write(f"Area: {data.area}\n")
            if data.density:
                f.write(f"Density: {data.density}\n")
            if data.bounds:
                f.write(f"Bounds Min: {data.bounds[0]}\n")
                f.write(f"Bounds Max: {data.bounds[1]}\n")
            if data.x_axis_bounds:
                f.write(f"X-Axis Bounds: {data.x_axis_bounds}\n")
            if data.y_axis_bounds:
                f.write(f"Y-Axis Bounds: {data.y_axis_bounds}\n")
            f.write("\n")

        # -- GPS Time --
        if (data.min_time or data.max_time):
            f.write("GPS Time:\n")
            if data.min_time:
                f.write(f"Min GPS Time: {data.min_time}\n")
            if data.max_time:
                f.write(f"Max GPS Time: {data.max_time}\n")
            f.write("\n")

        # -- Classifications --
        if data.unique_classes is not None and data.class_counts is not None:
            f.write("\nClassification Counts:\n")
            for cls, count in zip(data.unique_classes, data.class_counts):
                f.write(f" - Class {cls}: {count}\n")
            f.write("\n")

        # -- Returns --
        if data.unique_returns is not None and data.return_counts is not None:
            f.write("\nReturn Number Counts:\n")
            for ret, count in zip(data.unique_returns, data.return_counts):
                f.write(f" - Return {ret}: {count}\n")
            f.write("\n")

# --- Markdown Report Generation ---

def generate_markdown_report(self, path, data: ReportData):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# LiDAR File Report\n\n")

        current_time = datetime.now()
        f.write(f"**Report date**: `{current_time}`\n")

        if data.file_name:
            f.write(f"**File:** `{data.file_name}`\n")
            f.write("\n")

        # -- File Metadata --
        if (data.file_source or data.global_encoding or data.system_id or
            data.gen_software or data.version or data.point_format or data.creation_date):
            f.write("## File Metadata\n")
            if data.file_source:
                f.write(f"- **File Source ID:** `{data.file_source}`\n")
            if data.global_encoding:
                f.write(f"- **Global Encoding:**\n{data.global_encoding}")
            if data.system_id:
                f.write(f"- **System ID:** `{data.system_id}`\n")
            if data.gen_software:
                f.write(f"- **Generating Software:** `{data.gen_software}`\n")
            if data.version:
                f.write(f"- **Version:** `{data.version}`\n")
            if data.point_format:
                f.write(f"- **Point Format:**\n{data.point_format}")
            if data.creation_date:
                f.write(f"- **Creation Date:** `{data.creation_date}`\n")
            f.write("\n")

        # -- Intensity --
        if data.min_intensity or data.max_intensity:
            f.write("## Intensity\n")
            if data.min_intensity:
                f.write(f"- **Min Intensity:** `{data.min_intensity}`\n")
            if data.max_intensity:
                f.write(f"- **Max Intensity:** `{data.max_intensity}`\n")
            f.write("\n")

        # -- Spatial Measures --
        if (data.num_points or data.area or data.density or
            data.bounds or data.x_axis_bounds or data.y_axis_bounds):
            f.write("## Spatial Measures\n")
            if data.num_points:
                f.write(f"- **Number of Points:** `{data.num_points}`\n")
            if data.area:
                f.write(f"- **Area:** `{data.area}`\n")
            if data.density:
                f.write(f"- **Density:** `{data.density}`\n")
            if data.bounds:
                f.write(f"- **Bounds Min:** `{data.bounds[0]}`\n")
                f.write(f"- **Bounds Max:** `{data.bounds[1]}`\n")
            if data.x_axis_bounds:
                f.write(f"- **X-Axis Bounds:** `{data.x_axis_bounds}`\n")
            if data.y_axis_bounds:
                f.write(f"- **Y-Axis Bounds:** `{data.y_axis_bounds}`\n")
            f.write("\n")

        # -- GPS Time --
        if (data.min_time or data.max_time):
            f.write("## GPS Time\n")
            if data.min_time:
                f.write(f"- **Min GPS Time:** `{data.min_time}`\n")
            if data.max_time:
                f.write(f"- **Max GPS Time:** `{data.max_time}`\n")
            f.write("\n")

        # -- Classifications --
        if data.unique_classes is not None and data.class_counts is not None:
            f.write("## Classification Counts\n")
            for cls, count in zip(data.unique_classes, data.class_counts):
                f.write(f" - **Class {cls}**: {count}\n")
            f.write("\n")

        # -- Returns --
        if data.unique_returns is not None and data.return_counts is not None:
            f.write("## Return Number Counts\n")
            for ret, count in zip(data.unique_returns, data.return_counts):
                f.write(f" - **Return {ret}**: {count}\n")
            f.write("\n")

# --- PDF Report Generation ---

def generate_pdf_report(self, path, data: ReportData):
    canvas = Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 2 * cm

    def check_page_space(lines_needed=1):
        nonlocal y
        if y < lines_needed * 1.2 * cm:
            canvas.showPage()
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
        canvas.drawString(2 * cm, y, f"- {label}:")
        canvas.setFont("Courier", 12)
        canvas.drawString(7 * cm, y, str(value))
        y -= 0.6 * cm
        check_page_space()

    write_heading("LiDAR File Report", level=1)

    current_time = datetime.now()
    write_item("Report date", current_time)
    if data.file_name:
        write_item("File", data.file_name)

    # -- File Metadata --
    if (data.file_source or data.global_encoding or data.system_id or
        data.gen_software or data.version or data.point_format or data.creation_date):
        write_heading("File Metadata", level=2)
        if data.file_source:
            write_item("File Source ID", data.file_source)

        if data.global_encoding:
            write_item("Global Encoding", "")
            for line in str(data.global_encoding).splitlines():
                cleaned_line = line.lstrip("- ").strip()
                canvas.setFont("Courier", 12)
                canvas.drawString(3 * cm, y, f"• {cleaned_line}")
                y -= 0.6 * cm
                check_page_space()

        if data.system_id:
            write_item("System ID", data.system_id)
        if data.gen_software:
            write_item("Generating Software", data.gen_software)
        if data.version:
            write_item("Version", data.version)

        if data.point_format:
            write_item("Point Format", "")
            for line in str(data.point_format).splitlines():
                cleaned_line = line.lstrip("- ").strip()
                canvas.setFont("Courier", 12)
                canvas.drawString(3 * cm, y, f"• {cleaned_line}")
                y -= 0.6 * cm
                check_page_space()

        if data.creation_date:
            write_item("Creation Date", data.creation_date)

    # -- Intensity --
    if data.min_intensity or data.max_intensity:
        write_heading("Intensity", level=2)
        if data.min_intensity:
            write_item("Min Intensity", data.min_intensity)
        if data.max_intensity:
            write_item("Max Intensity", data.max_intensity)

    # -- Spatial Measures --
    if (data.num_points or data.area or data.density or
        data.bounds or data.x_axis_bounds or data.y_axis_bounds):
        write_heading("Spatial Measures", level=2)
        if data.num_points:
            write_item("Number of Points", data.num_points)
        if data.area:
            write_item("Area", data.area)
        if data.density:
            write_item("Density", data.density)
        if data.bounds:
            write_item("Bounds Min", data.bounds[0])
            write_item("Bounds Max", data.bounds[1])
        if data.x_axis_bounds:
            write_item("X-Axis Bounds", data.x_axis_bounds)
        if data.y_axis_bounds:
            write_item("Y-Axis Bounds", data.y_axis_bounds)

    # -- GPS Time --
    if (data.min_time or data.max_time):
        write_heading("GPS Time", level=2)
        if data.min_time:
            write_item("Min GPS Time", data.min_time)
        if data.max_time:
            write_item("Max GPS Time", data.max_time)

    # -- Classifications --
    if data.unique_classes is not None and data.class_counts is not None:
        write_heading("Classification Counts", level=2)
        for cls, count in zip(data.unique_classes, data.class_counts):
            write_item(f"Class {cls}", count)

    # -- Returns --
    if data.unique_returns is not None and data.return_counts is not None:
        write_heading("Return Number Counts", level=2)
        for ret, count in zip(data.unique_returns, data.return_counts):
            write_item(f"Return {ret}", count)

    canvas.save()
