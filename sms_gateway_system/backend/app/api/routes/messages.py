"""
Message sending API routes.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from app.db.database import get_db
from app.models.models import Message, Device, User, MessageStatus, MessageType
from app.schemas.schemas import (
    SendMessageRequest, BulkMessageRequest, MessageResponse, 
    MessageListResponse, BulkOperationResponse
)
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.post("/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a single SMS message."""
    # Validate device access if device_id provided
    if request.device_id:
        result = await db.execute(
            select(Device).where(Device.id == request.device_id)
        )
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
    
    # Create message
    message_uuid = str(uuid.uuid4())
    message = Message(
        message_uuid=message_uuid,
        message_type=MessageType.SMS,
        content=request.content,
        sender_name=request.sender_name,
        recipients=json.dumps(request.phone_numbers),
        total_recipients=len(request.phone_numbers),
        sender_id=current_user.id,
        device_id=request.device_id,
        sim_slot=request.sim_slot,
        status=MessageStatus.PENDING,
        metadata=request.metadata,
        scheduled_at=request.scheduled_at,
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        message_uuid=message.message_uuid,
        message_type=message.message_type,
        content=message.content,
        sender_name=message.sender_name,
        recipients=json.loads(message.recipients),
        total_recipients=message.total_recipients,
        status=message.status,
        parts_count=message.parts_count,
        created_at=message.created_at,
    )


@router.post("/bulk", response_model=BulkOperationResponse, status_code=status.HTTP_201_CREATED)
async def send_bulk_messages(
    request: BulkMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send bulk messages from list or uploaded file."""
    bulk_uuid = str(uuid.uuid4())
    accepted = 0
    rejected = 0
    
    for msg_data in request.messages:
        try:
            phone = msg_data.get("phone") or msg_data.get("phone_number")
            content = msg_data.get("content") or msg_data.get("message")
            
            if not phone or not content:
                rejected += 1
                continue
            
            message = Message(
                message_uuid=str(uuid.uuid4()),
                message_type=MessageType.SMS,
                content=content,
                sender_name=request.sender_name,
                recipients=json.dumps([phone]),
                total_recipients=1,
                sender_id=current_user.id,
                device_id=request.device_id,
                sim_slot=request.sim_slot,
                status=MessageStatus.PENDING,
                bulk_operation_id=bulk_uuid,
            )
            db.add(message)
            accepted += 1
        except Exception:
            rejected += 1
    
    await db.commit()
    
    return BulkOperationResponse(
        bulk_operation_id=bulk_uuid,
        total_messages=len(request.messages),
        accepted=accepted,
        rejected=rejected,
        created_at=datetime.utcnow(),
    )


@router.get("/history", response_model=MessageListResponse)
async def get_message_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    status_filter: Optional[MessageStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get sent message history."""
    offset = (page - 1) * page_size
    
    # Build query
    query = select(Message).where(Message.sender_id == current_user.id)
    
    if status_filter:
        query = query.where(Message.status == status_filter)
    
    # Get total count
    count_query = select(func.count(Message.id)).where(Message.sender_id == current_user.id)
    if status_filter:
        count_query = count_query.where(Message.status == status_filter)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get messages
    query = query.order_by(Message.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return MessageListResponse(
        items=[
            MessageResponse(
                id=m.id, message_uuid=m.message_uuid, message_type=m.message_type,
                content=m.content, sender_name=m.sender_name,
                recipients=json.loads(m.recipients), total_recipients=m.total_recipients,
                status=m.status, parts_count=m.parts_count, sent_at=m.sent_at,
                delivered_at=m.delivered_at, error_message=m.error_message,
                created_at=m.created_at,
            )
            for m in messages
        ],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific message details."""
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.sender_id == current_user.id
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return MessageResponse(
        id=message.id, message_uuid=message.message_uuid,
        message_type=message.message_type, content=message.content,
        sender_name=message.sender_name, recipients=json.loads(message.recipients),
        total_recipients=message.total_recipients, status=message.status,
        parts_count=message.parts_count, sent_at=message.sent_at,
        delivered_at=message.delivered_at, error_message=message.error_message,
        created_at=message.created_at,
    )


@router.delete("/{message_id}/cancel")
async def cancel_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending message."""
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.sender_id == current_user.id
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.status != MessageStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel message with status: {message.status.value}"
        )
    
    message.status = MessageStatus.CANCELLED
    await db.commit()
    
    return {"message": "Message cancelled successfully"}
