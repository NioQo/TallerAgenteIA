from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class DemoLogo(Flowable):
    """Small vector wordmark; explicitly fictional until workshop details arrive."""
    def __init__(self):
        super().__init__()
        self.width, self.height = 25*mm, 17*mm

    def draw(self):
        self.canv.setFillColor(colors.HexColor("#243b53"))
        self.canv.roundRect(0, 0, self.width, self.height, 3*mm, fill=1, stroke=0)
        self.canv.setFillColor(colors.white)
        self.canv.setFont("Helvetica-Bold", 17)
        self.canv.drawCentredString(self.width/2, 5*mm, "TD")


def budget_pdf(budget):
    """Render a budget snapshot suitable for storage and later delivery."""
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", parent=styles["Title"], alignment=TA_CENTER))
    story = [DemoLogo(), Paragraph("TALLER DEMO · Servicio Automotor", styles["Heading2"]),
             Paragraph("Av. del Taller 123 · Buenos Aires · Tel. (011) 4000-0000", styles["Normal"]),
             Spacer(1, 8*mm), Paragraph("PRESUPUESTO — NO ES FACTURA", styles["CenterTitle"]),
             Paragraph(f"Número: {budget.number}　　Fecha: {budget.created_at:%d/%m/%Y}", styles["Normal"]),
             Spacer(1, 5*mm),
             Paragraph(f"Cliente: {budget.vehicle.customer_name} ({budget.vehicle.get_customer_type_display()})", styles["Normal"]),
             Paragraph(f"Vehículo: {budget.vehicle.plate} · {budget.vehicle.make} {budget.vehicle.model}", styles["Normal"]),
             Spacer(1, 5*mm), Paragraph(f"Trabajo: {budget.description}", styles["Normal"]), Spacer(1, 4*mm)]
    data = [["Repuesto", "Cantidad", "Precio unitario", "Importe"]]
    for item in budget.items.all():
        data.append([Paragraph(item.description, styles["Normal"]), str(item.quantity),
                     f"ARS {item.unit_price:,.2f}", f"ARS {item.subtotal:,.2f}"])
    data.extend([["Mano de obra", "", "", f"ARS {budget.labor_amount:,.2f}"],
                 ["TOTAL ARS", "", "", f"ARS {budget.total:,.2f}"]])
    table = Table(data, colWidths=[78*mm, 22*mm, 37*mm, 37*mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243b53")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .4, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8eef4")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(table)
    doc.build(story)
    return output.getvalue()
