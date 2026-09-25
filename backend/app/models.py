# ====================== app/models.py ======================
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


# ---------------- WORKSPACE ----------------
class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    users = relationship(
        "User", back_populates="workspace",
        cascade="all, delete-orphan", lazy="selectin",
    )
    subscription = relationship(
        "Subscription", back_populates="workspace",
        uselist=False, cascade="all, delete-orphan", lazy="selectin",
    )
    emails = relationship(
        "EmailThread", back_populates="workspace",
        cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self):
        return f"<Workspace id={self.id} name={self.name}>"


# ---------------- FEATURE USAGE ----------------
class FeatureUsage(Base):
    __tablename__ = "feature_usage"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    feature = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace")

    __table_args__ = (
        Index("ix_feature_usage_workspace_feature", "workspace_id", "feature"),
    )


# ---------------- USER ----------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="member", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    # lazy="selectin" so `user.workspace` is safe to touch anywhere without
    # tripping SQLAlchemy's async "MissingGreenlet" lazy-load error.
    workspace = relationship("Workspace", back_populates="users", lazy="selectin")

    __table_args__ = (
        Index("uq_user_email_workspace", "email", "workspace_id", unique=True),
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


# ---------------- SUBSCRIPTION ----------------
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan = Column(String(50), nullable=False, default="starter")
    stripe_customer_id = Column(String(255), index=True)
    stripe_subscription_id = Column(String(255), index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ends_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="subscription")


# ---------------- EMAIL THREAD ----------------
class EmailThread(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    thread_id = Column(String(255), nullable=False)
    subject = Column(String(255))
    sender = Column(String(255))
    snippet = Column(Text, nullable=False)
    needs_followup = Column(Boolean, default=False, nullable=False)
    ai_insight = Column(Text)
    status = Column(String(50), default="new", nullable=False)
    detected_value = Column(Integer, default=0, nullable=False)
    # Populated once a follow-up action is taken; used by the analytics
    # and dashboard views to report actual recovered revenue.
    recovered_value = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="emails")

    __table_args__ = (
        Index("uq_workspace_thread", "workspace_id", "thread_id", unique=True),
    )
