from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserBase(BaseModel):
    username: str
    email: EmailStr
    
class UserCreate(UserBase):
    password: str
    
    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")

        elif not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")

        elif not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter")

        elif not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")

        return value
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserOut(UserBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)