"""
Inbox (incoming messages) API routes.
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from app.db.database import get_db
from app.models.models import IncomingMessage, Device, User, MessageType
from app.schemas.schemas import (
    IncomingMessageResponse, IncomingMessageListResponse, MarkAsReadRequest
)
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=IncomingMessageListResponse)
async def get_inbox(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    is_read: Optional[bool] = None,
    device_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get incoming messages (inbox)."""
    offset = (page - 1) * page_size
    
    # Build base query - admins see all, users see assigned devices
    if current_user.is_admin:
        query = select(IncomingMessage)
        count_query = select(func.count(IncomingMessage.id))
    else:
        # Get user's assigned devices
        from app.models.models import UserPhoneAssignment
        assignment_result = await db.execute(
            select(UserPhoneAssignment.device_id).where(
                UserPhoneAssignment.user_id == current_user.id
            )
        )
        assigned_device_ids = [r[0] for r in assignment_result.all()]
        
        if not assigned_device_ids:
            return IncomingMessageListResponse(
                items=[], total=0, page=page, page_size=page_size, unread_count=0
            )
        
        query = select(IncomingMessage).where(
            IncomingMessage.device_id.in_(assigned_device_ids)
        )
        count_query = select(func.count(IncomingMessage.id)).where(
            IncomingMessage.device_id.in_(assigned_device_ids)
        )
    
    # Apply filters
    if is_read is not None:
        query = query.where(IncomingMessage.is_read == is_read)
        count_query = count_query.where(IncomingMessage.is_read == is_read)
    
    if device_id is not None:
        query = query.where(IncomingMessage.device_id == device_id)
        count_query = count_query.where(IncomingMessage.device_id == device_id)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get unread count
    unread_query = select(func.count(IncomingMessage.id)).where(
        IncomingMessage.is_read == False
    )
    if not current_user.is_admin and assigned_device_ids:
        unread_query = unread_query.where(
            IncomingMessage.device_id.in_(assigned_device_ids)
        )
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar() or 0
    
    # Get messages
    query = query.order_by(IncomingMessage.received_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Enrich with device names
    device_map = {}
    for msg in messages:
        if msg.device_id not in device_map:
            dev_result = await db.execute(
                select(Device).where(Device.id == msg.device_id)
            )
            device = dev_result.scalar_one_or_none()
            device_map[msg.device_id] = device.device_name if device else f"Device {msg.device_id}"
    
    return IncomingMessageListResponse(
        items=[
            IncomingMessageResponse(
                id=m.id, message_uuid=m.message_uuid, message_type=m.message_type,
                sender_phone=m.sender_phone, content=m.content, subject=m.subject,
                attachments=m.attachments, device_id=m.device_id,
                device_name=device_map.get(m.device_id), sim_slot=m.sim_slot,
                is_read=m.is_read, received_at=m.received_at, created_at=m.created_at,
            )
            for m in messages
        ],
        total=total, page=page, page_size=page_size, unread_count=unread_count,
    )


@router.get("/{message_id}", response_model=IncomingMessageResponse)
async def get_inbox_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific inbox message."""
    result = await db.execute(
        select(IncomingMessage).where(IncomingMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check access
    if not current_user.is_admin:
        from app.models.models import UserPhoneAssignment
        assignment_result = await db.execute(
            select(UserPhoneAssignment).where(
                UserPhoneAssignment.user_id == current_user.id,
                UserPhoneAssignment.device_id == message.device_id
            )
        )
        if not assignment_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get device name
    dev_result = await db.execute(
        select(Device).where(Device.id == message.device_id)
    )
    device = dev_result.scalar_one_or_none()
    
    return IncomingMessageResponse(
        id=message.id, message_uuid=message.message_uuid,
        message_type=message.message_type, sender_phone=message.sender_phone,
        content=message.content, subject=message.subject,
        attachments=message.attachments, device_id=message.device_id,
        device_name=device.device_name if device else None,
        sim_slot=message.sim_slot, is_read=message.is_read,
        received_at=message.received_at, created_at=message.created_at,
    )


@router.put("/mark-read")
async def mark_as_read(
    request: MarkAsReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark messages as read."""
    for msg_id in request.message_ids:
        result = await db.execute(
            select(IncomingMessage).where(IncomingMessage.id == msg_id)
        )
        message = result.scalar_one_or_none()
        if message:
            message.is_read = True
    
    await db.commit()
    return {"message": f"Marked {len(request.message_ids)} messages as read"}


@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete inbox message."""
    result = await db.execute(
        select(IncomingMessage).where(IncomingMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    await db.delete(message)
    await db.commit()
    return {"message": "Message deleted"}
