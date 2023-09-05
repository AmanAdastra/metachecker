from fastapi import APIRouter, Depends, Form, UploadFile, File
from logging_module import logger
from pydantic import EmailStr
from typing import Annotated
from auth_layer.admin.admin_schemas import ads_management_schemas
from auth_layer.admin.admin_services import admin_ads_management_service
from common_layer.common_services.utils import valid_content_length
from common_layer.common_services.oauth_handler import oauth2_scheme
from common_layer import constants

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
    tags=["ADMIN ADS MANAGEMENT"],
)


@router.get("/get-welcome-card-info")
def get_welcome_card_info(token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside Get Welcome Card Info Router")
    response = admin_ads_management_service.get_welcome_card_info()
    logger.debug("Returning From the Get Welcome Card Info Router")
    return response

@router.get("/get-ads-info")
def get_ads_info(token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside Get Ads Info Router")
    response = admin_ads_management_service.get_ads_card_info()
    logger.debug("Returning From the Get Ads Info Router")
    return response

@router.get("/get-cta-card-info")
def get_cta_card_info(token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside Get CTA Info Router")
    response = admin_ads_management_service.get_cta_card_info()
    logger.debug("Returning From the Get CTA Info Router")
    return response

@router.post("/add-welcome-card")
def add_welcome_card(
    request: ads_management_schemas.AddWelcomeCardRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Welcome Card Router")
    response = admin_ads_management_service.add_welcome_card(request, token)
    logger.debug("Returning From the Add Welcome Card Router")
    return response

@router.post("/add-ads-card")
def add_ads_card(
    request: ads_management_schemas.AddAdsCardRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Ads Card Router")
    response = admin_ads_management_service.add_ads_card(request, token)
    logger.debug("Returning From the Add Ads Card Router")
    return response

@router.post("/add-cta-card")
def add_cta_card(
    request: ads_management_schemas.AddCTARequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add CTA Router")
    response = admin_ads_management_service.add_cta_card(request, token)
    logger.debug("Returning From the Add CTA Router")
    return response

@router.put("/update-welcome-card")
def update_welcome_card(
    request: ads_management_schemas.UpdateWelcomeCardRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Welcome Card Router")
    response = admin_ads_management_service.update_welcome_card(request, token)
    logger.debug("Returning From the Update Welcome Card Router")
    return response

@router.put("/update-ads-card")
def update_ads_card(
    request: ads_management_schemas.UpdateAdsRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Ads Card Router")
    response = admin_ads_management_service.update_ads_card(request, token)
    logger.debug("Returning From the Update Ads Card Router")
    return response

@router.put("/update-cta-card")
def update_cta_card(
    request: ads_management_schemas.UpdateCTARequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update CTA Router")
    response = admin_ads_management_service.update_cta_card(request, token)
    logger.debug("Returning From the Update CTA Router")
    return response


@router.post("/upload-welcome-card-image")
def upload_welcome_card_image(
    card_id: str = Form(...),
    welcome_card_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Upload Welcome Card Image Router")
    response = admin_ads_management_service.upload_welcome_card_image(
        card_id, welcome_card_image, token
    )
    logger.debug("Returning From the Upload Welcome Card Image Router")
    return response

@router.post("/upload-ads-image")
def upload_ads_image(
    card_id: str = Form(...),
    ads_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Upload Ads Image Router")
    response = admin_ads_management_service.upload_ads_card_image(
        card_id, ads_image, token
    )
    logger.debug("Returning From the Upload Ads Image Router")
    return response

@router.post("/upload-cta-card-image")
def upload_cta_card_image(
    card_id: str = Form(...),
    cta_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Upload CTA Image Router")
    response = admin_ads_management_service.upload_cta_card_image(
        card_id, cta_image, token
    )
    logger.debug("Returning From the Upload CTA Image Router")
    return response

@router.put("/update-welcome-card-image")
def update_welcome_card_image(
    card_id: str = Form(...),
    welcome_card_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Update Welcome Card Image Router")
    response = admin_ads_management_service.update_welcome_card_image(
        card_id, welcome_card_image, token
    )
    logger.debug("Returning From the Update Welcome Card Image Router")
    return response

@router.put("/update-ads-image")
def update_ads_image(
    card_id: str = Form(...),
    ads_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Update Ads Image Router")
    response = admin_ads_management_service.update_ads_card_image(
        card_id, ads_image, token
    )
    logger.debug("Returning From the Update Ads Image Router")
    return response

@router.put("/update-cta-card-image")
def update_cta_card_image(
    card_id: str = Form(...),
    cta_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Update CTA Image Router")
    response = admin_ads_management_service.update_cta_card_image(
        card_id, cta_image, token
    )
    logger.debug("Returning From the Update CTA Image Router")
    return response