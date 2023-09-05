import time
from typing import Any
from pydantic import BaseModel, validator, Field
from enum import Enum



class ResponseMessage(BaseModel):
    type: str
    data: Any
    status_code: int
class AddRegionSchemaRequest(BaseModel):
    title: str
    description: str
    latitude: float
    longitude: float


    @validator("latitude")
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @validator("longitude")
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @validator("title")
    def validate_region_title(cls, v):
        if len(str(v)) < 3:
            raise ValueError("Region Title must be atleast 3 characters long")
        return v

class AddRegionsInDBSchema(BaseModel):
    title: str
    description: str
    is_active: bool = True
    icon_image_key: str
    location: dict
    top_properties: list[str] = []
    featured_properties: list[str] = []
    recommended_properties: list[str] = []
    created_at: float = time.time()
    updated_at: float = time.time()
    

class UpdateRegionSchemaRequest(BaseModel):
    id: str
    title: str
    description: str
    latitude: float
    longitude: float
    is_active: bool
    updated_at: float = time.time()

    @validator("latitude")
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @validator("longitude")
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @validator("title")
    def validate_region_title(cls, v):
        if len(str(v)) < 3:
            raise ValueError("Region Title must be atleast 3 characters long")
        return v
    
class AddPropertyCategoryRequest(BaseModel):
    title: str
    description: str
    

    @validator("title")
    def validate_category_title(cls, v):
        if len(str(v)) < 3:
            raise ValueError("Category Title must be atleast 3 characters long")
        return v
    
class AddPropertyCategoryInDBSchema(AddPropertyCategoryRequest):
    is_active: bool = True
    icon_image_key: str
    created_at: float = time.time()
    updated_at: float = time.time()

class UpdatePropertyCategoryRequest(BaseModel):
    id: str
    title: str
    description: str
    is_active: bool
    updated_at: float = time.time()

    @validator("title")
    def validate_category_title(cls, v):
        if len(str(v)) < 3:
            raise ValueError("Category Title must be atleast 3 characters long")
        return v
    
class UpdatePropertyCategoryInDBSchema(UpdatePropertyCategoryRequest):
    updated_at: float = time.time()


class SetTopPropertiesRequest(BaseModel):
    property_ids: list[str]
    region_id: str
    updated_at: float = time.time()

class SetRecommendedPropertiesRequest(BaseModel):
    property_ids: list[str]
    region_id: str
    updated_at: float = time.time()


class SetFeaturedPropertiesRequest(BaseModel):
    property_ids: list[str]
    region_id: str
    updated_at: float = time.time()