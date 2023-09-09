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
def get_user_wallet(page_number:int, per_page:int,type:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get User Wallet Router")
    response = customer_conversation_service.get_customer_conversations(page_number, per_page,type, token)
    logger.debug("Returning From the Get User Wallet Router")
    return response

@router.get("/get-customer-conversation-by-id")
def get_user_wallet(conversation_id:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get User Wallet Router")
    response = customer_conversation_service.get_customer_conversation_by_id(conversation_id, token)
    logger.debug("Returning From the Get User Wallet Router")
    return response

@router.post("/add-customer-conversation")
def add_customer_conversation(property_id:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Add Customer Conversation Router")
    response = customer_conversation_service.add_customer_conversation(property_id, token)
    logger.debug("Returning From the Add Customer Conversation Router")
    return response

@router.post("/chat-with-customer")
def chat_with_customer(
    conversation_id:str,
    message:str,
    token: str = Depends(oauth2_scheme)
):
    logger.debug("Inside Add Customer Message Router")
    response = customer_conversation_service.chat_with_customer(conversation_id, message, token)
    logger.debug("Returning From the Add Customer Message Router")
    return response

@router.put("/close-customer-conversation")
def close_customer_conversation(
    conversation_id:str,
    token: str = Depends(oauth2_scheme)
):
    logger.debug("Inside Close Customer Conversation Router")
    response = customer_conversation_service.close_customer_conversation(conversation_id, token)
    logger.debug("Returning From the Close Customer Conversation Router")
    return response

@router.get("/get-list-of-closed-customer-conversation")
def get_list_of_closed_customer_conversation(page_number:int, per_page:int, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get List Of Closed Customer Conversation Router")
    response = customer_conversation_service.get_list_of_closed_customer_conversation(page_number, per_page, token)
    logger.debug("Returning From the Get List Of Closed Customer Conversation Router")
    return response