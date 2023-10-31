from fastapi import APIRouter, Depends, Form, UploadFile, File
from logging_module import logger
from pydantic import EmailStr
from typing import Annotated, List
from common_layer.common_services.utils import valid_content_length
from common_layer.common_services.oauth_handler import oauth2_scheme
from auth_layer.prospect.prospect_services import customer_investment_service

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
    tags=["CUSTOMER INVESTMENT MANAGEMENT"],
)


@router.get("/user-wallet")
def get_user_wallet(token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get User Wallet Router")
    response = customer_investment_service.get_user_wallet(token=token)
    logger.debug("Returning From the Get User Wallet Router")
    return response

@router.post("/add-balance")
def add_balance(token: str = Depends(oauth2_scheme), amount: float = Form(...)):
    logger.debug("Inside Add Balance Router")
    response = customer_investment_service.add_balance(token=token, amount=amount)
    logger.debug("Returning From the Add Balance Router")
    return response

@router.post("/withdraw-balance")
def withdraw_balance(token: str = Depends(oauth2_scheme), amount: float = Form(...)):
    logger.debug("Inside Withdraw Balance Router")
    response = customer_investment_service.withdraw_balance(token=token, amount=amount)
    logger.debug("Returning From the Withdraw Balance Router")
    return response

@router.post("/buy-investment-share")
def buy_investment_quanity(token: str = Depends(oauth2_scheme), quantity: int = Form(...), property_id: str = Form(...)):
    logger.debug("Inside Buy Investment Share Router")
    response = customer_investment_service.buy_investment_share(token=token, quantity=quantity, property_id=property_id)
    logger.debug("Returning From the Buy Investment Share Router")
    return response

@router.post("/sell-investment-share")
def sell_investment_quanity(token: str = Depends(oauth2_scheme), quantity: int = Form(...), property_id: str = Form(...)):
    logger.debug("Inside Sell Investment Share Router")
    response = customer_investment_service.sell_investment_share(token=token, quantity=quantity, property_id=property_id)
    logger.debug("Returning From the Sell Investment Share Router")
    return response


@router.get("/get-transaction-details-by-id")
def get_transaction_details_by_id(transaction_id: str,token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Transaction Details By Id Router")
    response = customer_investment_service.get_transaction_details_by_id(token=token, transaction_id=transaction_id)
    logger.debug("Returning From the Get Transaction Details By Id Router")
    return response

@router.get("/get-customers-transactions")
def get_customers_transactions(token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Customers Transactions Router")
    response = customer_investment_service.get_customers_transactions(token=token)
    logger.debug("Returning From the Get Customers Transactions Router")
    return response


@router.get("/get-property-current-wallet-value")
def get_property_current_wallet_value(property_id: str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Property Current Wallet Value Router")
    response = customer_investment_service.get_property_current_wallet_value(token=token, property_id=property_id)
    logger.debug("Returning From the Get Property Current Wallet Value Router")
    return response

@router.get("/get-investment-progress-details")
def get_investment_progress_details(property_id: str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Investment Progress Details Router")
    response = customer_investment_service.get_investment_progress_details(token=token, property_id=property_id)
    logger.debug("Returning From the Get Investment Progress Details Router")
    return response

@router.get("/get-property-order-history")
def get_property_order_history(page_number:int, per_page:int,property_id:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Property Order History Router")
    response = customer_investment_service.get_property_order_history(
        token=token, property_id=property_id, page_number=page_number, per_page=per_page
    )
    logger.debug("Returning From the Get Property Order History Router")
    return response

@router.get("/get-fiat-transaction-history")
def get_fiat_transaction_history(page_number:int, per_page:int, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Customer Fiat Transaction  Router")
    response = customer_investment_service.get_customer_fiat_transactions(
        page_number=page_number, per_page=per_page, token=token
    )
    logger.debug("Returning From the Geet Customer Fiat Transaction Service")
    return response