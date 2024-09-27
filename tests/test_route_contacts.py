from unittest.mock import patch, MagicMock
import pytest
from src.db.models import Contact, User
from src.schemas import ContactCreate
from datetime import datetime, timedelta

@pytest.fixture()
def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    data = response.json()
    return data["access_token"]

def test_create_contact(client, token):
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "+123456789",
        "birthday": "1990-01-01",
        "additional_info": "Friend"
    }
    
    with patch('src.services.auth.auth_service.get_current_user', return_value=User(id=1)):
        response = client.post(
            "/api/contact/contacts",
            json=contact_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["first_name"] == contact_data["first_name"]
        assert data["last_name"] == contact_data["last_name"]
        assert "id" in data

def test_read_contacts(client, token):
    with patch('src.services.auth.auth_service.get_current_user', return_value=User(id=1)):
        response = client.get(
            "/api/contact/contacts",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert "id" in data[0]

def test_search_contacts(client, token):
    with patch('src.services.auth.auth_service.get_current_user', return_value=User(id=1)):
        response = client.get(
            "/api/contact/contacts/search?first_name=John",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["first_name"] == "John"

def test_get_upcoming_birthdays(client, token):
    with patch('src.services.auth.auth_service.get_current_user', return_value=User(id=1)):
        response = client.get(
            "/api/contact/contacts/upcoming-birthdays",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

def test_read_contact(client, token):
    with patch('src.services.auth.auth_service.get_current_user', return_value=User(id=1)):
        response = client.get(
            "/api/contact/contacts/1",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == 1

def test_update_contact(client, token):
    contact_data = {
        "first_name": "John",
        "last_name": "Updated",
        "email": "john.updated@example.com",
        "phone_number": "+123456789",
        "birthday": "1990-01-01",
        "additional_info": "Updated Info"
    }
    
    with patch('src.services.auth.auth_service.get_current_user', return_value=User(id=1)):
        response = client.put(
            "/api/contact/contacts/1",
            json=contact_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["first_name"] == contact_data["first_name"]
        assert data["last_name"] == contact_data["last_name"]

def test_delete_contact(client, token):
    with patch('src.services.auth.auth_service.get_current_user', return_value=User(id=1)):
        response = client.delete(
            "/api/contact/contacts/1",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 204
