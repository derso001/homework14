from fastapi import Depends, HTTPException, status, Query, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi_limiter.depends import RateLimiter

from src.db.db import get_db
from src.db.models import Contact, User
from src.schemas import ContactCreate, ContactResponse

from src.services.auth import auth_service



router =  APIRouter(prefix='/contact', tags=["contact"])

@router.post("/contacts", status_code=201, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_note(contact: ContactCreate, db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    Creates a new contact for the current user.

    :param contact: The contact data to create.
    :type contact: ContactCreate
    :param db: The database session.
    :type db: Session
    :param user: The current authenticated user.
    :type user: User
    :return: The newly created contact.
    :rtype: Contact
    """
    new_contact = Contact(
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone_number=contact.phone_number,
        birthday=contact.birthday,
        additional_info=contact.additional_info,
        user_id=user.id  # Прив'язка контакту до користувача
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact


@router.get("/contacts", description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(skip: int = 0, limit: int = Query(default=10, le=100, ge=10), db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a list of contacts for the current user, with pagination.

    :param skip: Number of contacts to skip.
    :type skip: int
    :param limit: Maximum number of contacts to return (between 10 and 100).
    :type limit: int
    :param db: The database session.
    :type db: Session
    :param user: The current authenticated user.
    :type user: User
    :return: A list of contacts.
    :rtype: List[Contact]
    """
    contacts = db.query(Contact).filter(Contact.user_id == user.id).offset(skip).limit(limit).all()
    return contacts


@router.get("/contacts/search", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def search_contacts(
    first_name: Optional[str] = Query(None, description="Search by first name"),
    last_name: Optional[str] = Query(None, description="Search by last name"),
    email: Optional[str] = Query(None, description="Search by email"),
    db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)
):
    """
    Searches for contacts based on first name, last name, or email.

    :param first_name: Filter contacts by first name.
    :type first_name: str, optional
    :param last_name: Filter contacts by last name.
    :type last_name: str, optional
    :param email: Filter contacts by email.
    :type email: str, optional
    :param db: The database session.
    :type db: Session
    :param user: The current authenticated user.
    :type user: User
    :return: A list of contacts matching the search criteria.
    :rtype: List[Contact]
    """
    query = db.query(Contact).filter(Contact.user_id == user.id)
    
    if first_name:
        query = query.filter(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))
    
    contacts = query.all()
    return contacts

@router.get("/contacts/upcoming-birthdays", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_upcoming_birthdays(db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a list of contacts with birthdays within the next 7 days.

    :param db: The database session.
    :type db: Session
    :param user: The current authenticated user.
    :type user: User
    :return: A list of contacts with upcoming birthdays.
    :rtype: List[Contact]
    """
    today = datetime.today().date()
    next_week = today + timedelta(days=7)

    contacts = db.query(Contact).filter(
        Contact.user_id == user.id,
        Contact.birthday.between(today, next_week)
    ).all()

    return contacts

    return contacts


@router.get("/contacts/{contact_id}", description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contact(contact_id: int, db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a specific contact by ID for the current user.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :param user: The current authenticated user.
    :type user: User
    :return: The requested contact.
    :rtype: Contact
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found or does not belong to you")
    return contact


@router.put("/contacts/{contact_id}", description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def update_contact(contact_id: int, contact: ContactCreate, db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    Updates a specific contact for the current user.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param contact: The updated contact data.
    :type contact: ContactCreate
    :param db: The database session.
    :type db: Session
    :param user: The current authenticated user.
    :type user: User
    :return: The updated contact.
    :rtype: Contact
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found or does not belong to you")
    for key, value in contact.dict().items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def delete_contact(contact_id: int, db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    Deletes a specific contact for the current user.

    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :param user: The current authenticated user.
    :type user: User
    :return: None
    :rtype: None
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found or does not belong to you")
    db.delete(db_contact)
    db.commit()
    return None
