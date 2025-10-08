import re

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        title="Username",
        description="Unique username (letters, digits, underscores only).",
        examples=["johndoe_123"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        title="Password",
        description="User password (must contain upper, lower, digit, and special character).",
        examples=["StrongPass!23"],
    )

    @field_validator("username")
    def validate_username(cls, value: str) -> str:
        if not re.match(r"^[A-Za-z0-9_]+$", value):
            raise ValueError(
                "Username may contain only letters, digits, and underscores."
            )
        return value

    @field_validator("password")
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character.")
        return value


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        title="Username",
        description="Registered username.",
        examples=["johndoe"],
    )
    password: str = Field(
        ...,
        title="Password",
        description="User password (plaintext, will be verified against hash).",
        examples=["StrongPass!23"],
    )


class LoginResponse(BaseModel):
    token: str = Field(
        ...,
        title="JWT Access Token",
        description="JWT token used for authenticated requests.",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
