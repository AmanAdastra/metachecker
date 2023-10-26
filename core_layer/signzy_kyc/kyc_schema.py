from pydantic import BaseModel


class DigilockerVerificationRequest(BaseModel):
    request_id: str

class AccountTransfer(BaseModel):
    bank_account: str
    bank_ifsc: str

class VerifyTransfer(BaseModel):
    amount: float
    signzyId: str

class BankDetails(BaseModel):
    account_number : str
    ifsc_code : str