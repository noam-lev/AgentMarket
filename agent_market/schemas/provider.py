from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ProviderRegister(BaseModel):
    """
    Pydantic schema for new provider registration requests.
    Defines the required fields and their validation rules for incoming data.
    """
    name: str = Field(..., min_length=3, max_length=100, description="Organization or individual name.")
    email: EmailStr = Field(..., description="Unique email address for the provider.")
    password: str = Field(..., min_length=8, description="Secure password for the provider account (will be hashed).")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Global AI Services Inc.",
                "email": "info@globalaiservices.com",
                "password": "SuperSecurePass123!"
            }
        }
    }

class ProviderLogin(BaseModel):
    """
    Pydantic schema for provider login requests.
    """
    email: EmailStr = Field(..., description="Provider's email address for login.")
    password: str = Field(..., description="Provider's password for login.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "info@globalaiservices.com",
                "password": "SuperSecurePass123!"
            }
        }
    }

class ProviderInDB(BaseModel):
    """
    Pydantic schema representing a Provider document as stored in MongoDB.
    Uses 'id' as an alias for MongoDB's '_id' for convenience.
    """
    id: Optional[str] = Field(alias="_id", default=None, description="MongoDB ObjectId as a string.")
    name: str
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of provider creation.")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last update.")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()},
        "arbitrary_types_allowed": True
    }

class ProviderOut(BaseModel):
    """
    Pydantic schema for provider data returned in API responses.
    Excludes sensitive information like the password hash.
    """
    id: str = Field(..., description="Unique identifier of the provider.")
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = {
        "json_encoders": {datetime: lambda dt: dt.isoformat()}
    }
