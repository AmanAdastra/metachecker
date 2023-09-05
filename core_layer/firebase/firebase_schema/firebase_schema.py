from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PushNotificationFirebase(BaseModel):
    to : str
    title : str
    description : str
    is_scheduled: bool
    scheduled_time : Optional[str]