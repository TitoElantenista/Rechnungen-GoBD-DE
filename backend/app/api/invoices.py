"""Invoice API endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import extract, or_

from app.core import get_db
from app.models import Invoice as InvoiceModel, InvoiceLineItem
from app.schemas import Invoice, InvoiceCreate, InvoiceList, InvoiceFilter
from app.services.invoice_service import InvoiceService
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=Invoice, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new invoice with PDF/A-3 + ZUGFeRD XML + TSA signature
    
    This endpoint:
    1. Validates all §14 UStG mandatory fields
    2. Generates unique, sequential invoice number
    3. Creates ZUGFeRD XML (EN-16931)
    4. Generates PDF/A-3 with embedded XML
    5. Signs PDF with PAdES + RFC3161 timestamp
    6. Stores in S3 with object lock
    7. Saves metadata to database (immutable)
    """
    service = InvoiceService(db)
    
    try:
        invoice = await service.create_invoice(invoice_data, current_user.id)
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.get("", response_model=List[InvoiceList])
async def list_invoices(
    year: int = Query(None, description="Filter by year"),
    q: str = Query(None, description="Search in invoice number, buyer name, tax ID"),
    status_filter: str = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List invoices with filtering and pagination
    
    Query parameters:
    - year: Filter by issue year
    - q: Free text search (invoice number, buyer name, tax ID)
    - status: Filter by status (draft, issued, cancelled)
    - page: Page number (starting from 1)
    - limit: Items per page (1-100)
    """
    query = db.query(InvoiceModel)
    
    # Filter by year
    if year:
        query = query.filter(extract('year', InvoiceModel.issue_date) == year)
    
    # Filter by status
    if status_filter:
        query = query.filter(InvoiceModel.status == status_filter)
    
    # Search
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                InvoiceModel.invoice_number.ilike(search_term),
                InvoiceModel.buyer_name.ilike(search_term),
                InvoiceModel.buyer_tax_id.ilike(search_term)
            )
        )
    
    # Pagination
    total = query.count()
    invoices = query.order_by(InvoiceModel.issue_date.desc())\
                    .offset((page - 1) * limit)\
                    .limit(limit)\
                    .all()
    
    return invoices


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get invoice details by ID"""
    invoice = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    
    return invoice


@router.get("/{invoice_id}/preview")
async def preview_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Stream PDF for preview (readonly)
    
    Returns PDF/A-3 file as binary stream
    """
    invoice = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    
    service = InvoiceService(db)
    
    try:
        pdf_stream = await service.get_pdf_stream(invoice)
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={invoice.invoice_number}.pdf",
                "Cache-Control": "no-cache",
            }
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found in storage"
        )


@router.get("/{invoice_id}/download")
async def download_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Download invoice archive (ZIP with PDF + XML + TSA + Metadata)
    
    Returns a ZIP file containing:
    - PDF/A-3 file
    - ZUGFeRD XML file
    - TSA token JSON
    - Metadata JSON (invoice details)
    """
    invoice = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    
    service = InvoiceService(db)
    
    try:
        zip_path = await service.create_download_package(invoice)
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{invoice.invoice_number}_archive.zip",
            headers={"Content-Disposition": f"attachment; filename={invoice.invoice_number}_archive.zip"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create download package: {str(e)}"
        )


@router.delete("/{invoice_id}")
async def cancel_invoice(
    invoice_id: int,
    reason: str = Query(..., description="Reason for cancellation"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cancel an invoice (creates Stornobeleg)
    
    Note: Invoices cannot be deleted due to GoBD requirements.
    This endpoint marks the invoice as cancelled and creates a cancellation document.
    """
    invoice = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    
    if invoice.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice is already cancelled"
        )
    
    service = InvoiceService(db)
    
    try:
        cancelled_invoice = await service.cancel_invoice(invoice, reason, current_user.id)
        return {
            "message": "Invoice cancelled successfully",
            "invoice_id": invoice_id,
            "status": cancelled_invoice.status,
            "cancellation_reason": reason
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel invoice: {str(e)}"
        )
