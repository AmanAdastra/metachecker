from pydantic import BaseModel
from typing import Any
from enum import Enum
import time

class LeadStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MEETING_SCHEDULED = "meeting_scheduled"
    MEETING_COMPLETED = "meeting_completed"
    
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