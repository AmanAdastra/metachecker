from pydantic import BaseModel
from typing import Any
import time

class CustomBaseSchema(BaseModel):
    created_at: float = time.time()
    updated_at: float = time.time()

class ResponseMessage(BaseModel):
    type: str
    data: Any
    status_code: int

class CustomerLeadsInDB(CustomBaseSchema):
    user_id: str
    listed_by_user_id: str
    property_id: str
    status: str