import os
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def generate_pdf_certificate(
    output_path: Path,
    recipient_name: str,
    course_title: str,
    issuer: str,
    issue_date: str,
    certificate_number: str,
    custom_text: str = None
) -> str:
    """
    Generates a professional PDF certificate using ReportLab.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Dimensions for Landscape A4
    width, height = landscape(A4)
    c = canvas.Canvas(str(output_path), pagesize=landscape(A4))
    
    # Background color
    c.setFillColor(colors.HexColor("#FAFAFC"))
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Margins & Borders
    margin = 30
    c.setStrokeColor(colors.HexColor("#1B365D")) # Deep Navy
    c.setLineWidth(4)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)
    
    inner_margin = margin + 6
    c.setStrokeColor(colors.HexColor("#D4AF37")) # Gold Accent
    c.setLineWidth(1.5)
    c.rect(inner_margin, inner_margin, width - 2 * inner_margin, height - 2 * inner_margin)
    
    # Corner Ornaments (Gold Triangles/Lines)
    corner_size = 20
    # Top Left
    c.line(inner_margin, height - inner_margin - corner_size, inner_margin + corner_size, height - inner_margin)
    # Top Right
    c.line(width - inner_margin - corner_size, height - inner_margin, width - inner_margin, height - inner_margin - corner_size)
    # Bottom Left
    c.line(inner_margin, inner_margin + corner_size, inner_margin + corner_size, inner_margin)
    # Bottom Right
    c.line(width - inner_margin - corner_size, inner_margin, width - inner_margin, inner_margin + corner_size)

    # 1. Issuer Name Header
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#D4AF37"))
    c.drawCentredString(width / 2.0, height - 80, issuer.upper())
    
    # Decorative line under issuer
    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor("#D4AF37"))
    c.line(width / 2.0 - 100, height - 90, width / 2.0 + 100, height - 90)

    # 2. Main Title
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(colors.HexColor("#1B365D"))
    c.drawCentredString(width / 2.0, height - 140, "CERTIFICATE OF ACHIEVEMENT")

    # 3. Subtitle / Presentation text
    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(colors.HexColor("#5A6B7C"))
    c.drawCentredString(width / 2.0, height - 180, "PROUDLY PRESENTED TO")

    # 4. Recipient Name
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(colors.HexColor("#1B365D"))
    c.drawCentredString(width / 2.0, height - 230, recipient_name)

    # Underline for recipient name
    name_width = c.stringWidth(recipient_name, "Helvetica-Bold", 28)
    underline_width = max(name_width + 40, 260)
    c.setLineWidth(1.5)
    c.setStrokeColor(colors.HexColor("#D4AF37"))
    c.line(width / 2.0 - underline_width / 2.0, height - 242, width / 2.0 + underline_width / 2.0, height - 242)

    # 5. Course Completion Text
    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#5A6B7C"))
    c.drawCentredString(width / 2.0, height - 280, "for successfully completing the program")

    # 6. Course Title
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#1B365D"))
    c.drawCentredString(width / 2.0, height - 315, course_title)

    # 7. Optional Custom Text (e.g. Grade / Distinction)
    if custom_text:
        c.setFont("Helvetica-BoldOblique", 12)
        c.setFillColor(colors.HexColor("#D4AF37"))
        c.drawCentredString(width / 2.0, height - 345, f"[{custom_text}]")

    # 8. Footer Section (Left: Credentials, Center: Badge, Right: Signature)
    footer_y = 100
    
    # Left Block: Issue Date & Credential ID
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#2C3E50"))
    c.drawString(inner_margin + 40, footer_y + 20, f"Date of Issue: {issue_date}")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1B365D"))
    c.drawString(inner_margin + 40, footer_y, f"Certificate ID: {certificate_number}")
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.HexColor("#BDC3C7"))
    c.line(inner_margin + 40, footer_y + 35, inner_margin + 200, footer_y + 35)

    # Center Block: Official Gold Seal Graphic
    badge_x = width / 2.0
    badge_y = footer_y + 15
    c.setFillColor(colors.HexColor("#D4AF37"))
    c.setStrokeColor(colors.HexColor("#B8860B"))
    c.setLineWidth(1)
    c.circle(badge_x, badge_y, 30, fill=True, stroke=True)
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.circle(badge_x, badge_y, 25, fill=True, stroke=False)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#1B365D"))
    c.drawCentredString(badge_x, badge_y + 4, "OFFICIAL")
    c.drawCentredString(badge_x, badge_y - 6, "VERIFIED")

    # Right Block: Signature line
    sig_x = width - inner_margin - 200
    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor("#1B365D"))
    c.line(sig_x, footer_y + 35, sig_x + 160, footer_y + 35)
    
    c.setFont("Helvetica-BoldOblique", 14)
    c.setFillColor(colors.HexColor("#1B365D"))
    c.drawString(sig_x + 30, footer_y + 42, issuer) # Simulated signature
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#2C3E50"))
    c.drawString(sig_x + 20, footer_y + 18, "AUTHORIZED SIGNATURE")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#7F8C8D"))
    c.drawString(sig_x + 20, footer_y, issuer)

    # Save PDF
    c.showPage()
    c.save()
    
    return str(output_path)
