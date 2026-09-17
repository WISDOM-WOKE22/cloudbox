import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cloudbox_api.db.base import Base


class ResourceType(str, enum.Enum):
    FILE = "file"
    FOLDER = "folder"


class Permission(str, enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"


class Share(Base):
    __tablename__ = "shares"
    __table_args__ = (
        UniqueConstraint(
            "resource_type", "resource_id", "shared_with_id",
            name="uq_share_resource_user",
        ),
        CheckConstraint(
            "owner_id != shared_with_id",
            name="ck_not_self_share",
        ),
        CheckConstraint(
            "resource_type IN ('file', 'folder')",
            name="ck_resource_type",
        ),
        CheckConstraint(
            "permission IN ('viewer', 'editor')",
            name="ck_permission",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    resource_type: Mapped[str] = mapped_column(String(10), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    shared_with_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    shared_with: Mapped["User"] = relationship(foreign_keys=[shared_with_id])
