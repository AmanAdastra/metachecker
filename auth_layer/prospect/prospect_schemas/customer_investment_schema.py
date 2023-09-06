from pydantic import BaseModel
import time

class BuyInvestmentQuantityRequest(BaseModel):
    property_id: str
    quantity: float


class CustomerSharesInDb(BaseModel):
    quantity: float
    avg_price: float
    investment_value: float
    created_at: float = time.time()
    updated_at: float = time.time()


class CustomerTransactionSchemaInDB(BaseModel):
    user_id: str
    property_id: str
    transaction_type: str
    transaction_amount: float
    transaction_quantity: float
    transaction_avg_price: float
    transaction_id: str
    transaction_status: str
    transaction_date: float = time.time()
    created_at: float = time.time()
    updated_at: float = time.time()
