from fastapi import APIRouter, Depends, Form, UploadFile, File
from logging_module import logger
from pydantic import EmailStr
from typing import Annotated, Optional
from auth_layer.admin.admin_schemas import admin_property_management_schemas
from auth_layer.admin.admin_services import admin_property_management_service
from auth_layer.prospect.prospect_services import customer_property_service
from common_layer.common_services.utils import valid_content_length
from common_layer.common_services.oauth_handler import oauth2_scheme
from common_layer import constants
from common_layer.common_schemas.property_schema import UpdateCandleDataSchema
from common_layer.common_schemas.property_schema import (
    ResidentialPropertyRequestSchema,
    CommercialPropertyRequestSchema,
    FarmPropertyRequestSchema,
)

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
    tags=["ADMIN PROPERTY MANAGEMENT"],
)


@router.get("/regions")
def get_regions(page_number:int, per_page:int, token: Annotated[str, Depends(oauth2_scheme)], region:Optional[str] = "", status:Optional[str] = ""):
    logger.debug("Inside Add Regions Router")
    response = admin_property_management_service.get_regions(page_number,per_page, region, status, token)
    logger.debug("Returning From the Add Regions Router")
    return response


@router.post("/add-region")
def add_region(
    request: admin_property_management_schemas.AddRegionSchemaRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Region Router")
    response = admin_property_management_service.add_region(request, token)
    logger.debug("Returning From the Add Region Router")
    return response


@router.put("/update-region")
def update_region(
    request: admin_property_management_schemas.UpdateRegionSchemaRequest,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Update Region Router")
    response = admin_property_management_service.update_region(request, token)
    logger.debug("Returning From the Update Region Router")
    return response

@router.put("/update-region-status")
def update_region_status(
    region_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Region Status Router")
    response = admin_property_management_service.deactivate_region(region_id, token)
    logger.debug("Returning From the Update Region Status Router")
    return response


@router.post("/upload-region-icon")
def upload_region_icon(
    region_id: str = Form(...),
    icon_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Upload Region Icon Router")
    response = admin_property_management_service.upload_region_icon(
        region_id, icon_image, token
    )
    logger.debug("Returning From the Upload Region Icon Router")
    return response


@router.put("/update-region-icon")
def update_region_icon(
    region_id: str = Form(...),
    icon_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Update Region Icon Router")
    response = admin_property_management_service.update_region_icon(
        region_id, icon_image, token
    )
    logger.debug("Returning From the Update Region Icon Router")
    return response

@router.get("/property-categories")
def get_property_categories(token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside Get Property Categories Router")
    response = admin_property_management_service.get_property_categories(token)
    logger.debug("Returning From the Get Property Categories Router")
    return response

@router.post("/add-property-category")
def add_property_category(
    request: admin_property_management_schemas.AddPropertyCategoryRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Property Category Router")
    response = admin_property_management_service.add_property_category(request, token)
    logger.debug("Returning From the Add Property Category Router")
    return response

@router.put("/update-property-category")
def update_property_category(
    request: admin_property_management_schemas.UpdatePropertyCategoryRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Property Category Router")
    response = admin_property_management_service.update_property_category(request, token)
    logger.debug("Returning From the Update Property Category Router")
    return response

@router.post("/upload-property-category-icon")
def upload_property_category_icon(
    category_id: str = Form(...),
    icon_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Upload Property Category Icon Router")
    response = admin_property_management_service.upload_property_category_icon(
        category_id, icon_image, token
    )
    logger.debug("Returning From the Upload Property Category Icon Router")
    return response

@router.put("/update-property-category-icon")
def update_property_category_icon(
    category_id: str = Form(...),
    icon_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Update Property Category Icon Router")
    response = admin_property_management_service.update_property_category_icon(
        category_id, icon_image, token
    )
    logger.debug("Returning From the Update Property Category Icon Router")
    return response


@router.post("/set-top-properties")
def set_top_properties(
    request: admin_property_management_schemas.SetTopPropertiesRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Set Top Properties Router")
    response = admin_property_management_service.set_top_properties(request, token)
    logger.debug("Returning From the Set Top Properties Router")
    return response

@router.post("/set-featured-properties")
def set_featured_properties(
    request: admin_property_management_schemas.SetFeaturedPropertiesRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Set Featured Properties Router")
    response = admin_property_management_service.set_featured_properties(request, token)
    logger.debug("Returning From the Set Featured Properties Router")
    return response

@router.post("/set-recommended-properties")
def set_recommended_properties(
    request: admin_property_management_schemas.SetRecommendedPropertiesRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Set Recommended Properties Router")
    response = admin_property_management_service.set_recommended_properties(request, token)
    logger.debug("Returning From the Set Recommended Properties Router")
    return response


@router.post("/add-residential-property")
def add_residential_property(request: ResidentialPropertyRequestSchema, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Add Residential Property Router")
    response = customer_property_service.add_residential_property(request=request, token=token)
    logger.debug("Returning From the Add Residential Property Router")
    return response

@router.put("/update-residential-property")
def update_residential_property(property_id:str, request: ResidentialPropertyRequestSchema, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Update Residential Property Router")
    response = customer_property_service.update_residential_property(property_id=property_id, request=request, token=token)
    logger.debug("Returning From the Update Residential Property Router")
    return response


@router.post("/add-commercial-property")
def add_commercial_property(request :CommercialPropertyRequestSchema , token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Add Commercial Property Router")
    response = customer_property_service.add_commercial_property(request=request, token=token)
    logger.debug("Returning From the Add Commercial Property Router")
    return response

@router.put("/update-commercial-property")
def update_commercial_property(property_id:str, request: CommercialPropertyRequestSchema, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Update Commercial Property Router")
    response = customer_property_service.update_commercial_property(property_id=property_id, request=request, token=token)
    logger.debug("Returning From the Update Commercial Property Router")
    return response

@router.post("/add-farm-property")
def add_farm_property(request :FarmPropertyRequestSchema , token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Add Farm Property Router")
    response = customer_property_service.add_farm_property(request=request, token=token)
    logger.debug("Returning From the Add Farm Property Router")
    return response
    
@router.put("/update-farm-property")
def update_farm_property(property_id:str, request: FarmPropertyRequestSchema, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Update Farm Property Router")
    response = customer_property_service.update_farm_property(property_id=property_id, request=request, token=token)
    logger.debug("Returning From the Update Farm Property Router")
    return response

@router.get("/get-candles-of-property")
def get_candles_of_property(property_id:str):
    logger.debug("Inside Get Candles Of Property Router")
    response = admin_property_management_service.get_candles_of_property(property_id=property_id)
    logger.debug("Returning From the Get Candles Of Property Router")
    return response

@router.put("/set-candles-of-property")
def set_candles_of_property(request: UpdateCandleDataSchema, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Set Candles Of Property Router")
    response = admin_property_management_service.set_candles_of_property(request=request, token=token)
    logger.debug("Returning From the Set Candles Of Property Router")
    return response

@router.get("/get-filter-buttons-list")
def get_filter_buttons_list():
    logger.debug("Inside Add Regions Router")
    response = customer_property_service.get_filter_buttons_list()
    logger.debug("Returning From the Add Regions Router")
    return response

@router.get("/get-property-details")
def get_property_details(property_id:str):
    logger.debug("Inside Get Property Details Router")
    response = customer_property_service.get_property_by_id(property_id=property_id)
    logger.debug("Returning From the Get Property Details Router")
    return response

@router.post("/get-property-list")
def get_property_list(per_page:int, page_number:int, filter_dict:dict, sort_dict:dict):
    logger.debug("Inside Get Property List Router")
    response = customer_property_service.get_property_list(
        per_page=per_page, page_number=page_number,
        filter_dict=filter_dict, sort_dict=sort_dict
    )
    logger.debug("Returning From the Get Property List Router")
    return response