from pydantic import BaseModel


class DigilockerVerificationRequest(BaseModel):
    request_id: str