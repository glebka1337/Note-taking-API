from passlib.context import CryptContext
from typing import Annotated
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(
    plain_password: Annotated[str, "Password to verify"],
    hashed_password: Annotated[str, "Hashed password"]
) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(
    password: Annotated[str, "Password to hash"]
) -> str:
    return pwd_context.hash(password)