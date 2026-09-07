"""
User management API routes (Admin only).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.db.database import get_db
from app.models.models import User, ActivityLog, Device, UserPhoneAssignment
from app.schemas.schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse
)
from app.utils.auth import get_password_hash
from app.api.routes.auth import get_current_user

router = APIRouter()


async def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    offset = (page - 1) * page_size
    
    result = await db.execute(select(func.count(User.id)))
    total = result.scalar() or 0
    
    users_result = await db.execute(
        select(User).offset(offset).limit(page_size)
    )
    users = users_result.scalars().all()
    
    return UserListResponse(
        items=[
            UserResponse(
                id=u.id, email=u.email, full_name=u.full_name,
                role=u.role, rate_limit=u.rate_limit, is_active=u.is_active,
                is_verified=u.is_verified, last_login_at=u.last_login_at,
                created_at=u.created_at
            ) for u in users
        ],
        total=total, page=page, page_size=page_size
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin only)."""
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        rate_limit=user_data.rate_limit,
        is_active=user_data.is_active,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete user (admin only)."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}


@router.put("/{user_id}/phones")
async def assign_phones(
    user_id: int,
    device_ids: list[int],
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Assign phones to user (admin only)."""
    # Remove existing assignments
    await db.execute(
        UserPhoneAssignment.__table__.delete().where(
            UserPhoneAssignment.user_id == user_id
        )
    )
    
    # Create new assignments
    for device_id in device_ids:
        assignment = UserPhoneAssignment(user_id=user_id, device_id=device_id)
        db.add(assignment)
    
    await db.commit()
    return {"message": "Phones assigned successfully"}
