from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Installation(Base):
    """
    A GitHub App installation, owned by a user. A user can have several
    (e.g. their personal account + one or more organizations), so this is a
    one-to-many from User — installation ids are NOT stored on the users table.
    """

    __tablename__ = "installations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    github_installation_id = Column(Integer, unique=True, nullable=False, index=True)
    account_login = Column(String)   # e.g. "vidhiisaxena" or an org login
    account_type = Column(String)    # "User" | "Organization"
    target_type = Column(String)     # "User" | "Organization"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User")
