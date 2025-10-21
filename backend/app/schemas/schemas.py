"""Pydantic schemas for request/response validation"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Invoice Line Item Schemas
# ============================================================================

class LineItemBase(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit: str = Field(default="Stück", max_length=20)
    unit_price: float = Field(..., ge=0)
    tax_rate: float = Field(..., ge=0, le=100)


class LineItemCreate(LineItemBase):
    # position se genera automáticamente en el backend
    pass


class LineItem(LineItemBase):
    id: int
    position: int
    line_net: float
    tax_amount: float
    line_gross: float
    
    class Config:
        from_attributes = True


# ============================================================================
# Party (Seller/Buyer) Schemas
# ============================================================================

class PartyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    street: str = Field(..., min_length=1, max_length=255)
    zip: str = Field(..., min_length=1, max_length=20)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(default="DE", min_length=2, max_length=2)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class Seller(PartyBase):
    tax_id: str = Field(..., min_length=1, max_length=50)  # Pflicht für Verkäufer


class Buyer(PartyBase):
    tax_id: Optional[str] = Field(None, max_length=50)  # Optional für B2C


# ============================================================================
# Invoice Schemas
# ============================================================================

class InvoiceBase(BaseModel):
    issue_date: datetime
    delivery_date_start: Optional[datetime] = None
    delivery_date_end: Optional[datetime] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    tax_exempt: bool = False
    tax_exempt_reason: Optional[str] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = Field(default="Zahlbar innerhalb von 14 Tagen")


class InvoiceCreate(InvoiceBase):
    seller: Seller
    buyer: Buyer
    line_items: List[LineItemCreate] = Field(..., min_items=1)


class InvoiceUpdate(BaseModel):
    """Only draft invoices can be updated (before issuance)"""
    notes: Optional[str] = None
    payment_terms: Optional[str] = None


class Invoice(InvoiceBase):
    id: int
    invoice_number: str
    
    # Seller
    seller_name: str
    seller_street: str
    seller_zip: str
    seller_city: str
    seller_country: str
    seller_tax_id: str
    seller_email: Optional[str]
    seller_phone: Optional[str]
    
    # Buyer
    buyer_name: str
    buyer_street: str
    buyer_zip: str
    buyer_city: str
    buyer_country: str
    buyer_tax_id: Optional[str]
    buyer_email: Optional[str]
    buyer_phone: Optional[str]
    
    # Totals
    net_total: float
    tax_total: float
    gross_total: float
    
    # Files
    pdfa3_path: str
    zugferd_xml_path: Optional[str]
    pdf_hash: str
    
    # Status
    status: str
    version: int
    is_immutable: bool
    
    # Audit
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    line_items: List[LineItem] = []
    
    class Config:
        from_attributes = True


class InvoiceList(BaseModel):
    """Simplified schema for list view"""
    id: int
    invoice_number: str
    issue_date: datetime
    buyer_name: str
    buyer_city: str
    gross_total: float
    currency: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Filter & Search Schemas
# ============================================================================

class InvoiceFilter(BaseModel):
    year: Optional[int] = None
    q: Optional[str] = None  # Search in number, buyer name, tax_id
    status: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)


# ============================================================================
# Authentication Schemas
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ============================================================================
# Contact Schemas
# ============================================================================

class ContactBase(BaseModel):
    contact_type: str = Field(default="customer", pattern="^(customer|supplier|both)$")
    company_name: Optional[str] = Field(None, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    street: str = Field(..., min_length=1, max_length=255)
    zip_code: str = Field(..., min_length=1, max_length=20)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(default="DE", min_length=2, max_length=2)
    tax_id: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    is_active: bool = True


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    contact_type: Optional[str] = Field(None, pattern="^(customer|supplier|both)$")
    company_name: Optional[str] = Field(None, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    street: Optional[str] = Field(None, max_length=255)
    zip_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    tax_id: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class Contact(ContactBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContactList(BaseModel):
    """Simplified schema for list view"""
    id: int
    contact_type: str
    company_name: Optional[str]
    contact_person: Optional[str]
    city: str
    email: Optional[str]
    phone: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True
