from pydantic import BaseModel
import time
from typing import Any

class ResponseMessage(BaseModel):
    type: str
    data: Any
    status_code: int

class CustomBaseSchema(BaseModel):
    created_at: float = time.time()
    updated_at: float = time.time()

class CustomerConversationInDB(CustomBaseSchema):
    sender_id: str
    reciever_id: str
    property_id: str
    status: str
    messages: list = []

class CustomerConversationRequest(BaseModel):
    property_id: str