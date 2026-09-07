"""
Dashboard API routes - Statistics and analytics.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload

from app.db.database import get_db
from app.models.models import (
    User, Device, Message, IncomingMessage, ActivityLog, DeviceStatus,
    MessageStatus
)
from app.schemas.schemas import (
    DashboardResponse, DashboardStats, DashboardCharts, 
    ChartDataPoint, RecentActivity, DeviceResponse
)
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive dashboard data.
    
    Returns statistics, charts data, recent activities, and connected devices.
    Accessible by all authenticated users with appropriate permissions.
    """
    # Only admins can see global stats, regular users see their own
    if current_user.is_admin:
        # Global statistics for admins
        user_filter = True  # No filter for admins
    else:
        user_filter = Message.sender_id == current_user.id
    
    # Calculate date ranges
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    
    # ========== Statistics ==========
    
    # Device counts
    device_count_result = await db.execute(select(func.count(Device.id)))
    total_devices = device_count_result.scalar() or 0
    
    online_device_result = await db.execute(
        select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
    )
    online_devices = online_device_result.scalar() or 0
    
    # User count (admins only)
    if current_user.is_admin:
        user_count_result = await db.execute(select(func.count(User.id)))
        total_users = user_count_result.scalar() or 0
    else:
        total_users = 1
    
    # Message statistics
    sent_count = await db.execute(
        select(func.count(Message.id)).where(
            Message.status == MessageStatus.SENT
        )
    )
    total_sent = sent_count.scalar() or 0
    
    delivered_count = await db.execute(
        select(func.count(Message.id)).where(
            Message.status == MessageStatus.DELIVERED
        )
    )
    total_delivered = delivered_count.scalar() or 0
    
    failed_count = await db.execute(
        select(func.count(Message.id)).where(
            Message.status == MessageStatus.FAILED
        )
    )
    total_failed = failed_count.scalar() or 0
    
    queued_count = await db.execute(
        select(func.count(Message.id)).where(
            Message.status.in_([MessageStatus.PENDING, MessageStatus.QUEUED])
        )
    )
    total_queued = queued_count.scalar() or 0
    
    # Inbox count
    inbox_count = await db.execute(select(func.count(IncomingMessage.id)))
    total_received = inbox_count.scalar() or 0
    
    # Today's messages
    today_count = await db.execute(
        select(func.count(Message.id)).where(
            Message.created_at >= today_start
        )
    )
    messages_today = today_count.scalar() or 0
    
    # This hour's messages
    hour_count = await db.execute(
        select(func.count(Message.id)).where(
            Message.created_at >= hour_start
        )
    )
    messages_this_hour = hour_count.scalar() or 0
    
    stats = DashboardStats(
        total_devices=total_devices,
        online_devices=online_devices,
        total_users=total_users,
        total_messages_sent=total_sent,
        total_messages_delivered=total_delivered,
        total_messages_failed=total_failed,
        total_messages_queued=total_queued,
        total_messages_received=total_received,
        messages_today=messages_today,
        messages_this_hour=messages_this_hour,
    )
    
    # ========== Charts Data ==========
    
    # Messages by status
    status_counts = await db.execute(
        select(Message.status, func.count(Message.id))
        .group_by(Message.status)
    )
    messages_by_status = [
        ChartDataPoint(label=status.value if status else "unknown", value=count)
        for status, count in status_counts.all()
    ]
    
    # Messages by day (last 7 days)
    seven_days_ago = now - timedelta(days=7)
    daily_counts = await db.execute(
        select(
            func.date(Message.created_at).label('date'),
            func.count(Message.id)
        )
        .where(Message.created_at >= seven_days_ago)
        .group_by(func.date(Message.created_at))
    )
    messages_by_day = [
        ChartDataPoint(label=str(date), value=count)
        for date, count in daily_counts.all()
    ]
    
    # Messages by device
    device_counts = await db.execute(
        select(Device.device_name, func.count(Message.id))
        .join(Message, Message.device_id == Device.id, isouter=True)
        .group_by(Device.id, Device.device_name)
    )
    messages_by_device = [
        ChartDataPoint(label=name or "Unassigned", value=count)
        for name, count in device_counts.all() if count > 0
    ]
    
    # Top senders (users with most messages)
    if current_user.is_admin:
        sender_counts = await db.execute(
            select(User.email, func.count(Message.id))
            .join(Message, Message.sender_id == User.id)
            .group_by(User.id, User.email)
            .order_by(func.count(Message.id).desc())
            .limit(5)
        )
        top_senders = [
            ChartDataPoint(label=email, value=count)
            for email, count in sender_counts.all()
        ]
    else:
        top_senders = []
    
    charts = DashboardCharts(
        messages_by_status=messages_by_status,
        messages_by_day=messages_by_day,
        messages_by_device=messages_by_device,
        top_senders=top_senders,
    )
    
    # ========== Recent Activities ==========
    recent_logs = await db.execute(
        select(ActivityLog)
        .options(joinedload(ActivityLog.user))
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
    )
    recent_activities = [
        RecentActivity(
            id=log.id,
            action=log.action,
            resource_type=log.resource_type,
            user_email=log.user.email if log.user else None,
            created_at=log.created_at,
        )
        for log in recent_logs.scalars().all()
    ]
    
    # ========== Connected Devices ==========
    devices_result = await db.execute(
        select(Device)
        .order_by(Device.last_seen_at.desc())
        .limit(10)
    )
    connected_devices = [
        DeviceResponse(
            id=device.id,
            device_id=device.device_id,
            device_name=device.device_name,
            phone_number=device.phone_number,
            manufacturer=device.manufacturer,
            model=device.model,
            android_version=device.android_version,
            app_version=device.app_version,
            sim_cards=device.sim_cards,
            status=device.status,
            last_seen_at=device.last_seen_at,
            created_at=device.created_at,
            updated_at=device.updated_at,
            send_delay_min=device.send_delay_min,
            send_delay_max=device.send_delay_max,
            working_hours_enabled=device.working_hours_enabled,
            working_hours_start=device.working_hours_start,
            working_hours_end=device.working_hours_end,
        )
        for device in devices_result.scalars().all()
    ]
    
    return DashboardResponse(
        stats=stats,
        charts=charts,
        recent_activities=recent_activities,
        connected_devices=connected_devices,
    )
