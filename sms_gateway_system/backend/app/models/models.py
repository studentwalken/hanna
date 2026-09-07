"""
Database models for the SMS Gateway System.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    String, Integer, Boolean, DateTime, ForeignKey, Text, 
    Float, Index, UniqueConstraint, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.database import Base


class UserRole(str, PyEnum):
    """User role enumeration."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


class MessageStatus(str, PyEnum):
    """Message status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(str, PyEnum):
    """Message type enumeration."""
    SMS = "sms"
    MMS = "mms"


class DeviceStatus(str, PyEnum):
    """Device connection status."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


# ==================== User Models ====================

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # Rate limiting
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)  # messages per hour
    rate_limit_period: Mapped[int] = mapped_column(Integer, default=3600)  # seconds
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    api_keys: Mapped[List["APIKey"]] = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    assigned_phones: Mapped[List["UserPhoneAssignment"]] = relationship("UserPhoneAssignment", back_populates="user", cascade="all, delete-orphan")
    sent_messages: Mapped[List["Message"]] = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN
    
    @property
    def is_admin(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]


# ==================== API Key Models ====================

class APIKey(Base):
    """API Key model for external application access."""
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)  # First 8 chars for identification
    
    # Permissions
    permissions: Mapped[dict] = mapped_column(JSON, default=lambda: {"send_sms": True, "read_inbox": True, "read_history": True})
    
    # Rate limiting (overrides user limit if set)
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey {self.key_prefix}...>"


# ==================== Device Models ====================

class Device(Base):
    """Android device model representing connected phones."""
    __tablename__ = "devices"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)  # Unique device identifier from app
    device_name: Mapped[str] = mapped_column(String(255), nullable=True)  # User-friendly name
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Device's phone number
    
    # Device info
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    android_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    app_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # SIM cards info (stored as JSON)
    sim_cards: Mapped[dict] = mapped_column(JSON, default=list)  # [{"slot": 1, "number": "...", "carrier": "..."}]
    
    # Status
    status: Mapped[DeviceStatus] = mapped_column(SQLEnum(DeviceStatus), default=DeviceStatus.OFFLINE)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Settings
    send_delay_min: Mapped[int] = mapped_column(Integer, default=1)  # seconds
    send_delay_max: Mapped[int] = mapped_column(Integer, default=3)  # seconds
    working_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    working_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM format
    working_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM format
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    assignments: Mapped[List["UserPhoneAssignment"]] = relationship("UserPhoneAssignment", back_populates="device", cascade="all, delete-orphan")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="device", cascade="all, delete-orphan")
    incoming_messages: Mapped[List["IncomingMessage"]] = relationship("IncomingMessage", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Device {self.device_name or self.device_id}>"


class UserPhoneAssignment(Base):
    """Assignment of devices to users."""
    __tablename__ = "user_phone_assignments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    
    # Permissions for this assignment
    can_send: Mapped[bool] = mapped_column(Boolean, default=True)
    can_receive: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="assigned_phones")
    device: Mapped["Device"] = relationship("Device", back_populates="assignments")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'device_id', name='unique_user_device_assignment'),
    )


# ==================== Message Models ====================

class Message(Base):
    """Outgoing message model."""
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)  # UUID for external reference
    
    # Content
    message_type: Mapped[MessageType] = mapped_column(SQLEnum(MessageType), default=MessageType.SMS)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Flexible sender name per message
    
    # Recipients
    recipients: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of phone numbers
    total_recipients: Mapped[int] = mapped_column(Integer, default=1)
    
    # Routing
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    device_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    sim_slot: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-based SIM slot
    
    # Status tracking
    status: Mapped[MessageStatus] = mapped_column(SQLEnum(MessageStatus), default=MessageStatus.PENDING)
    parts_count: Mapped[int] = mapped_column(Integer, default=1)  # For multipart SMS
    
    # Delivery info
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Retry logic
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)  # Additional data from API
    bulk_operation_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)  # For bulk operations
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    device: Mapped["Device"] = relationship("Device", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.message_uuid}>"
    
    __table_args__ = (
        Index('idx_messages_status_created', 'status', 'created_at'),
        Index('idx_messages_sender_created', 'sender_id', 'created_at'),
    )


# ==================== Incoming Message Models ====================

class IncomingMessage(Base):
    """Incoming message (inbox) model."""
    __tablename__ = "incoming_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    
    # Content
    message_type: Mapped[MessageType] = mapped_column(SQLEnum(MessageType), default=MessageType.SMS)
    sender_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Source device
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    sim_slot: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)  # Processed by webhooks
    
    # Message metadata
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    parts_count: Mapped[int] = mapped_column(Integer, default=1)
    service_center: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # For MMS
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attachments: Mapped[dict] = mapped_column(JSON, default=list)  # [{"type": "image", "url": "...", "name": "..."}]
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="incoming_messages")
    
    def __repr__(self):
        return f"<IncomingMessage from {self.sender_phone}>"
    
    __table_args__ = (
        Index('idx_incoming_device_received', 'device_id', 'received_at'),
        Index('idx_incoming_sender_received', 'sender_phone', 'received_at'),
    )


# ==================== Webhook Models ====================

class Webhook(Base):
    """Webhook configuration for external notifications."""
    __tablename__ = "webhooks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # For HMAC signature
    
    # Events to subscribe
    events: Mapped[list] = mapped_column(JSON, default=list)  # ["message.sent", "message.delivered", "message.failed", "inbox.received"]
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Webhook {self.name}>"


# ==================== Settings Models ====================

class SystemSettings(Base):
    """System-wide settings."""
    __tablename__ = "system_settings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemSettings {self.key}>"


# ==================== Activity Log Models ====================

class ActivityLog(Base):
    """Activity log for audit trail."""
    __tablename__ = "activity_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Action details
    action: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Details
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ActivityLog {self.action}>"
