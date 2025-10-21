"""Contact API endpoints"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core import get_db
from app.models import Contact as ContactModel
from app.schemas import Contact, ContactCreate, ContactUpdate, ContactList
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new contact (customer or supplier)
    
    This endpoint creates a new contact that can be used when creating invoices.
    """
    # Create contact
    db_contact = ContactModel(
        **contact_data.model_dump(),
        created_by=current_user.id
    )
    
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    
    return db_contact


@router.get("", response_model=List[ContactList])
async def list_contacts(
    contact_type: Optional[str] = Query(None, description="Filter by type: customer, supplier, both"),
    q: str = Query(None, description="Search in name, company, email"),
    active_only: bool = Query(True, description="Show only active contacts"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all contacts with filtering and pagination
    """
    query = db.query(ContactModel)
    
    # Filter by active status
    if active_only:
        query = query.filter(ContactModel.is_active == True)
    
    # Filter by contact type
    if contact_type:
        query = query.filter(ContactModel.contact_type == contact_type)
    
    # Search
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                ContactModel.company_name.ilike(search_term),
                ContactModel.contact_person.ilike(search_term),
                ContactModel.email.ilike(search_term),
                ContactModel.tax_id.ilike(search_term)
            )
        )
    
    # Pagination
    offset = (page - 1) * limit
    contacts = query.order_by(ContactModel.company_name, ContactModel.contact_person)\
                    .offset(offset)\
                    .limit(limit)\
                    .all()
    
    return contacts


@router.get("/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a specific contact by ID
    """
    contact = db.query(ContactModel).filter(ContactModel.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    return contact


@router.put("/{contact_id}", response_model=Contact)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update a contact
    """
    contact = db.query(ContactModel).filter(ContactModel.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Update fields
    update_data = contact_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    db.commit()
    db.refresh(contact)
    
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete (deactivate) a contact
    
    Note: Contacts are not physically deleted, just marked as inactive.
    """
    contact = db.query(ContactModel).filter(ContactModel.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Soft delete
    contact.is_active = False
    db.commit()
    
    return None
