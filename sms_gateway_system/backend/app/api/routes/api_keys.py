"""
API Key management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.models import APIKey, User
from app.schemas.schemas import APIKeyCreate, APIKeyResponse, APIKeyWithSecret, APIKeyListResponse
from app.utils.auth import generate_api_key, get_key_prefix
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=APIKeyListResponse)
async def list_api_keys(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's API keys."""
    offset = (page - 1) * page_size
    
    count_result = await db.execute(
        select(func.count(APIKey.id)).where(APIKey.user_id == current_user.id)
    )
    total = count_result.scalar() or 0
    
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id)
        .offset(offset).limit(page_size)
    )
    keys = result.scalars().all()
    
    return APIKeyListResponse(
        items=[
            APIKeyResponse(
                id=k.id, name=k.name, key_prefix=k.key_prefix,
                permissions=k.permissions, rate_limit=k.rate_limit,
                is_active=k.is_active, expires_at=k.expires_at,
                last_used_at=k.last_used_at, created_at=k.created_at
            ) for k in keys
        ],
        total=total, page=page, page_size=page_size
    )


@router.post("/", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new API key."""
    api_key, key_hash = generate_api_key()
    
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    api_key_obj = APIKey(
        user_id=current_user.id,
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=get_key_prefix(api_key),
        permissions=key_data.permissions,
        rate_limit=key_data.rate_limit,
        expires_at=expires_at,
    )
    
    db.add(api_key_obj)
    await db.commit()
    await db.refresh(api_key_obj)
    
    return APIKeyWithSecret(
        id=api_key_obj.id, name=api_key_obj.name,
        key_prefix=api_key_obj.key_prefix, permissions=api_key_obj.permissions,
        rate_limit=api_key_obj.rate_limit, is_active=api_key_obj.is_active,
        expires_at=api_key_obj.expires_at, last_used_at=api_key_obj.last_used_at,
        created_at=api_key_obj.created_at, api_key=api_key
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke API key."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    await db.delete(key)
    await db.commit()
    
    return {"message": "API key revoked"}
