import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from src.db.models import User
from src.schemas import UserModel
from src.repository.users import get_user_by_email, create_user, update_token, confirmed_email


class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, email="test@example.com", confirmed=False, refresh_token=None)

    async def test_get_user_by_email_found(self):
        self.session.query().filter().first.return_value = self.user
        result = await get_user_by_email(email="test@example.com", db=self.session)
        self.assertEqual(result, self.user)

    async def test_get_user_by_email_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email(email="test@example.com", db=self.session)
        self.assertIsNone(result)

    async def test_create_user(self):
        body = UserModel(email="test@example.com", password="password123")
        self.session.add.return_value = None
        self.session.commit.return_value = None
        self.session.refresh.return_value = self.user
        result = await create_user(body=body, db=self.session)
        self.assertEqual(result.email, body.email)
        self.assertTrue(hasattr(result, "id"))

    async def test_update_token(self):
        token = "new_refresh_token"
        await update_token(user=self.user, token=token, db=self.session)
        self.assertEqual(self.user.refresh_token, token)
        self.session.commit.assert_called_once()

    async def test_confirmed_email(self):
        self.session.query().filter().first.return_value = self.user
        await confirmed_email(email="test@example.com", db=self.session)
        self.assertTrue(self.user.confirmed)
        self.session.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()