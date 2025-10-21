"""SQLAlchemy database models"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")


class Invoice(Base):
    """Invoice model - main entity"""
    __tablename__ = "invoices"
    
    # Primary
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Dates (§14 UStG)
    issue_date = Column(DateTime, nullable=False, index=True)
    delivery_date_start = Column(DateTime)
    delivery_date_end = Column(DateTime)
    
    # Seller (leistender Unternehmer) - §14 UStG
    seller_name = Column(String(255), nullable=False)
    seller_street = Column(String(255), nullable=False)
    seller_zip = Column(String(20), nullable=False)
    seller_city = Column(String(100), nullable=False)
    seller_country = Column(String(2), nullable=False, default="DE")
    seller_tax_id = Column(String(50), nullable=False)  # USt-IdNr oder Steuernummer
    seller_email = Column(String(255))
    seller_phone = Column(String(50))
    
    # Buyer (Leistungsempfänger) - §14 UStG
    buyer_name = Column(String(255), nullable=False)
    buyer_street = Column(String(255), nullable=False)
    buyer_zip = Column(String(20), nullable=False)
    buyer_city = Column(String(100), nullable=False)
    buyer_country = Column(String(2), nullable=False, default="DE")
    buyer_tax_id = Column(String(50))  # Optional für B2C
    buyer_email = Column(String(255))
    buyer_phone = Column(String(50))
    
    # Totals (§14 UStG)
    currency = Column(String(3), nullable=False, default="EUR")
    net_total = Column(Float, nullable=False)
    tax_total = Column(Float, nullable=False)
    gross_total = Column(Float, nullable=False)
    
    # Tax information
    tax_exempt = Column(Boolean, default=False)
    tax_exempt_reason = Column(String(255))  # Hinweis auf Steuerbefreiung
    
    # Notes
    notes = Column(Text)
    payment_terms = Column(String(255))
    
    # Files & Integrity (GoBD)
    zugferd_xml_path = Column(String(500))
    pdfa3_path = Column(String(500), nullable=False)
    pdf_hash = Column(String(64), nullable=False)  # SHA-256
    tsa_token = Column(JSON)  # RFC3161 Timestamp Token
    signature_info = Column(JSON)  # PAdES signature metadata
    
    # Status & Versioning
    status = Column(String(20), nullable=False, default="draft")  # draft, issued, cancelled
    version = Column(Integer, nullable=False, default=1)
    is_immutable = Column(Boolean, default=False)  # Nach Erstellung: True
    
    # Audit
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_invoice_date", "issue_date"),
        Index("idx_invoice_buyer", "buyer_name", "buyer_tax_id"),
        Index("idx_invoice_status", "status"),
    )


class InvoiceLineItem(Base):
    """Invoice line items (Rechnungspositionen) - §14 UStG"""
    __tablename__ = "invoice_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Line item details (§14 UStG: Menge, Art, Leistungszeitraum)
    position = Column(Integer, nullable=False)  # Positionsnummer
    description = Column(Text, nullable=False)  # Art der Leistung
    quantity = Column(Float, nullable=False)  # Menge
    unit = Column(String(20), nullable=False, default="Stück")  # Einheit
    unit_price = Column(Float, nullable=False)  # Preis pro Einheit
    line_net = Column(Float, nullable=False)  # Netto-Zeilenbetrag
    tax_rate = Column(Float, nullable=False)  # MwSt-Satz (z.B. 19.0)
    tax_amount = Column(Float, nullable=False)  # Steuerbetrag
    line_gross = Column(Float, nullable=False)  # Brutto-Zeilenbetrag
    
    # Relationship
    invoice = relationship("Invoice", back_populates="line_items")
    
    __table_args__ = (
        UniqueConstraint("invoice_id", "position", name="uq_invoice_position"),
    )


class AuditLog(Base):
    """Audit log for all actions (GoBD Nachvollziehbarkeit)"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    entity_type = Column(String(50), nullable=False)  # "invoice", "user", etc.
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # "create", "read", "update", "delete"
    details = Column(JSON)  # Additional details
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_timestamp", "timestamp"),
    )


class InvoiceNumberSequence(Base):
    """Sequence table for generating invoice numbers (lückenlos, fortlaufend)"""
    __tablename__ = "invoice_number_sequence"
    
    id = Column(Integer, primary_key=True)
    prefix = Column(String(10), nullable=False, unique=True)  # z.B. "RE"
    current_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Contact(Base):
    """Contact model for storing customer/supplier information"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Contact type
    contact_type = Column(String(20), nullable=False, default="customer")  # customer, supplier, both
    
    # Company/Person info
    company_name = Column(String(255))
    contact_person = Column(String(255))
    
    # Address (§14 UStG)
    street = Column(String(255), nullable=False)
    zip_code = Column(String(20), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(2), nullable=False, default="DE")
    
    # Tax information
    tax_id = Column(String(50))  # USt-IdNr oder Steuernummer
    
    # Contact details
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    
    # Additional info
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    creator = relationship("User")
    
    __table_args__ = (
        Index("idx_contact_type", "contact_type"),
        Index("idx_contact_name", "company_name"),
        Index("idx_contact_active", "is_active"),
    )
