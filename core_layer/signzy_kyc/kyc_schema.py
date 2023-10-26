from pydantic import BaseModel


class DigilockerVerificationRequest(BaseModel):
    request_id: str
    pan_number : str
    name : str
    uid : str