"""Pydantic models: request validation and response shapes."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

PHONE_PATTERN = r"^\+?[0-9\s\-]{7,15}$"


class StudentBase(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["Aarav Sharma"])
    date_of_birth: date = Field(examples=["2004-05-17"])
    email: Optional[EmailStr] = Field(default=None, examples=["aarav@example.com"])
    phone: Optional[str] = Field(default=None, pattern=PHONE_PATTERN, examples=["+91 98765 43210"])
    course: Optional[str] = Field(default=None, max_length=100, examples=["B.Tech CSE"])
    address: Optional[str] = Field(default=None, max_length=255)
    enrollment_date: Optional[date] = None

    @field_validator("name", check_fields=False)
    @classmethod
    def clean_name(cls, v):
        if v is None:
            raise ValueError("name cannot be null")
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("name must have at least 2 characters")
        return v

    @field_validator("date_of_birth", check_fields=False)
    @classmethod
    def dob_not_future(cls, v):
        if v is None:
            raise ValueError("date_of_birth cannot be null")
        if v > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return v

    @field_validator("email", check_fields=False)
    @classmethod
    def lower_email(cls, v):
        return v.lower() if v else v


class StudentCreate(StudentBase):
    """Used for POST and PUT. At least one contact method is required."""

    @model_validator(mode="after")
    def need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("Provide at least one contact: email and/or phone")
        return self


class StudentUpdate(StudentBase):
    """Used for PATCH: every field is optional."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None


class StudentOut(StudentBase):
    id: int


class AIQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=500, examples=["How many students are there?"])


class AIAnswer(BaseModel):
    question: str
    answer: str
    model: str
    filters_applied: dict
    records_used: int
