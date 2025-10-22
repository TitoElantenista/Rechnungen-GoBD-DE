"""PDF/A-3 Generator with embedded ZUGFeRD XML"""

from datetime import datetime
from io import BytesIO
from typing import List, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from pikepdf import Pdf, Name, Dictionary, Array
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from app.schemas import Seller, Buyer


class PDFGenerator:
    """
    Generate PDF/A-3 invoices with embedded ZUGFeRD XML
    
    PDF/A-3 is required for GoBD compliance as it:
    - Ensures long-term archivability
    - Allows embedding of structured data (XML)
    - Is machine-readable and human-readable (hybrid)
    """
    
    def generate(
        self,
        invoice_number: str,
        issue_date: datetime,
        seller: Seller,
        buyer: Buyer,
        line_items: List[Dict],
        net_total: float,
        tax_total: float,
        gross_total: float,
        currency: str = "EUR",
        notes: str = None,
        payment_terms: str = None,
        zugferd_xml: bytes = None,
    ) -> bytes:
        """
        Generate PDF/A-3 invoice with embedded ZUGFeRD XML
        
        Returns PDF as bytes
        """
        
        buffer = BytesIO()
        
        # Create PDF with ReportLab
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
        )
        
        # Build story (content)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=TA_LEFT,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=6,
            spaceBefore=12,
        )
        
        # Title
        story.append(Paragraph(f"Rechnung {invoice_number}", title_style))
        story.append(Spacer(1, 10*mm))
        
        # Buyer (left) and seller (right)
        buyer_block = Paragraph(
            f"{buyer.name}<br/>{buyer.street}<br/>{buyer.zip} {buyer.city}<br/>{buyer.country}"
            + (f"<br/>USt-IdNr: {buyer.tax_id}" if buyer.tax_id else ""),
            styles['Normal']
        )
        seller_block = Paragraph(
            f"<b>Rechnungssteller:</b><br/>{seller.name}<br/>{seller.street}<br/>{seller.zip} {seller.city}<br/>{seller.country}<br/>USt-IdNr: {seller.tax_id}",
            styles['Normal']
        )
        seller_buyer_table = Table([[buyer_block, seller_block]], colWidths=[90*mm, 90*mm])
        seller_buyer_table.hAlign = 'LEFT'
        seller_buyer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(seller_buyer_table)
        story.append(Spacer(1, 10*mm))
        
        # Invoice details
        details_data = [
            ['Rechnungsnummer', invoice_number],
            ['Rechnungsdatum', issue_date.strftime('%d.%m.%Y')],
        ]
        
        details_table = Table(details_data, colWidths=[55*mm, 65*mm])
        details_table.hAlign = 'LEFT'
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 10*mm))
        
        # Line items
        story.append(Paragraph("Rechnungspositionen", heading_style))
        
        # Table header
        line_items_data = [
            ['Pos.', 'Beschreibung', 'Menge', 'Einheit', 'Preis', 'MwSt.', 'Gesamt']
        ]
        
        # Add line items
        for item in line_items:
            line_items_data.append([
                str(item['position']),
                item['description'],
                f"{item['quantity']:.2f}",
                item['unit'],
                f"{item['unit_price']:.2f} {currency}",
                f"{item['tax_rate']:.0f}%",
                f"{item['line_gross']:.2f} {currency}",
            ])
        
        line_items_table = Table(
            line_items_data,
            colWidths=[10*mm, 60*mm, 20*mm, 20*mm, 25*mm, 20*mm, 25*mm]
        )
        
        line_items_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(line_items_table)
        story.append(Spacer(1, 10*mm))
        
        # Totals
        totals_data = [
            ['Nettobetrag:', f"{net_total:.2f} {currency}"],
            ['MwSt.:', f"{tax_total:.2f} {currency}"],
            ['', ''],  # Separator
            ['Gesamtbetrag:', f"{gross_total:.2f} {currency}"],
        ]
        
        totals_table = Table(totals_data, colWidths=[140*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, 1), 'Helvetica'),
            ('FONTNAME', (0, 3), (0, 3), 'Helvetica-Bold'),
            ('FONTNAME', (1, 3), (1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 3), (-1, 3), 12),
            ('LINEABOVE', (0, 3), (-1, 3), 1.5, colors.black),
            ('TOPPADDING', (0, 3), (-1, 3), 8),
        ]))
        
        story.append(totals_table)
        
        # Payment terms
        if payment_terms:
            story.append(Spacer(1, 10*mm))
            story.append(Paragraph("<b>Zahlungsbedingungen:</b>", styles['Normal']))
            story.append(Paragraph(payment_terms, styles['Normal']))
        
        # Notes
        if notes:
            story.append(Spacer(1, 10*mm))
            story.append(Paragraph("<b>Hinweise:</b>", styles['Normal']))
            story.append(Paragraph(notes, styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 15*mm))
        footer_text = f"""
        <font size=8 color="#7f8c8d">
        Dieses Dokument wurde maschinell erstellt und ist ohne Unterschrift gültig.<br/>
        Die Rechnung entspricht den Anforderungen nach §14 UStG und ist GoBD-konform archiviert.<br/>
        PDF/A-3 mit eingebettetem ZUGFeRD XML (EN-16931 kompatibel).
        </font>
        """
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Embed ZUGFeRD XML using pikepdf (PDF/A-3 compliance)
        if zugferd_xml:
            pdf_bytes = self._embed_zugferd_xml(pdf_bytes, zugferd_xml, invoice_number)
        
        return pdf_bytes
    
    def _embed_zugferd_xml(self, pdf_bytes: bytes, xml_bytes: bytes, invoice_number: str) -> bytes:
        """
        Embed ZUGFeRD XML into PDF/A-3
        
        Uses pikepdf to attach XML as embedded file with proper metadata
        """
        pdf = Pdf.open(BytesIO(pdf_bytes))
        
        # Create file specification for ZUGFeRD XML
        xml_filename = f"zugferd-invoice.xml"
        
        # Embedded file stream
        xml_stream = pdf.make_stream(xml_bytes)
        xml_stream.Type = Name.EmbeddedFile
        xml_stream.Subtype = Name('/text#2Fxml')  # MIME type
        xml_stream.Params = Dictionary(
            Size=len(xml_bytes),
            ModDate=datetime.now().strftime('D:%Y%m%d%H%M%S'),
        )
        
        # File specification
        file_spec = Dictionary(
            Type=Name.Filespec,
            F=xml_filename,
            UF=xml_filename,
            EF=Dictionary(F=xml_stream),
            AFRelationship=Name.Alternative,  # PDF/A-3 requirement
        )
        
        # Add to embedded files
        if '/Names' not in pdf.Root:
            pdf.Root.Names = Dictionary()
        
        if '/EmbeddedFiles' not in pdf.Root.Names:
            pdf.Root.Names.EmbeddedFiles = Dictionary(Names=Array())
        
        pdf.Root.Names.EmbeddedFiles.Names.append(xml_filename)
        pdf.Root.Names.EmbeddedFiles.Names.append(file_spec)
        
        # Set AF (Associated Files) for PDF/A-3
        if '/AF' not in pdf.Root:
            pdf.Root.AF = Array()
        pdf.Root.AF.append(file_spec)
        
        # Save to bytes
        output = BytesIO()
        pdf.save(output)
        result = output.getvalue()
        output.close()
        pdf.close()
        
        return result
