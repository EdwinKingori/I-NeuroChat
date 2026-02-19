import uuid
from sqlalchemy import Column, String, DateTime,func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)  
    description = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships 
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles"
    )

    # ✅ Role ↔ User (M2M via user_roles)
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles"
    )
