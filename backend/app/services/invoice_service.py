"""Invoice service - main business logic"""

import hashlib
import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from zipfile import ZipFile
from functools import lru_cache

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Invoice, InvoiceLineItem, InvoiceNumberSequence, AuditLog
from app.schemas import InvoiceCreate
from app.core.config import settings
from app.services.zugferd_generator import ZUGFeRDGenerator
from app.services.pdf_generator import PDFGenerator
from app.services.signature_service import SignatureService
from app.services.storage_service import StorageService


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    """Return a shared storage service instance (avoids repeated S3 handshakes)."""
    return StorageService()


class InvoiceService:
    """Service for invoice operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.zugferd_gen = ZUGFeRDGenerator()
        self.pdf_gen = PDFGenerator()
        self.signature_service = SignatureService()
        self.storage_service = get_storage_service()
    
    async def create_invoice(self, invoice_data: InvoiceCreate, user_id: int) -> Invoice:
        """
        Create a new invoice with all GoBD requirements
        
        Steps:
        1. Generate unique invoice number
        2. Calculate totals
        3. Generate ZUGFeRD XML
        4. Generate PDF/A-3 with embedded XML
        5. Sign PDF with PAdES + RFC3161 timestamp
        6. Store in S3
        7. Save to database (immutable)
        8. Create audit log
        """
        
        # 1. Generate invoice number (sequential, immutable)
        invoice_number = await self._generate_invoice_number()
        
        # 2. Calculate totals
        line_items_data = []
        net_total = 0.0
        tax_total = 0.0
        
        for idx, item in enumerate(invoice_data.line_items, start=1):
            line_net = round(item.quantity * item.unit_price, 2)
            tax_amount = round(line_net * item.tax_rate / 100, 2)
            line_gross = round(line_net + tax_amount, 2)
            
            line_items_data.append({
                "position": idx,
                "description": item.description,
                "quantity": item.quantity,
                "unit": item.unit,
                "unit_price": item.unit_price,
                "line_net": line_net,
                "tax_rate": item.tax_rate,
                "tax_amount": tax_amount,
                "line_gross": line_gross,
            })
            
            net_total += line_net
            tax_total += tax_amount
        
        gross_total = round(net_total + tax_total, 2)
        
        # 3. Generate ZUGFeRD XML
        zugferd_xml = self.zugferd_gen.generate(
            invoice_number=invoice_number,
            issue_date=invoice_data.issue_date,
            seller=invoice_data.seller,
            buyer=invoice_data.buyer,
            line_items=line_items_data,
            net_total=net_total,
            tax_total=tax_total,
            gross_total=gross_total,
            currency=invoice_data.currency,
        )
        
        # 4. Generate PDF/A-3
        pdf_bytes = self.pdf_gen.generate(
            invoice_number=invoice_number,
            issue_date=invoice_data.issue_date,
            seller=invoice_data.seller,
            buyer=invoice_data.buyer,
            line_items=line_items_data,
            net_total=net_total,
            tax_total=tax_total,
            gross_total=gross_total,
            currency=invoice_data.currency,
            notes=invoice_data.notes,
            payment_terms=invoice_data.payment_terms,
            zugferd_xml=zugferd_xml,
        )
        
        # 5. Sign PDF with PAdES + RFC3161 timestamp
        signed_pdf_bytes, tsa_token = await self.signature_service.sign_pdf(pdf_bytes)
        
        # 6. Calculate hash
        pdf_hash = hashlib.sha256(signed_pdf_bytes).hexdigest()
        
        # 7. Store in S3
        pdf_path = await self.storage_service.store_pdf(
            invoice_number, signed_pdf_bytes
        )
        xml_path = await self.storage_service.store_xml(
            invoice_number, zugferd_xml
        )
        
        # 8. Create database record
        db_invoice = Invoice(
            invoice_number=invoice_number,
            issue_date=invoice_data.issue_date,
            delivery_date_start=invoice_data.delivery_date_start,
            delivery_date_end=invoice_data.delivery_date_end,
            
            # Seller
            seller_name=invoice_data.seller.name,
            seller_street=invoice_data.seller.street,
            seller_zip=invoice_data.seller.zip,
            seller_city=invoice_data.seller.city,
            seller_country=invoice_data.seller.country,
            seller_tax_id=invoice_data.seller.tax_id,
            seller_email=invoice_data.seller.email,
            seller_phone=invoice_data.seller.phone,
            
            # Buyer
            buyer_name=invoice_data.buyer.name,
            buyer_street=invoice_data.buyer.street,
            buyer_zip=invoice_data.buyer.zip,
            buyer_city=invoice_data.buyer.city,
            buyer_country=invoice_data.buyer.country,
            buyer_tax_id=invoice_data.buyer.tax_id,
            buyer_email=invoice_data.buyer.email,
            buyer_phone=invoice_data.buyer.phone,
            
            # Totals
            currency=invoice_data.currency,
            net_total=net_total,
            tax_total=tax_total,
            gross_total=gross_total,
            
            # Tax
            tax_exempt=invoice_data.tax_exempt,
            tax_exempt_reason=invoice_data.tax_exempt_reason,
            
            # Notes
            notes=invoice_data.notes,
            payment_terms=invoice_data.payment_terms,
            
            # Files
            pdfa3_path=pdf_path,
            zugferd_xml_path=xml_path,
            pdf_hash=pdf_hash,
            tsa_token=tsa_token,
            
            # Status
            status="issued",
            is_immutable=True,
            
            # Audit
            created_by=user_id,
        )
        
        self.db.add(db_invoice)
        self.db.flush()
        
        # 9. Add line items
        for item_data in line_items_data:
            line_item = InvoiceLineItem(
                invoice_id=db_invoice.id,
                **item_data
            )
            self.db.add(line_item)
        
        # 10. Create audit log
        audit_log = AuditLog(
            user_id=user_id,
            entity_type="invoice",
            entity_id=db_invoice.id,
            action="create",
            details={
                "invoice_number": invoice_number,
                "gross_total": gross_total,
                "buyer": invoice_data.buyer.name,
            }
        )
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(db_invoice)
        
        return db_invoice
    
    async def _generate_invoice_number(self) -> str:
        """
        Generate sequential, unique invoice number
        Uses database transaction to ensure no gaps
        """
        prefix = settings.INVOICE_NUMBER_PREFIX
        
        # Get or create sequence
        sequence = self.db.query(InvoiceNumberSequence)\
            .filter(InvoiceNumberSequence.prefix == prefix)\
            .with_for_update()\
            .first()
        
        if not sequence:
            sequence = InvoiceNumberSequence(
                prefix=prefix,
                current_number=settings.INVOICE_NUMBER_START
            )
            self.db.add(sequence)
            self.db.flush()
        
        # Increment
        invoice_number = f"{prefix}{sequence.current_number:06d}"
        sequence.current_number += 1
        
        self.db.commit()
        
        return invoice_number
    
    async def get_pdf_stream(self, invoice: Invoice) -> BinaryIO:
        """Get PDF as binary stream for preview"""
        return await self.storage_service.get_pdf_stream(invoice.pdfa3_path)
    
    async def create_download_package(self, invoice: Invoice) -> Path:
        """
        Create ZIP package with PDF + XML + TSA + Metadata
        """
        temp_zip = Path(f"/tmp/{invoice.invoice_number}_archive.zip")
        
        # Get files from storage
        pdf_bytes = await self.storage_service.get_file(invoice.pdfa3_path)
        xml_bytes = await self.storage_service.get_file(invoice.zugferd_xml_path)
        
        # Create metadata JSON
        metadata = {
            "invoice_number": invoice.invoice_number,
            "issue_date": invoice.issue_date.isoformat(),
            "buyer": invoice.buyer_name,
            "gross_total": invoice.gross_total,
            "currency": invoice.currency,
            "pdf_hash": invoice.pdf_hash,
            "created_at": invoice.created_at.isoformat(),
            "status": invoice.status,
        }
        
        # Create ZIP
        with ZipFile(temp_zip, 'w') as zipf:
            zipf.writestr(f"{invoice.invoice_number}.pdf", pdf_bytes)
            zipf.writestr(f"{invoice.invoice_number}.xml", xml_bytes)
            zipf.writestr("tsa_token.json", json.dumps(invoice.tsa_token, indent=2))
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        return temp_zip
    
    async def cancel_invoice(self, invoice: Invoice, reason: str, user_id: int) -> Invoice:
        """
        Cancel invoice (mark as cancelled, create audit log)
        Note: Invoice file remains in storage (GoBD requirement)
        """
        invoice.status = "cancelled"
        
        # Create audit log
        audit_log = AuditLog(
            user_id=user_id,
            entity_type="invoice",
            entity_id=invoice.id,
            action="cancel",
            details={
                "invoice_number": invoice.invoice_number,
                "reason": reason,
            }
        )
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(invoice)
        
        return invoice
