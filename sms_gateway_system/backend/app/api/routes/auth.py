"""
Authentication API routes.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.models import User, ActivityLog
from app.schemas.schemas import (
    LoginRequest, SignupRequest, TokenResponse, UserResponse, TokenRefreshRequest
)
from app.utils.auth import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, decode_token
)
from app.core.config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    token_use: str = payload.get("token_use")
    
    if token_use != "access" or user_id is None:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
    client_ip: str = Depends(lambda r: r.client.host if r.client else "unknown"),
):
    """
    Create first super admin account.
    
    This endpoint should only be used once to create the initial super admin.
    Subsequent users should be created by admins through the user management interface.
    """
    # Check if any users exist
    result = await db.execute(select(User))
    existing_users = result.scalars().all()
    
    # If users exist, prevent direct signup (should use admin interface)
    if existing_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Signup is only available for the first super admin. Please contact an administrator."
        )
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create super admin user
    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        full_name=request.full_name,
        role="super_admin",
        rate_limit=settings.ADMIN_RATE_LIMIT,
        is_active=True,
        is_verified=True,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Log activity
    activity_log = ActivityLog(
        user_id=user.id,
        action="USER_SIGNUP",
        resource_type="user",
        resource_id=user.id,
        ip_address=client_ip,
        metadata={"role": "super_admin"}
    )
    db.add(activity_log)
    await db.commit()
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    client_ip: str = Depends(lambda r: r.client.host if r.client else "unknown"),
):
    """
    Authenticate user and return access/refresh tokens.
    
    Uses OAuth2 password flow for compatibility with standard auth clients.
    """
    # Find user by email (username field in form)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "email": user.email}
    )
    
    # Log activity
    activity_log = ActivityLog(
        user_id=user.id,
        action="USER_LOGIN",
        resource_type="user",
        resource_id=user.id,
        ip_address=client_ip,
    )
    db.add(activity_log)
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)
    
    if payload is None or payload.get("token_use") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.id, "email": user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information."""
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user (client should discard tokens).
    
    Note: In a stateless JWT system, logout is handled client-side
    by discarding tokens. For token blacklisting, consider using Redis.
    """
    # Log activity
    activity_log = ActivityLog(
        user_id=current_user.id,
        action="USER_LOGOUT",
        resource_type="user",
        resource_id=current_user.id,
    )
    db.add(activity_log)
    await db.commit()
    
    return {"message": "Successfully logged out"}
