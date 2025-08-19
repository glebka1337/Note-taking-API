"""
Here will be auth service
"""
from fastapi import Depends, HTTPException, Header, status
import jwt
from api.auth.schemas import UserCreate, UserLogin, UserOut
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from api.auth.security import get_password_hash, verify_password
from api.config import settings
from api.db import get_session
from api.models import User
from redis.asyncio import Redis
from typing import Annotated
from api.auth.services.jwt_service import validate_refresh_token
from api.redis_client import get_redis

async def create_new_user(
    db: AsyncSession,
    user_in: UserCreate
) -> User:
    """
    Create new user

    Args:
        db (AsyncSession): connect to database
        user_in (UserCreate): user to create

    Raises:
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        User: _description_
    """
    user_in_db = await db.execute(
        select(User).where(
            or_(
                User.email == user_in.email,
                User.username == user_in.username
            )
        )
    )
    if user_in_db := user_in_db.scalar_one_or_none():
        if user_in_db.email == user_in.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        if user_in_db.username == user_in.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
    user = User(
        username=user_in.username,
        email=user_in.email
    )
    user.hashed_password = get_password_hash(user_in.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def login_user(
    user_login: UserLogin,
    db: AsyncSession
) -> UserOut:
    """
    Login user

    Args:
        user_login (UserLogin): user to login
        db (AsyncSession): connect to database

    Raises:
        HTTPException: if email or password is incorrect

    Returns:
        UserOut: pydantic model of user
    """    
    user_in_db = await db.execute(
        select(User).where(
            User.email == user_login.email
        )
    )
    
    user = user_in_db.scalar_one_or_none()
    detail="Incorrect email or password"
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
    if not verify_password(
        plain_password=user_login.password,
        hashed_password=user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
    return UserOut(**user.model_dump())

async def get_current_user(
    access_token: str = Header(..., alias="Authorization"),
    redis_client: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_session)
) -> UserOut:
    
    if not access_token.startswith("Bearer "):
        raise HTTPException(400, "Invalid token format")
    
    try:
        payload = jwt.decode(
            access_token.split(" ")[1],
            settings.secret_key,
            algorithms=settings.algorithm
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    
    
    if user_data := await redis_client.get(f"user:{payload['user_id']}"):
        return UserOut.model_validate_json(user_data)
    
    user = await db.get(User, payload["user_id"])
    if not user:
        raise HTTPException(404, "User not found")
    
    await redis_client.set(
        f"user:{user.id}",
        user.model_dump_json(),
        ex=3600
    )
    return UserOut.model_validate(user)