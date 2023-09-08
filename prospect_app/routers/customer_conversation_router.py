from fastapi import APIRouter, Depends, Form, UploadFile, File
from logging_module import logger
from pydantic import EmailStr
from typing import Annotated, List
from common_layer.common_services.utils import valid_content_length
from common_layer.common_services.oauth_handler import oauth2_scheme
from auth_layer.prospect.prospect_services import customer_conversation_service

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
    tags=["CUSTOMER CONVERSATION MANAGEMENT"],
)

@router.get("/get-customer-conversation")
def get_user_wallet(page_number:int, per_page:int, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get User Wallet Router")
    response = customer_conversation_service.get_customer_conversations(page_number, per_page, token)
    logger.debug("Returning From the Get User Wallet Router")
    return response