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
    banking_name: str
    account_number : str
    ifsc_code : str
    is_primary: bool

class UpdateBankDetailsSchema(BankDetails):
    record_id:str