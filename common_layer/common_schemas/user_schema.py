from pydantic import BaseModel, EmailStr, Field, validator
from typing import Any
import time
from enum import Enum

class UserTypes(str, Enum):
    CUSTOMER = "customer"
    PARTNER = "partner"
    SUPER_ADMIN = "super_admin"
    STAFF = "staff"



class PasscodeDetails(BaseModel):
    email_id: EmailStr
    email_otp: str


class MobileOtpDetails(BaseModel):
    mobile_number: str
    mobile_otp: str


class RegisterRequest(BaseModel):
    legal_name: str
    email_id: EmailStr
    password: str
    password_confirmed: str
    mobile_number: str
    user_type: str

    @validator("mobile_number")
    def validate_mobile_number(cls, value):
        if len(value) != 12:
            raise ValueError("Mobile Number Must Be Twelve Digits")
        if not str(value).startswith("91"):
            raise ValueError("Mobile Number Must Start with 91")
        if not str(value).isnumeric():
            raise ValueError("Mobile Number Must Be Numeric")
        return value
    
    @validator("user_type")
    def validate_user_type(cls, value):
        if value not in [user_type.value for user_type in UserTypes]:
            raise ValueError("Invalid User Type. Must be one of customer, admin, super_admin, staff")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "mobile_number": "919999999999",
                "legal_name": "John Doe",
                "email_id": "johndoe@mailinator.com",
                "password": "Test@123",
                "password_confirmed": "Test@123",
                "user_type": "customer",
            }
        }


class Register(RegisterRequest):
    username: str
    is_active: bool = True
    kyc_verified: bool = False
    created_at: float = time.time()
    updated_at: float = time.time()
    last_login_at: float = time.time()
    secure_pin: str = None
    password_confirmed: str = Field(exclude=True)
    profile_picture_uploaded: bool = False
    secure_pin_set: bool = False

class ResponseMessage(BaseModel):
    type: str
    data: Any
    status_code: int


class UserWallet(BaseModel):
    user_id: str
    balance: float = 0.0
    created_at: float = time.time()
    updated_at: float = time.time()


class UserLogin(BaseModel):
    mobile_number: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {"mobile_number": "919999999999", "password": "Test@123"}
        }

class AdminUserLogin(BaseModel):
    email_id: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {"email_id": "johndoe@mailinator.com", "password": "Test@123"}
        }