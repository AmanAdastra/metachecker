from fastapi import APIRouter, Depends, Form, UploadFile, File
from logging_module import logger
from pydantic import EmailStr
from typing import Annotated, List
from common_layer.common_services.utils import valid_content_length
from common_layer.common_services.oauth_handler import oauth2_scheme
from auth_layer.prospect.prospect_services import customer_property_service
from common_layer.common_schemas.property_schema import (
    ResidentialPropertyRequestSchema, 
    CommercialPropertyRequestSchema,
    FarmPropertyRequestSchema
)
router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
    tags=["CUSTOMER PROPERTY MANAGEMENT"],
)


@router.get("/regions-list")
def get_regions():
    logger.debug("Inside Add Regions Router")
    response = customer_property_service.get_regions()
    logger.debug("Returning From the Add Regions Router")
    return response

@router.get("/available-regions")
def get_available_regions_name():
    logger.debug("Inside Add Regions Router")
    response = customer_property_service.get_available_regions_name()
    logger.debug("Returning From the Add Regions Router")
    return response

@router.get("/available-categories")
def get_available_categories_name():
    logger.debug("Inside Add Regions Router")
    response = customer_property_service.get_available_categories_name()
    logger.debug("Returning From the Add Regions Router")
    return response

@router.get("/get-filter-buttons-list")
def get_filter_buttons_list():
    logger.debug("Inside Add Regions Router")
    response = customer_property_service.get_filter_buttons_list()
    logger.debug("Returning From the Add Regions Router")
    return response

# Add Customer Residential Property
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

@router.put("/update-property-view-count")
def update_property_view_count(property_id:str):
    logger.debug("Inside Update Property View Count Router")
    response = customer_property_service.update_property_view_count(property_id=property_id)
    logger.debug("Returning From the Update Property View Count Router")
    return response

# Add Pagination
@router.get("/get-list-of-featured-properties")
def get_list_of_featured_properties(latitude:float, longitude:float, per_page: int, page_number: int):
    logger.debug("Inside Get List of Featured Properties Router")
    response = customer_property_service.get_list_of_featured_properties(latitude=latitude, longitude=longitude, per_page=per_page, page_number=page_number)
    logger.debug("Returning From the Get List of Featured Properties Router")
    return response

# Add Pagination
@router.get("/get-list-of-recommended-properties")
def get_list_of_recommended_properties(per_page: int, page_number: int,latitude:float, longitude:float):
    logger.debug("Inside Get List of Recommended Properties Router")
    response = customer_property_service.get_list_of_recommended_properties(latitude=latitude, longitude=longitude, per_page=per_page, page_number=page_number)
    logger.debug("Returning From the Get List of Recommended Properties Router")
    return response

# Add Pagination
@router.get("/get-list-of-most-viewed-properties")
def get_list_of_most_viewed_properties(per_page: int, page_number: int):
    logger.debug("Inside Get List of Most Viewed Properties Router")
    response = customer_property_service.get_list_of_most_viewed_properties(per_page=per_page, page_number=page_number)
    logger.debug("Returning From the Get List of Most Viewed Properties Router")
    return response

# Add Pagination
@router.get("/get-list-of-top-properties")
def get_list_of_top_properties(latitude:float, longitude:float, per_page: int, page_number: int):
    logger.debug("Inside Get List of Top Properties Router")
    response = customer_property_service.get_list_of_top_properties(latitude=latitude, longitude=longitude, per_page=per_page, page_number=page_number)
    logger.debug("Returning From the Get List of Top Properties Router")
    return response

@router.get("/get-nearby-properties")
def get_nearby_properties(latitude:float, longitude:float, per_page: int, page_number: int):
    logger.debug("Inside Get Nearby Properties Router")
    response = customer_property_service.get_nearby_properties(latitude=latitude, longitude=longitude, per_page=per_page, page_number=page_number)
    logger.debug("Returning From the Get Nearby Properties Router")
    return response

# Property Images
@router.post("/add-property-images")
def add_property_images(property_id:str, images: List[UploadFile] = File(...), token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Add Property Images Router")
    response = customer_property_service.add_property_images(property_id=property_id, images=images, token=token)
    logger.debug("Returning From the Add Property Images Router")
    return response

@router.post("/add-project-logo")
def add_project_logo(property_id:str, logo: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Add Project Logo Router")
    response = customer_property_service.add_project_logo(property_id=property_id, logo=logo, token=token)
    logger.debug("Returning From the Add Project Logo Router")
    return response

@router.get("/get-property-images")
def get_property_images(property_id:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Property Images Router")
    response = customer_property_service.get_property_images(property_id=property_id, token=token)
    logger.debug("Returning From the Get Property Images Router")
    return response

@router.put("/update-property-images")
def update_property_images(property_id:str, images: List[UploadFile] = File(...), token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Update Property Images Router")
    response = customer_property_service.update_property_images(property_id=property_id, images=images, token=token)
    logger.debug("Returning From the Update Property Images Router")
    return response

@router.get("/get-property-by-id")
def get_property_by_id(property_id:str):
    logger.debug("Inside Get Property By Id Router")
    response = customer_property_service.get_property_by_id(property_id=property_id)
    logger.debug("Returning From the Get Property By Id Router")
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

@router.post("/upload-property-documents")
def upload_brochure_or_project_document(property_id:str,type:str,document_title:str, document: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Upload Property Documents Router")
    response = customer_property_service.upload_brochure_or_project_document(
        property_id=property_id, type=type, document_title=document_title, document=document, token=token
    )
    logger.debug("Returning From the Upload Property Documents Router")
    return response


@router.get("/get-top-gainers")
def get_top_gainers():
    logger.debug("Inside Get Top Gainers Router")
    response = customer_property_service.get_top_gainers()
    logger.debug("Returning From the Get Top Gainers Router")
    return response

@router.get("/get-similar-properties")
def get_similar_properties(region_id:str, page_number:int, per_page:int):
    logger.debug("Inside Get Similar Properties Router")
    response = customer_property_service.get_similar_properties(region_id=region_id, page_number=page_number, per_page=per_page)
    logger.debug("Returning From the Get Similar Properties Router")
    return response

@router.put("/change-property-status")
def change_property_status(property_id:str, status:str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Change Property Status Router")
    response = customer_property_service.change_property_status(property_id=property_id, status=status, token=token)
    logger.debug("Returning From the Change Property Status Router")
    return response