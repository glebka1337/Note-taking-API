"""
Here will be auth service
"""
from fastapi import HTTPException, status
from api.auth.schemas import UserCreate, UserLogin, UserOut
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from api.auth.security import get_password_hash, verify_password
from api.models import User

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
    user = User(**user_in.model_dump())
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