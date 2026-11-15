from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from tallerweb import identity



def budget_pdf(budget):
    """Render a budget snapshot suitable for storage and later delivery."""
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", parent=styles["Title"], alignment=TA_CENTER))
    story = [
        Paragraph(escape(identity.NAME), styles["Heading2"]),
        Paragraph(f"{escape(identity.ADDRESS)} · Tel. {escape(identity.PHONE)}", styles["Normal"]),
        Spacer(1, 8*mm),
        Paragraph("PRESUPUESTO — NO ES FACTURA", styles["CenterTitle"]),
        Paragraph(
            f"Número: {escape(str(budget.number))}　　Fecha: {budget.created_at:%d/%m/%Y}",
            styles["Normal"],
        ),
        Spacer(1, 5*mm),
        Paragraph(
            f"Cliente: {escape(budget.vehicle.customer_name)} "
            f"({escape(budget.vehicle.get_customer_type_display())})",
            styles["Normal"],
        ),
        Paragraph(
            f"Vehículo: {escape(budget.vehicle.plate)} · {escape(budget.vehicle.make)} "
            f"{escape(budget.vehicle.model)}",
            styles["Normal"],
        ),
        Spacer(1, 5*mm),
        Paragraph(f"Trabajo: {escape(budget.description)}", styles["Normal"]),
        Spacer(1, 4*mm),
    ]
    data = [["Repuesto", "Cantidad", "Precio unitario", "Importe"]]
    for item in budget.items.all():
        data.append([Paragraph(escape(item.description), styles["Normal"]), str(item.quantity),
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
