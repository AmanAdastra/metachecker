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
def get_investors_projects(token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Investors Projects Router")
    response = customer_leads_management_service.get_investors_projects(token)
    logger.debug("Returning From the Get Investors Project Router")
    return response