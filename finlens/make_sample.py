from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
S = getSampleStyleSheet()
def tbl(rows):
    t = Table([["", "Note", "2025", "2024"]] + rows, colWidths=[260, 40, 80, 80])
    t.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 9), ("ALIGN", (1,0), (-1,-1), "RIGHT"), ("LINEBELOW", (0,0), (-1,0), .5, colors.grey)]))
    return t
doc = SimpleDocTemplate("samples/northwind_annual_report.pdf", pagesize=A4)
E = [Paragraph("Northwind Textiles Limited", S["Title"]), Paragraph("Annual Report for the year ended 31 March 2025 (all amounts in millions)", S["Normal"]), Spacer(1, 14),
 Paragraph("Management discussion", S["Heading2"]),
 Paragraph("The company achieved record revenue and strong profit growth this year. Management expanded into new export markets with rising customer demand for technical fabrics. "
  "The group improved operating margins through cost efficiency and reduced debt during the period. Cash flow was higher and the board increased dividends. "
  "However, the company faces significant liquidity risk because several large customers may delay payments. The business is exposed to cotton price volatility and currency movements that could reduce margins. "
  "Management recorded an impairment charge on an older spinning plant. The company is dependent on a small number of customers who may reduce orders. "
  "The company is incorporated in India and operates through three business segments. The board held its annual general meeting during the year.", S["Normal"]),
 PageBreak(), Paragraph("Statement of profit or loss", S["Heading2"]),
 tbl([["Revenue from operations", "5", "4,812.5", "4,205.1"], ["Cost of materials and services", "6", "3,051.2", "2,764.9"], ["Gross profit", "", "1,761.3", "1,440.2"],
      ["Operating profit", "", "612.4", "498.7"], ["Net profit for the year", "", "398.6", "331.0"]]), Spacer(1, 18),
 Paragraph("Balance sheet", S["Heading2"]),
 tbl([["Total current assets", "", "1,904.0", "1,722.5"], ["Total assets", "", "4,310.8", "3,968.4"], ["Total current liabilities", "", "1,320.6", "1,184.9"],
      ["Total borrowings", "", "1,105.3", "1,240.8"], ["Total liabilities", "", "2,360.2", "2,288.7"], ["Total equity", "", "1,950.6", "1,679.7"]]), Spacer(1, 18),
 Paragraph("Cash flow statement", S["Heading2"]),
 tbl([["Net cash from operating activities", "", "455.9", "372.4"]])]
doc.build(E)
