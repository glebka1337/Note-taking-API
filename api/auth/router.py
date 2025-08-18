from fastapi import APIRouter, HTTPException, status, Depends
from api.db import get_session

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/register")
async def register():
    ...

@router.post("/login")
async def login():
    ...

@router.post("/logout")    
async def logout():
    ...
    
@router.post("/refresh")
async def refresh_access_token():
    ...