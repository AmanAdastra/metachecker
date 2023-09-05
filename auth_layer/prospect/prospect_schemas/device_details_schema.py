from pydantic import BaseModel
import time

class DeviceDetailsInput(BaseModel):
    device_id : str = None
    device_token: str = None

class DeviceDetails(DeviceDetailsInput):
    user_id: str
    created_at: float = time.time()
    updated_at: float = time.time()