from pathlib import Path
from kicad import KicadComponent

HEADER_FONT = "Helvetica-BoldOblique"
BODY_FONT = "Helvetica"
MARGIN = 40


def group_by_feeder(components: list[KicadComponent]) -> list:
    # group into (feederNo, value, footprint) -> sorted designators, ordered by feeder
    entries = {}
    for comp in components:
        key = (comp.feederNo, str(comp.val), str(comp.package))
        entries.setdefault(key, []).append(str(comp.ref))
    rows = sorted(entries.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2]))
    for _, refs in rows:
        refs.sort()
    return rows


def wrap_designators(canvas, tokens: list[str], size: int, max_width: float) -> list[str]:
    # greedily wrap a comma-separated designator list to the content width
    lines = []
    line = ""
    for token in tokens:
        piece = token if not line else ", " + token
        if canvas.stringWidth(line + piece, BODY_FONT, size) <= max_width:
            line += piece
        else:
            if line:
                lines.append(line)
            line = token
    if line:
        lines.append(line)
    return lines


def write_feeder_pdf(components: list[KicadComponent], pdf_path: Path):
    """
    Render a printable, single-page feeder-loading sheet: one entry per
    (feeder, value, footprint) with a bold header and the designators below.
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except ImportError:
        print("Error: --pdf requires reportlab. Install it with: pip install reportlab")
        exit(1)

    rows = group_by_feeder(components)
    page_w, page_h = A4
    content_w = page_w - 2 * MARGIN
    content_h = page_h - 2 * MARGIN
    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)

    # pick the largest header size (down to 6pt) whose content still fits one page
    header_size = 6
    for size in (11, 10, 9, 8, 7, 6):
        height = 0
        for _, refs in rows:
            line_count = len(wrap_designators(pdf, refs, size - 1, content_w))
            height += size * 1.35 + (size - 1) * 1.3 * line_count + size * 0.7
        if height <= content_h:
            header_size = size
            break

    body_size = header_size - 1
    header_h = header_size * 1.35
    body_h = body_size * 1.3
    gap = header_size * 0.7
    y = page_h - MARGIN
    for (feeder, value, footprint), refs in rows:
        ref_lines = wrap_designators(pdf, refs, body_size, content_w)
        if y - (header_h + body_h * len(ref_lines)) < MARGIN:  # spill to a new page
            pdf.showPage()
            y = page_h - MARGIN
        y -= header_h
        pdf.setFont(HEADER_FONT, header_size)
        pdf.drawString(MARGIN, y, f"FeederNo {feeder} | {value} | {footprint}")
        pdf.setFont(BODY_FONT, body_size)
        for line in ref_lines:
            y -= body_h
            pdf.drawString(MARGIN, y, line)
        y -= gap
    pdf.save()
