"""
Device management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.models.models import Device, User, UserPhoneAssignment, DeviceStatus
from app.schemas.schemas import DeviceResponse, DeviceListResponse, DeviceUpdate
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=DeviceListResponse)
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all connected devices."""
    # Admins see all, users see assigned only
    if current_user.is_admin:
        query = select(Device)
        count_query = select(func.count(Device.id))
    else:
        assignment_result = await db.execute(
            select(UserPhoneAssignment.device_id).where(
                UserPhoneAssignment.user_id == current_user.id
            )
        )
        assigned_device_ids = [r[0] for r in assignment_result.all()]
        
        if not assigned_device_ids:
            return DeviceListResponse(items=[], total=0, online_count=0, offline_count=0)
        
        query = select(Device).where(Device.id.in_(assigned_device_ids))
        count_query = select(func.count(Device.id)).where(Device.id.in_(assigned_device_ids))
    
    # Get counts
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    online_result = await db.execute(
        select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
    )
    online_count = online_result.scalar() or 0
    
    # Get devices
    result = await db.execute(query.order_by(Device.last_seen_at.desc()))
    devices = result.scalars().all()
    
    return DeviceListResponse(
        items=[
            DeviceResponse(
                id=d.id, device_id=d.device_id, device_name=d.device_name,
                phone_number=d.phone_number, manufacturer=d.manufacturer,
                model=d.model, android_version=d.android_version,
                app_version=d.app_version, sim_cards=d.sim_cards,
                status=d.status, last_seen_at=d.last_seen_at,
                created_at=d.created_at, updated_at=d.updated_at,
                send_delay_min=d.send_delay_min, send_delay_max=d.send_delay_max,
                working_hours_enabled=d.working_hours_enabled,
                working_hours_start=d.working_hours_start,
                working_hours_end=d.working_hours_end,
            )
            for d in devices
        ],
        total=total,
        online_count=online_count,
        offline_count=total - online_count,
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific device details."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check access
    if not current_user.is_admin:
        assignment_result = await db.execute(
            select(UserPhoneAssignment).where(
                UserPhoneAssignment.user_id == current_user.id,
                UserPhoneAssignment.device_id == device_id
            )
        )
        if not assignment_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access denied")
    
    return DeviceResponse(
        id=device.id, device_id=device.device_id, device_name=device.device_name,
        phone_number=device.phone_number, manufacturer=device.manufacturer,
        model=device.model, android_version=device.android_version,
        app_version=device.app_version, sim_cards=device.sim_cards,
        status=device.status, last_seen_at=device.last_seen_at,
        created_at=device.created_at, updated_at=device.updated_at,
        send_delay_min=device.send_delay_min, send_delay_max=device.send_delay_max,
        working_hours_enabled=device.working_hours_enabled,
        working_hours_start=device.working_hours_start,
        working_hours_end=device.working_hours_end,
    )


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update device settings (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = device_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    await db.commit()
    await db.refresh(device)
    
    return DeviceResponse(
        id=device.id, device_id=device.device_id, device_name=device.device_name,
        phone_number=device.phone_number, manufacturer=device.manufacturer,
        model=device.model, android_version=device.android_version,
        app_version=device.app_version, sim_cards=device.sim_cards,
        status=device.status, last_seen_at=device.last_seen_at,
        created_at=device.created_at, updated_at=device.updated_at,
        send_delay_min=device.send_delay_min, send_delay_max=device.send_delay_max,
        working_hours_enabled=device.working_hours_enabled,
        working_hours_start=device.working_hours_start,
        working_hours_end=device.working_hours_end,
    )


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove device (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    await db.delete(device)
    await db.commit()
    
    return {"message": "Device removed"}
