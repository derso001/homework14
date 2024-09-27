import os
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.db.db import get_db
from src.repository import users as repository_users


class Auth:
    """
    A service class for handling authentication and token-related functionality, including
    password hashing, token creation (access, refresh, and email), and user authentication.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = os.getenv('SECRET_KEY')
    ALGORITHM = os.getenv('JWT_ALGORITHM')
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    def verify_password(self, plain_password, hashed_password):
        """
        Verifies a plain-text password against a hashed password.

        :param plain_password: The plain-text password to verify.
        :type plain_password: str
        :param hashed_password: The hashed password to compare against.
        :type hashed_password: str
        :return: True if the password is valid, False otherwise.
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Hashes a plain-text password using bcrypt.

        :param password: The plain-text password to hash.
        :type password: str
        :return: The hashed password.
        :rtype: str
        """
        return self.pwd_context.hash(password)

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Creates a new JWT access token with an expiration time.

        :param data: The data to encode in the token (e.g., user info).
        :type data: dict
        :param expires_delta: Optional expiration time in seconds. If not provided, defaults to 15 minutes.
        :type expires_delta: Optional[float]
        :return: The encoded JWT access token.
        :rtype: str
        """
        if not expires_delta:
            expires_delta = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')) * 60
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Creates a new JWT refresh token with an expiration time.

        :param data: The data to encode in the token (e.g., user info).
        :type data: dict
        :param expires_delta: Optional expiration time in seconds. If not provided, defaults to 7 days.
        :type expires_delta: Optional[float]
        :return: The encoded JWT refresh token.
        :rtype: str
        """
        if not expires_delta:
            expires_delta = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS')) * 86400
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decodes and verifies a refresh token, returning the email if the token is valid.

        :param refresh_token: The refresh token to decode.
        :type refresh_token: str
        :return: The email extracted from the token if valid.
        :rtype: str
        :raises HTTPException: If the token is invalid or the scope is incorrect.
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        Retrieves the current authenticated user based on the provided JWT token.

        :param token: The JWT token provided by the OAuth2 scheme.
        :type token: str
        :param db: The database session.
        :type db: Session
        :return: The current authenticated user.
        :rtype: User
        :raises HTTPException: If the token is invalid or the user does not exist.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user

    def create_email_token(self, data: dict):
        """
        Creates a token for email verification with a 7-day expiration.

        :param data: The data to encode in the token (e.g., email info).
        :type data: dict
        :return: The encoded email verification token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token
    
    async def get_email_from_token(self, token: str):
        
        """
        Decodes an email verification token and retrieves the email from it.

        :param token: The email verification token.
        :type token: str
        :return: The email extracted from the token.
        :rtype: str
        :raises HTTPException: If the token is invalid.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")

auth_service = Auth()