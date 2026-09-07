"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from enum import Enum


# ==================== Enums ====================

class UserRoleEnum(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


class MessageStatusEnum(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageTypeEnum(str, Enum):
    SMS = "sms"
    MMS = "mms"


class DeviceStatusEnum(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


# ==================== Authentication Schemas ====================

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class SignupRequest(BaseModel):
    """Signup request schema for first-time super admin."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


class TokenRefreshRequest(BaseModel):
    """Token refresh request schema."""
    refresh_token: str


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema (admin only)."""
    password: str = Field(..., min_length=8)
    role: UserRoleEnum = UserRoleEnum.USER
    rate_limit: int = Field(default=100, ge=1)
    is_active: bool = True


class UserUpdate(BaseModel):
    """User update schema."""
    full_name: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    rate_limit: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    role: UserRoleEnum
    rate_limit: int
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


class UserListResponse(BaseModel):
    """Paginated user list response."""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int


# ==================== API Key Schemas ====================

class APIKeyCreate(BaseModel):
    """API key creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    permissions: Dict[str, bool] = Field(
        default={"send_sms": True, "read_inbox": True, "read_history": True}
    )
    rate_limit: Optional[int] = Field(default=None, ge=1)
    expires_in_days: Optional[int] = Field(default=None, ge=1)


class APIKeyResponse(BaseModel):
    """API key response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    key_prefix: str  # Only show prefix for security
    permissions: Dict[str, bool]
    rate_limit: Optional[int] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime


class APIKeyWithSecret(APIKeyResponse):
    """API key response with secret (only on creation)."""
    api_key: str  # Full key shown only once


class APIKeyListResponse(BaseModel):
    """Paginated API key list response."""
    items: List[APIKeyResponse]
    total: int
    page: int
    page_size: int


# ==================== Message Schemas ====================

class SendMessageRequest(BaseModel):
    """Single message send request."""
    phone_numbers: List[str] = Field(..., min_length=1)
    content: str = Field(..., min_length=1, max_length=1600)
    sender_name: Optional[str] = Field(default=None, max_length=255)
    device_id: Optional[int] = None
    sim_slot: Optional[int] = Field(default=None, ge=1, le=2)
    scheduled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BulkMessageRequest(BaseModel):
    """Bulk message send request."""
    messages: List[Dict[str, Any]] = Field(..., min_length=1)
    # Each message: {"phone": "...", "content": "...", "name": "..."}
    device_id: Optional[int] = None
    sim_slot: Optional[int] = None
    sender_name: Optional[str] = None
    batch_delay_min: int = Field(default=1, ge=0)
    batch_delay_max: int = Field(default=3, ge=0)


class MessageResponse(BaseModel):
    """Message response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    message_uuid: str
    message_type: MessageTypeEnum
    content: str
    sender_name: Optional[str] = None
    recipients: List[str]
    total_recipients: int
    status: MessageStatusEnum
    parts_count: int
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    # Optional fields
    device_name: Optional[str] = None
    sender_email: Optional[str] = None


class MessageListResponse(BaseModel):
    """Paginated message list response."""
    items: List[MessageResponse]
    total: int
    page: int
    page_size: int


class BulkOperationResponse(BaseModel):
    """Bulk operation response."""
    bulk_operation_id: str
    total_messages: int
    accepted: int
    rejected: int
    status: str = "processing"
    created_at: datetime


# ==================== Inbox Schemas ====================

class IncomingMessageResponse(BaseModel):
    """Incoming message response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    message_uuid: str
    message_type: MessageTypeEnum
    sender_phone: str
    content: str
    subject: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    device_id: int
    device_name: Optional[str] = None
    sim_slot: Optional[int] = None
    is_read: bool
    received_at: datetime
    created_at: datetime


class IncomingMessageListResponse(BaseModel):
    """Paginated incoming message list response."""
    items: List[IncomingMessageResponse]
    total: int
    page: int
    page_size: int
    unread_count: int


class MarkAsReadRequest(BaseModel):
    """Mark message as read request."""
    message_ids: List[int] = Field(..., min_length=1)


# ==================== Device Schemas ====================

class DeviceBase(BaseModel):
    """Base device schema."""
    device_name: Optional[str] = None
    send_delay_min: int = Field(default=1, ge=0)
    send_delay_max: int = Field(default=3, ge=0)
    working_hours_enabled: bool = False
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None


class DeviceUpdate(DeviceBase):
    """Device update schema."""
    pass


class DeviceResponse(DeviceBase):
    """Device response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    device_id: str
    phone_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    android_version: Optional[str] = None
    app_version: Optional[str] = None
    sim_cards: List[Dict[str, Any]] = []
    status: DeviceStatusEnum
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DeviceListResponse(BaseModel):
    """Device list response."""
    items: List[DeviceResponse]
    total: int
    online_count: int
    offline_count: int


# ==================== Webhook Schemas ====================

class WebhookCreate(BaseModel):
    """Webhook creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=2048)
    events: List[str] = Field(..., min_length=1)
    secret: Optional[str] = Field(default=None, max_length=255)


class WebhookResponse(BaseModel):
    """Webhook response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    url: str
    events: List[str]
    is_active: bool
    last_triggered_at: Optional[datetime] = None
    failure_count: int
    created_at: datetime


class WebhookListResponse(BaseModel):
    """Webhook list response."""
    items: List[WebhookResponse]
    total: int


# ==================== Settings Schemas ====================

class SystemSettingsResponse(BaseModel):
    """System settings response."""
    delay_min: int
    delay_max: int
    max_bulk_messages: int
    telegram_enabled: bool
    backup_enabled: bool
    rate_limit_default: int
    rate_limit_admin: int


class SystemSettingsUpdate(BaseModel):
    """System settings update schema."""
    delay_min: Optional[int] = Field(default=None, ge=0)
    delay_max: Optional[int] = Field(default=None, ge=0)
    max_bulk_messages: Optional[int] = Field(default=None, ge=1)
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    backup_enabled: Optional[bool] = None


# ==================== Dashboard Schemas ====================

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_devices: int
    online_devices: int
    total_users: int
    total_messages_sent: int
    total_messages_delivered: int
    total_messages_failed: int
    total_messages_queued: int
    total_messages_received: int
    messages_today: int
    messages_this_hour: int


class ChartDataPoint(BaseModel):
    """Chart data point."""
    label: str
    value: int


class DashboardCharts(BaseModel):
    """Dashboard chart data."""
    messages_by_status: List[ChartDataPoint]
    messages_by_day: List[ChartDataPoint]
    messages_by_device: List[ChartDataPoint]
    top_senders: List[ChartDataPoint]


class RecentActivity(BaseModel):
    """Recent activity item."""
    id: int
    action: str
    resource_type: Optional[str]
    user_email: Optional[str]
    created_at: datetime


class DashboardResponse(BaseModel):
    """Complete dashboard response."""
    stats: DashboardStats
    charts: DashboardCharts
    recent_activities: List[RecentActivity]
    connected_devices: List[DeviceResponse]


# ==================== Pagination ====================

class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)
