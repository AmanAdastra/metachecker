from fastapi import APIRouter, Depends, Form, UploadFile, File
from logging_module import logger
from pydantic import EmailStr
from typing import Annotated, List
from common_layer.common_services.utils import valid_content_length
from common_layer.common_services.oauth_handler import oauth2_scheme
from auth_layer.prospect.prospect_services import customer_leads_management_service

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
    tags=["CUSTOMERS LEADS MANAGEMENT"],
)


@router.get("/get-investors-project")
def get_investors_projects(page_number:int, per_page:int,token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Investors Projects Router")
    response = customer_leads_management_service.get_investors_projects(page_number, per_page, token)
    logger.debug("Returning From the Get Investors Project Router")
    return response

@router.post("/generate-lead-for-property")
def generate_lead_for_property(property_id:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Generate Lead For Property Router")
    response = customer_leads_management_service.generate_lead_for_property(property_id, token)
    logger.debug("Returning From the Generate Lead For Property Router")
    return response

@router.get("/check-already-lead-exist")
def check_already_lead_exist(property_id:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Check Already Lead Exist Router")
    response = customer_leads_management_service.check_already_lead_exist(property_id, token)
    logger.debug("Returning From the Check Already Lead Exist Router")
    return response

@router.get("/get-candle-of-property")
def get_candle_of_property(property_id:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Candle Of Property Router")
    response = customer_leads_management_service.get_candle_of_property(property_id, token)
    logger.debug("Returning From the Get Candle Of Property Router")
    return response

@router.get("/get-investors-leads")
def get_investors_leads(page_number:int, per_page:int, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Investors Leads Router")
    response = customer_leads_management_service.get_investors_leads(page_number, per_page, token)
    logger.debug("Returning From the Get Investors Leads Router")
    return response

@router.get("/get-investors-leads-details")
def get_investors_leads_details(lead_id:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Investors Leads Details Router")
    response = customer_leads_management_service.get_investors_leads_details(lead_id, token)
    logger.debug("Returning From the Get Investors Leads Details Router")
    return response