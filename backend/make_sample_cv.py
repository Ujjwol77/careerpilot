"""Generates samples/sample_cv.docx and samples/sample_cv.pdf (a fictional data-analyst CV) for demos and tests."""
from pathlib import Path

import docx
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

LINES = [
    ("Alex Morgan", "name"),
    ("alex.morgan@example.com | 0400 000 000 | Melbourne, VIC", "plain"),
    ("Summary", "h"),
    ("Recent IT graduate with hands-on experience in reporting and data analysis, looking for a data analyst role.", "plain"),
    ("Experience", "h"),
    ("Reporting Assistant, Southern Retail Group  2023 - Present", "plain"),
    ("- Built weekly sales dashboards in Excel and Power BI used by 12 store managers", "b"),
    ("- Responsible for cleaning and preparing monthly data extracts using SQL", "b"),
    ("- Reduced manual reporting time by 6 hours per week by automating pivot tables", "b"),
    ("- Worked on customer survey analysis with the marketing team", "b"),
    ("Data Entry Clerk, Bayside Logistics  2021 - 2023", "plain"),
    ("- Maintained accurate records for 200+ shipments per week with strong attention to detail", "b"),
    ("Education", "h"),
    ("Bachelor of Information Technology, Victoria University  2018 - 2021", "plain"),
    ("Skills", "h"),
    ("SQL, Excel, Power BI, data visualisation, communication, teamwork, problem solving", "plain"),
    ("Projects", "h"),
    ("- Analysed a public housing dataset with statistics and charts, published on GitHub", "b"),
]


def main():
    out = Path(__file__).parent / "samples"
    out.mkdir(exist_ok=True)
    d = docx.Document()
    for text, kind in LINES:
        d.add_heading(text, level=1) if kind == "h" else d.add_paragraph(text)
    d.save(out / "sample_cv.docx")

    c = canvas.Canvas(str(out / "sample_cv.pdf"), pagesize=A4)
    y = 800
    for text, kind in LINES:
        c.setFont("Helvetica-Bold" if kind in {"h", "name"} else "Helvetica", 12)
        c.drawString(50, y, text)
        y -= 20
    c.save()


if __name__ == "__main__":
    main()
