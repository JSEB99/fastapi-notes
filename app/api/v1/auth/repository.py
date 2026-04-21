import email

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, user_email: str) -> User | None:
        query = select(User).where(User.email == user_email)
        return self.db.execute(query).scalar_one_or_none()

    def create(self, user_email: str, hashed_pass: str, full_name: str) -> User:
        user = User(
            email=user_email,
            hashed_pass=hashed_pass,
            full_name=full_name
        )
        self.db.add(user)
        self.db.flush()
        return user

    def set_role(self, user: User, role: str) -> User:
        user.role = role
        self.db.add(user)
        return user
