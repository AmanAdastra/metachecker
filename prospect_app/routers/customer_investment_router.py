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