from datetime import datetime
import re

from pydantic import BaseModel, field_validator, model_validator


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class CredentialsRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value:
            raise ValueError("Password is required.")
        return value


class RegisterRequest(CredentialsRequest):
    full_name: str
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Full name is required.")
        if len(normalized) > 120:
            raise ValueError("Full name must be 120 characters or fewer.")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_registration_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class ProfileUpdateRequest(BaseModel):
    full_name: str

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Full name is required.")
        if len(normalized) > 120:
            raise ValueError("Full name must be 120 characters or fewer.")
        return normalized


class DemoLoginRequest(BaseModel):
    email: str = "demo@medicalcost.local"


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    is_demo: bool
    role: str
    account_type: str
    created_at: datetime


class AuthResponse(UserResponse):
    access_token: str
