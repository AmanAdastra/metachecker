import time
from typing import Any
from pydantic import BaseModel, validator, Field


class ResponseMessage(BaseModel):
    type: str
    data: Any
    status_code: int


class AddWelcomeCardRequest(BaseModel):
    title: str
    cta_text: str
    video_url: str

class AddAdsCardRequest(BaseModel):
    title: str
    cta_text: str
    cta_url: str

class AddCTARequest(BaseModel):
    title: str
    description: str
    cta_text: str
    cta_url: str

class WelcomeCardInDB(AddWelcomeCardRequest):
    welcome_card_image: str
    created_at: float = time.time()
    updated_at: float = time.time()

class AdsInDB(AddAdsCardRequest):
    ads_card_image: str = ""
    created_at: float = time.time()
    updated_at: float = time.time()

class CTAInDB(AddCTARequest):
    cta_image: str = ""
    created_at: float = time.time()
    updated_at: float = time.time()


class UpdateWelcomeCardRequest(BaseModel):
    card_id: str
    title: str
    cta_text: str
    video_url: str

class UpdateAdsRequest(BaseModel):
    card_id: str
    title: str
    cta_text: str
    cta_url: str

class UpdateCTARequest(BaseModel):
    card_id: str
    title: str
    description: str
    cta_text: str
    cta_url: str

class UpdateWelcomeCardInDB(UpdateWelcomeCardRequest):
    updated_at: float = time.time()
    card_id: str = Field(exclude=True)

class UpdateAdsInDB(UpdateAdsRequest):
    updated_at: float = time.time()
    card_id: str = Field(exclude=True)

class UpdateCTAInDB(UpdateCTARequest):
    updated_at: float = time.time()
    card_id: str = Field(exclude=True)
