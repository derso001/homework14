import os
from dotenv import load_dotenv
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import auth_service

load_dotenv()

# mail_from = os.getenv('MAIL_FROM')
# print(mail_from)
# print(type(mail_from))

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_FROM=os.getenv('MAIL_FROM'),
    MAIL_PORT=int(os.getenv('MAIL_PORT')),
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_FROM_NAME="Desired Name",
    MAIL_STARTTLS=False,  # TLS отключен
    MAIL_SSL_TLS=True,    # Включить SSL
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    Sends an email to the specified recipient for email verification.

    :param email: The recipient's email address.
    :type email: EmailStr
    :param username: The username of the recipient, used in the email template.
    :type username: str
    :param host: The host URL where the user can verify their email.
    :type host: str
    :return: None
    :raises ConnectionErrors: If there is an error while sending the email.
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as err:
        print(err)

