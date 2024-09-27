from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

from src.db.db import get_db
from src.db.models import User
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.schemas import UserDb

load_dotenv()

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves the current authenticated user's details.

    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The current user's details.
    :rtype: UserDb
    """
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    """
    Updates the user's avatar by uploading a new image to Cloudinary and updating the user record.

    :param file: The new avatar image file.
    :type file: UploadFile
    :param current_user: The current authenticated user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The updated user with the new avatar URL.
    :rtype: UserDb
    """
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'NotesApp/{current_user.username}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'NotesApp/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user