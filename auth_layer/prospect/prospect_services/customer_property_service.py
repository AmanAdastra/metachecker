import time
from datetime import datetime
from database import db
from bson import ObjectId
from common_layer import constants
from http import HTTPStatus
from admin_app.logging_module import logger
from fastapi.encoders import jsonable_encoder
from fastapi import Depends, UploadFile
from typing import Annotated
from bson.son import SON
from common_layer.common_services.utils import (
    token_decoder,
    upload_image,
    get_nearest_region_id,
    upload_pdf,
)
from common_layer.common_schemas.user_schema import UserTypes
from auth_layer.admin.admin_schemas import admin_property_management_schemas
from common_layer.common_services.oauth_handler import oauth2_scheme
from core_layer.aws_s3 import s3
from core_layer.aws_cloudfront import core_cloudfront
from common_layer.common_schemas.property_schema import (
    ListingType,
    ListedBy,
    PossessionType,
    Category,
    ResidentialType,
    Furnishing,
    Facing,
    PropertySubCategory,
    ResidentialPropertyRequestSchema,
    ResidentialPropertySchema,
    PropertySchema,
    LocationSchema,
    CandleDataSchema,
    CommercialPropertyRequestSchema,
    CommercialPropertySchema,
    FarmPropertyRequestSchema,
    FarmPropertySchema,
    PropertyStatus,
    PropertyAnalyticsSchema,
    PropertyDailyViewCountSchema,
)


def get_regions():
    logger.debug("Inside Get Regions Service")
    try:
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        regions = list(
            region_collection.find(
                {constants.IS_ACTIVE_FIELD: True},
                {
                    constants.INDEX_ID: 1,
                    constants.ICON_IMAGE_FIELD: 1,
                    constants.TITLE_FIELD: 1,
                },
            ).sort(constants.CREATED_AT_FIELD, -1)
        )
        response_regions = []
        for region in regions:
            region[constants.ID] = str(region[constants.INDEX_ID])
            region[constants.TITLE_FIELD] = region[constants.TITLE_FIELD].title()
            region["listed_properties_count"] = db[
                constants.PROPERTY_DETAILS_SCHEMA
            ].count_documents(
                {
                    constants.REGION_ID_FIELD: str(region[constants.INDEX_ID]),
                }
            )
            region["icon_image_url"] = core_cloudfront.cloudfront_sign(
                region[constants.ICON_IMAGE_FIELD]
            )
            # Get maximum area of all properties in the region
            max_doc_info = list(
                db[constants.PROPERTY_DETAILS_SCHEMA].aggregate(
                    [
                        {
                            "$match": {
                                constants.REGION_ID_FIELD: str(
                                    region[constants.INDEX_ID]
                                ),
                            }
                        },
                        {"$group": {"_id": None, "max_area": {"$max": "$area"}}},
                    ]
                )
            )
            region["max_area"] = (
                0 if len(max_doc_info) == 0 else max_doc_info[0]["max_area"]
            )

            # Get minimum area of all properties in the region
            min_doc_info = list(
                db[constants.PROPERTY_DETAILS_SCHEMA].aggregate(
                    [
                        {
                            "$match": {
                                constants.REGION_ID_FIELD: str(
                                    region[constants.INDEX_ID]
                                ),
                            }
                        },
                        {"$group": {"_id": None, "min_area": {"$min": "$area"}}},
                    ]
                )
            )
            region["min_area"] = (
                0 if len(min_doc_info) == 0 else min_doc_info[0]["min_area"]
            )

            region[constants.ID] = str(region[constants.INDEX_ID])
            del region[constants.INDEX_ID]
            del region[constants.ICON_IMAGE_FIELD]
            response_regions.append(region)
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"regions": response_regions},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Regions Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Regions Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Regions Service")
    return response


def get_available_regions_name():
    logger.debug("Inside Get Available Regions Name Service")
    try:
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        regions = list(
            region_collection.find(
                {constants.IS_ACTIVE_FIELD: True},
                {constants.INDEX_ID: 0, constants.TITLE_FIELD: 1},
            ).sort(constants.CREATED_AT_FIELD, -1)
        )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"regions": regions},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Available Regions Name Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get Available Regions Name Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Available Regions Name Service")
    return response


def get_available_categories_name():
    logger.debug("Inside Get Available Categories Name Service")
    try:
        category_collection = db[constants.PROPERTY_CATEGORY_DETAILS_SCHEMA]
        categories = list(
            category_collection.find(
                {constants.IS_ACTIVE_FIELD: True},
                {constants.INDEX_ID: 0, constants.TITLE_FIELD: 1},
            ).sort(constants.CREATED_AT_FIELD, -1)
        )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"categories": categories},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Available Categories Name Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get Available Categories Name Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Available Categories Name Service")
    return response


def get_filter_buttons_list():
    logger.debug("Inside Get Filter Buttons List Service")
    try:
        filter_buttons_dict = {
            "listing_type": [
                {
                    "value": listing_type.value,
                    "label": listing_type.value.title().replace("_", " "),
                }
                for listing_type in ListingType
            ],
            "listed_by": [
                {
                    "value": listed_by.value,
                    "label": listed_by.value.title().replace("_", " "),
                }
                for listed_by in ListedBy
            ],
            "possession_type": [
                {
                    "value": possession_type.value,
                    "label": possession_type.value.title().replace("_", " "),
                }
                for possession_type in PossessionType
            ],
            "category": [
                {
                    "value": category.value,
                    "label": category.value.title().replace("_", " "),
                }
                for category in Category
            ],
            "residential_type": [
                {
                    "value": residential_type.value,
                    "label": residential_type.value.title().replace("_", " "),
                }
                for residential_type in ResidentialType
            ],
            "furnishing": [
                {
                    "value": furnishing.value,
                    "label": furnishing.value.title().replace("_", " "),
                }
                for furnishing in Furnishing
            ],
            "facing": [
                {"value": facing.value, "label": facing.value.title().replace("_", " ")}
                for facing in Facing
            ],
            "residentials_sub_category": [
                {
                    "value": residential_sub_category.value,
                    "label": residential_sub_category.value.replace(
                        "residential_", ""
                    ).title(),
                }
                for residential_sub_category in PropertySubCategory
                if residential_sub_category.value.startswith("residential")
            ],
            "commercial_sub_category": [
                {
                    "value": commercial_sub_category.value,
                    "label": commercial_sub_category.value.replace(
                        "commercial_", ""
                    ).title(),
                }
                for commercial_sub_category in PropertySubCategory
                if commercial_sub_category.value.startswith("commercial")
            ],
            "farm_sub_category": [
                {
                    "value": farm_sub_category.value,
                    "label": farm_sub_category.value.replace("_", " ").title(),
                }
                for farm_sub_category in PropertySubCategory
                if farm_sub_category.value.startswith("farm")
            ],
        }
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"filter_buttons_dict": filter_buttons_dict},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Filter Buttons List Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Filter Buttons List Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Filter Buttons List Service")
    return response


def add_residential_property(
    request: ResidentialPropertyRequestSchema,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Residential Property Service")
    try:
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        request = jsonable_encoder(request)
        residential_property_collection = db[
            constants.RESIDENTIAL_PROPERTY_DETAILS_SCHEMA
        ]
        # Property Details Index
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_index = PropertySchema(
            is_investment_property=request["is_investment_property"],
            listed_by_user_id=user_id,
            listing_type=request["listing_type"],
            listed_by=request["listed_by"],
            possession_type=request["possession_type"],
            category="residential",
            description=request["description"],
            project_logo="",
            project_title=request["project_title"],
            price=request["price"],
            area=request["carpet_area"],
            view_count=0,
            video_url=request["video_url"],
            address=request["address"],
            location={
                "type": "Point",
                "coordinates": [
                    request["location"]["longitude"],
                    request["location"]["latitude"],
                ],
            },
            region_id=request["region_id"],
            verified=False,
            property_details_id="",
            candle_data_id="",
            roi_percentage=request["roi_percentage"],
        )
        property_index = property_details_collection.insert_one(
            jsonable_encoder(property_index)
        )
        # Residential Property Index
        residential_index = ResidentialPropertySchema(
            property_id=str(property_index.inserted_id),
            property_type=request["property_type"],
            bedrooms=request["bedrooms"],
            bathrooms=request["bathrooms"],
            furnishing=request["furnishing"],
            built_up_area=request["built_up_area"],
            carpet_area=request["carpet_area"],
            maintenance=request["maintenance"],
            floor_no=request["floor_no"],
            car_parking=request["car_parking"],
            facing=request["facing"],
            balcony=request["balcony"],
        )
        residential_index = residential_property_collection.insert_one(
            jsonable_encoder(residential_index)
        )

        # Candle Data Index
        candle_collection = db[constants.CANDLE_DETAILS_SCHEMA]
        candle_index = CandleDataSchema(
            property_id=str(property_index.inserted_id),
            property_gain=0,
            candle_data=[{"timestamp": time.time(), "price": request["price"]}],
        )
        candle_index = candle_collection.insert_one(jsonable_encoder(candle_index))

        # Update Property Details Index
        property_details_collection.update_one(
            {constants.INDEX_ID: property_index.inserted_id},
            {
                "$set": {
                    "candle_data_id": str(candle_index.inserted_id),
                    "property_details_id": str(residential_index.inserted_id),
                }
            },
        )
        logger.debug(
            f"Residential Property Added Successfully at Index {residential_index.inserted_id}"
        )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Residential Property Added Successfully",constants.ID: str(property_index.inserted_id)},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Residential Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Residential Property Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Residential Property Service")
    return response


def update_residential_property(
    property_id: str,
    request: ResidentialPropertyRequestSchema,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Residential Property Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        request = jsonable_encoder(request)
        residential_property_collection = db[
            constants.RESIDENTIAL_PROPERTY_DETAILS_SCHEMA
        ]
        # Property Details Index
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        # If Property doesn't belongs to the user and property is not of type residential then dont update it
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if (
            property_details.get(constants.LISTED_BY_USER_ID_FIELD) != user_id
            or property_details.get("category") != "residential"
        ):
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property doesn't belongs to the user or property is not of type residential"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        # Update Property Details Index
        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {
                "$set": {
                    "listing_type": request["listing_type"],
                    "region_id": request["region_id"],
                    "listed_by": request["listed_by"],
                    "possession_type": request["possession_type"],
                    "description": request["description"],
                    "project_title": request["project_title"],
                    "price": request["price"],
                    "area": request["carpet_area"],
                    "video_url": request["video_url"],
                    "address": request["address"],
                    "location": {
                        "type": "Point",
                        "coordinates": [
                            request["location"]["longitude"],
                            request["location"]["latitude"],
                        ],
                    },
                    "roi_percentage": request["roi_percentage"],
                }
            },
        )

        # Residential Property Index
        residential_property_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {
                "$set": {
                    "property_type": request["property_type"],
                    "bedrooms": request["bedrooms"],
                    "bathrooms": request["bathrooms"],
                    "furnishing": request["furnishing"],
                    "built_up_area": request["built_up_area"],
                    "carpet_area": request["carpet_area"],
                    "maintenance": request["maintenance"],
                    "floor_no": request["floor_no"],
                    "car_parking": request["car_parking"],
                    "facing": request["facing"],
                    "balcony": request["balcony"],
                }
            },
        )

        logger.debug(
            f"Residential Property Updated Successfully at Index {property_id}"
        )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Residential Property Updated Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update Residential Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Update Residential Property Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Residential Property Service")
    return response


def add_commercial_property(
    request: CommercialPropertyRequestSchema,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Commercial Property Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        request = jsonable_encoder(request)
        commercial_property_collection = db[
            constants.COMMERCIAL_PROPERTY_DETAILS_SCHEMA
        ]
        # Property Details Index
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_index = PropertySchema(
            is_investment_property=request["is_investment_property"],
            region_id=request["region_id"],
            listed_by_user_id=user_id,
            listing_type=request["listing_type"],
            listed_by=request["listed_by"],
            possession_type=request["possession_type"],
            category="commercial",
            description=request["description"],
            project_logo="",
            project_title=request["project_title"],
            price=request["price"],
            area=request["carpet_area"],
            view_count=0,
            video_url=request["video_url"],
            address=request["address"],
            location={
                "type": "Point",
                "coordinates": [
                    request["location"]["longitude"],
                    request["location"]["latitude"],
                ],
            },
            verified=False,
            property_details_id="",
            candle_data_id="",
            roi_percentage=request["roi_percentage"],
        )
        property_index = property_details_collection.insert_one(
            jsonable_encoder(property_index)
        )

        # Commercial Property Index
        commercial_index = CommercialPropertySchema(
            property_id=str(property_index.inserted_id),
            property_type=request["property_type"],
            furnishing=request["furnishing"],
            built_up_area=request["built_up_area"],
            carpet_area=request["carpet_area"],
            maintenance=request["maintenance"],
            car_parking=request["car_parking"],
            bathrooms=request["bathrooms"],
        )
        commercial_index = commercial_property_collection.insert_one(
            jsonable_encoder(commercial_index)
        )

        # Candle Data Index
        candle_collection = db[constants.CANDLE_DETAILS_SCHEMA]
        candle_index = CandleDataSchema(
            property_gain=0,
            property_id=str(property_index.inserted_id),
            candle_data=[{"timestamp": time.time(), "price": request["price"]}],
        )

        candle_index = candle_collection.insert_one(jsonable_encoder(candle_index))

        # Update Property Details Index
        property_details_collection.update_one(
            {constants.INDEX_ID: property_index.inserted_id},
            {
                "$set": {
                    "candle_data_id": str(candle_index.inserted_id),
                    "property_details_id": str(commercial_index.inserted_id),
                }
            },
        )

        logger.debug(
            f"Commercial Property Added Successfully at Index {commercial_index.inserted_id}"
        )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "Commercial Property Added Successfully",
                constants.ID: str(property_index.inserted_id),
            },
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Add Commercial Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Commercial Property Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Commercial Property Service")
    return response


def update_commercial_property(
    property_id: str,
    request: CommercialPropertyRequestSchema,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Commercial Property Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        request = jsonable_encoder(request)
        commercial_property_collection = db[
            constants.COMMERCIAL_PROPERTY_DETAILS_SCHEMA
        ]
        # Property Details Index
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        # If Property doesn't belongs to the user and property is not of type commercial then dont update it
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if (
            property_details.get(constants.LISTED_BY_USER_ID_FIELD) != user_id
            or property_details.get("category") != "commercial"
        ):
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property doesn't belongs to the user or property is not of type commercial"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        # Update Property Details Index
        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {
                "$set": {
                    "listing_type": request["listing_type"],
                    "region_id": request["region_id"],
                    "listed_by": request["listed_by"],
                    "possession_type": request["possession_type"],
                    "description": request["description"],
                    "project_title": request["project_title"],
                    "price": request["price"],
                    "area": request["carpet_area"],
                    "video_url": request["video_url"],
                    "address": request["address"],
                    "location": {
                        "type": "Point",
                        "coordinates": [
                            request["location"]["longitude"],
                            request["location"]["latitude"],
                        ],
                    },
                    "roi_percentage": request["roi_percentage"],
                }
            },
        )

        # Commercial Property Index
        commercial_property_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {
                "$set": {
                    "property_type": request["property_type"],
                    "furnishing": request["furnishing"],
                    "built_up_area": request["built_up_area"],
                    "carpet_area": request["carpet_area"],
                    "maintenance": request["maintenance"],
                    "car_parking": request["car_parking"],
                    "bathrooms": request["bathrooms"],
                }
            },
        )

        logger.debug(f"Commercial Property Updated Successfully at Index {property_id}")

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Commercial Property Updated Successfully"},
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Update Commercial Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Update Commercial Property Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Commercial Property Service")
    return response


def add_farm_property(
    request: FarmPropertyRequestSchema,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Farm Property Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        request = jsonable_encoder(request)
        farm_property_collection = db[constants.FARM_PROPERTY_DETAILS_SCHEMA]
        # Property Details Index
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_index = PropertySchema(
            is_investment_property=request["is_investment_property"],
            region_id=request["region_id"],
            listed_by_user_id=user_id,
            listing_type=request["listing_type"],
            listed_by=request["listed_by"],
            possession_type=request["possession_type"],
            category="farm",
            description=request["description"],
            project_logo="",
            project_title=request["project_title"],
            price=request["price"],
            area=request["plot_area"],
            view_count=0,
            video_url="",
            address=request["address"],
            location={
                "type": "Point",
                "coordinates": [
                    request["location"]["longitude"],
                    request["location"]["latitude"],
                ],
            },
            verified=False,
            property_details_id="",
            candle_data_id="",
            roi_percentage=request["roi_percentage"],
        )
        property_index = property_details_collection.insert_one(
            jsonable_encoder(property_index)
        )

        # Farm Property Index
        farm_index = FarmPropertySchema(
            property_id=str(property_index.inserted_id),
            property_type=request["property_type"],
            plot_area=request["plot_area"],
            length=request["length"],
            breadth=request["breadth"],
            facing=request["facing"],
        )
        farm_index = farm_property_collection.insert_one(jsonable_encoder(farm_index))

        # Candle Data Index
        candle_collection = db[constants.CANDLE_DETAILS_SCHEMA]
        candle_index = CandleDataSchema(
            property_id=str(property_index.inserted_id),
            property_gain=0,
            candle_data=[{"timestamp": time.time(), "price": request["price"]}],
        )

        candle_index = candle_collection.insert_one(jsonable_encoder(candle_index))

        # Update Property Details Index
        property_details_collection.update_one(
            {constants.INDEX_ID: property_index.inserted_id},
            {
                "$set": {
                    "candle_data_id": str(candle_index.inserted_id),
                    "property_details_id": str(farm_index.inserted_id),
                }
            },
        )

        logger.debug(
            f"Farm Property Added Successfully at Index {farm_index.inserted_id}"
        )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "Farm Property Added Successfully",
                constants.ID: str(property_index.inserted_id),
            },
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Add Farm Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Farm Property Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Farm Property Service")
    return response


def update_farm_property(
    property_id: str,
    request: FarmPropertyRequestSchema,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Farm Property Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        request = jsonable_encoder(request)
        farm_property_collection = db[constants.FARM_PROPERTY_DETAILS_SCHEMA]
        # Property Details Index
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        # If Property doesn't belongs to the user and property is not of type farm then dont update it
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if (
            property_details.get(constants.LISTED_BY_USER_ID_FIELD) != user_id
            or property_details.get("category") != "farm"
        ):
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property doesn't belongs to the user or property is not of type farm"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        # Update Property Details Index
        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {
                "$set": {
                    "listing_type": request["listing_type"],
                    "region_id": request["region_id"],
                    "area": request["plot_area"],
                    "listed_by": request["listed_by"],
                    "possession_type": request["possession_type"],
                    "category": "farm",
                    "description": request["description"],
                    "project_logo": "",
                    "project_title": request["project_title"],
                    "price": request["price"],
                    "video_url": request["video_url"],
                    "address": request["address"],
                    "location": {
                        "type": "Point",
                        "coordinates": [
                            request["location"]["longitude"],
                            request["location"]["latitude"],
                        ],
                    },
                    "roi_percentage": request["roi_percentage"],
                }
            },
        )

        # Farm Property Index
        farm_property_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {
                "$set": {
                    "plot_area": request["plot_area"],
                    "property_type": request["property_type"],
                    "length": request["length"],
                    "breadth": request["breadth"],
                    "facing": request["facing"],
                }
            },
        )

        logger.debug(f"Farm Property Updated Successfully at Index {property_id}")

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Farm Property Updated Successfully"},
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Update Farm Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update Farm Property Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )

    logger.debug("Returning From the Update Farm Property Service")
    return response


def update_property_view_count(
    property_id
):
    logger.debug("Inside Update View Count Of Property Service")
    try:
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if property_details is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {"$inc": {"view_count": 1}},
        )
        logger.debug(
            f"View Count of Property Updated Successfully at Index {property_id}"
        )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "View Count of Property Updated Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update View Count Of Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Update View Count Of Property Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update View Count Of Property Service")
    return response


def get_list_of_featured_properties(
    latitude: float, longitude: float, per_page: int, page_number: int
):
    logger.debug("Inside Get List Of Featured Properties Service")
    try:
        location = {"latitude": latitude, "longitude": longitude}
        region_id = get_nearest_region_id(location)
        if region_id is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        region_id = region_id[0].get(constants.INDEX_ID)
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        region = region_collection.find_one({constants.INDEX_ID: region_id})

        if region is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        featured_properties = region.get(constants.FEATURED_PROPERTIES_FIELD)
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        filter_by = [ObjectId(property_id) for property_id in featured_properties]
        properties = list(
            property_details_collection.find(
                {constants.INDEX_ID: {"$in": filter_by}, constants.STATUS_FIELD: PropertyStatus.ACTIVE.value },
                {
                    constants.INDEX_ID: 1,
                    constants.PROJECT_TITLE_FIELD: 1,
                    constants.PRICE_FIELD: 1,
                    constants.IMAGES_FIELD: 1,
                    constants.ADDRESS_FIELD: 1,
                    constants.LOCATION_FIELD: 1,
                },
            )
            .sort(constants.CREATED_AT_FIELD, -1)
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        document_count = property_details_collection.count_documents(
            {constants.INDEX_ID: {"$in": filter_by}, constants.STATUS_FIELD: PropertyStatus.ACTIVE.value}
        )
        response_list = []
        for property in properties:
            response_list.append(
                {
                    constants.ID: str(property[constants.INDEX_ID]),
                    constants.PROJECT_TITLE_FIELD: property[
                        constants.PROJECT_TITLE_FIELD
                    ],
                    constants.ADDRESS_FIELD: property[constants.ADDRESS_FIELD],
                    constants.PRICE_FIELD: property[constants.PRICE_FIELD],
                    constants.LOCATION_FIELD: property[constants.LOCATION_FIELD],
                    constants.IMAGES_FIELD: [
                        core_cloudfront.cloudfront_sign(image_key)
                        for image_key in property[constants.IMAGES_FIELD][:1]
                    ],
                }
            )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "properties": response_list,
                "document_count": document_count,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.debug(f"Error in Get List Of Featured Properties Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get List Of Featured Properties Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get List Of Featured Properties Service")
    return response


def get_list_of_recommended_properties(
    latitude: float, longitude: float, per_page: int, page_number: int
):
    logger.debug("Inside Get List Of Recommended Properties Service")
    try:
        location = {"latitude": latitude, "longitude": longitude}
        region_id = get_nearest_region_id(location)
        if region_id is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        region_id = region_id[0].get(constants.INDEX_ID)
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        region = region_collection.find_one({constants.INDEX_ID: region_id})

        if region is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        region_collection = db[constants.REGION_DETAILS_SCHEMA]

        region = region_collection.find_one({constants.INDEX_ID: ObjectId(region_id)})

        if region is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        recommended_properties = region.get(constants.RECOMMENDED_PROPERTIES_FIELD)
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        filter_by = [ObjectId(property_id) for property_id in recommended_properties]
        properties = list(
            property_details_collection.find(
                {constants.INDEX_ID: {"$in": filter_by}, constants.STATUS_FIELD: PropertyStatus.ACTIVE.value},
                {
                    constants.INDEX_ID: 1,
                    constants.PROJECT_TITLE_FIELD: 1,
                    constants.PRICE_FIELD: 1,
                    constants.IMAGES_FIELD: 1,
                    constants.ADDRESS_FIELD: 1,
                    constants.LISTED_BY_FIELD: 1,
                    constants.CREATED_AT_FIELD: 1,
                    constants.LOCATION_FIELD: 1,
                },
            )
            .sort(constants.CREATED_AT_FIELD, -1)
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        document_count = property_details_collection.count_documents(
            {constants.INDEX_ID: {"$in": filter_by}, constants.STATUS_FIELD: PropertyStatus.ACTIVE.value}
        )
        response_list = []
        for property in properties:
            response_list.append(
                {
                    constants.ID: str(property[constants.INDEX_ID]),
                    constants.PROJECT_TITLE_FIELD: property[
                        constants.PROJECT_TITLE_FIELD
                    ],
                    constants.ADDRESS_FIELD: property[constants.ADDRESS_FIELD],
                    constants.PRICE_FIELD: property[constants.PRICE_FIELD],
                    constants.IMAGES_FIELD: [
                        core_cloudfront.cloudfront_sign(image_key)
                        for image_key in property[constants.IMAGES_FIELD][:4]
                    ],
                    constants.LISTED_BY_FIELD: property[constants.LISTED_BY_FIELD],
                    constants.CREATED_AT_FIELD: property[constants.CREATED_AT_FIELD],
                    constants.LOCATION_FIELD: property[constants.LOCATION_FIELD],
                }
            )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "properties": response_list,
                "document_count": document_count,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get List Of Recommended Properties Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get List Of Recommended Properties Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get List Of Recommended Properties Service")
    return response


def get_list_of_most_viewed_properties(per_page: int, page_number: int):
    logger.debug("Inside Get List Of Most Viewed Properties Service")
    try:
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        properties = list(
            property_details_collection.find(
                { constants.STATUS_FIELD: PropertyStatus.ACTIVE.value},
                {
                    constants.INDEX_ID: 1,
                    constants.PROJECT_TITLE_FIELD: 1,
                    constants.PRICE_FIELD: 1,
                    constants.IMAGES_FIELD: 1,
                    constants.ADDRESS_FIELD: 1,
                    constants.LISTED_BY_FIELD: 1,
                    constants.CREATED_AT_FIELD: 1,
                    constants.VIEW_COUNT_FIELD: 1,
                    constants.LOCATION_FIELD: 1,
                },
            )
            .sort(constants.VIEW_COUNT_FIELD, -1)
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        document_count = property_details_collection.count_documents({ constants.STATUS_FIELD: PropertyStatus.ACTIVE.value})
        response_list = []
        for property in properties:
            response_list.append(
                {
                    constants.ID: str(property[constants.INDEX_ID]),
                    constants.PROJECT_TITLE_FIELD: property[
                        constants.PROJECT_TITLE_FIELD
                    ],
                    constants.ADDRESS_FIELD: property[constants.ADDRESS_FIELD],
                    constants.PRICE_FIELD: property[constants.PRICE_FIELD],
                    constants.IMAGES_FIELD: [
                        core_cloudfront.cloudfront_sign(image_key)
                        for image_key in property[constants.IMAGES_FIELD][:1]
                    ],
                    constants.LISTED_BY_FIELD: property[constants.LISTED_BY_FIELD],
                    constants.CREATED_AT_FIELD: property[constants.CREATED_AT_FIELD],
                    constants.VIEW_COUNT_FIELD: property[constants.VIEW_COUNT_FIELD],
                    constants.LOCATION_FIELD: property[constants.LOCATION_FIELD],
                }
            )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "properties": response_list,
                "document_count": document_count,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get List Of Most Viewed Properties Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get List Of Most Viewed Properties Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get List Of Most Viewed Properties Service")
    return response


def get_list_of_top_properties(
    latitude: float, longitude: float, per_page: int, page_number: int
):
    logger.debug("Inside Get List Of Top Properties Service")
    try:
        location = {"latitude": latitude, "longitude": longitude}
        region_id = get_nearest_region_id(location)
        if region_id is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        region_id = region_id[0].get(constants.INDEX_ID)
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        region = region_collection.find_one({constants.INDEX_ID: region_id})

        if region is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        region_collection = db[constants.REGION_DETAILS_SCHEMA]

        region = region_collection.find_one({constants.INDEX_ID: ObjectId(region_id)})

        if region is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        top_properties = region.get(constants.TOP_PROPERTIES_FIELD)
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        filter_by = [ObjectId(property_id) for property_id in top_properties]
        properties = list(
            property_details_collection.find(
                {constants.INDEX_ID: {"$in": filter_by}, constants.STATUS_FIELD: PropertyStatus.ACTIVE.value},
                {
                    constants.INDEX_ID: 1,
                    constants.IMAGES_FIELD: 1,
                    constants.PRICE_FIELD: 1,
                    constants.ADDRESS_FIELD: 1,
                    constants.LOCATION_FIELD: 1,
                },
            )
            .sort(constants.CREATED_AT_FIELD, -1)
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        document_count = property_details_collection.count_documents(
            {constants.INDEX_ID: {"$in": filter_by}, constants.STATUS_FIELD: PropertyStatus.ACTIVE.value}
        )
        response_list = []
        for property in properties:
            response_list.append(
                {
                    constants.ID: str(property[constants.INDEX_ID]),
                    constants.IMAGES_FIELD: [
                        core_cloudfront.cloudfront_sign(image_key)
                        for image_key in property[constants.IMAGES_FIELD][:1]
                    ],
                    constants.ADDRESS_FIELD: property[constants.ADDRESS_FIELD],
                    constants.PRICE_FIELD: property[constants.PRICE_FIELD],
                    constants.LOCATION_FIELD: property[constants.LOCATION_FIELD],
                }
            )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "properties": response_list,
                "document_count": document_count,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get List Of Recommended Properties Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get List Of Recommended Properties Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get List Of Recommended Properties Service")
    return response


def get_nearby_properties(
    latitude: float, longitude: float, per_page: int, page_number: int
):
    logger.debug("Inside Get List Of Nearby Properties Service")
    try:
        location = {"latitude": latitude, "longitude": longitude}

        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        location_filter = {
            constants.LOCATION_FIELD: SON(
                [
                    (
                        "$nearSphere",
                        [location.get("longitude"), location.get("latitude")],
                    ),
                ]
            ), constants.STATUS_FIELD: PropertyStatus.ACTIVE.value
        }
        properties = list(
            property_details_collection.find(
                location_filter,
                {
                    constants.INDEX_ID: 1,
                    constants.IMAGES_FIELD: 1,
                    constants.PRICE_FIELD: 1,
                    constants.ADDRESS_FIELD: 1,
                    constants.LOCATION_FIELD: 1,
                },
            )
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        
        document_count = len(list(property_details_collection.find(location_filter)))
        response_list = []
        for property in properties:
            response_list.append(
                {
                    constants.ID: str(property[constants.INDEX_ID]),
                    constants.IMAGES_FIELD: [
                        core_cloudfront.cloudfront_sign(image_key)
                        for image_key in property[constants.IMAGES_FIELD][:4]
                    ],
                    constants.ADDRESS_FIELD: property[constants.ADDRESS_FIELD],
                    constants.PRICE_FIELD: property[constants.PRICE_FIELD],
                    constants.LOCATION_FIELD: property[constants.LOCATION_FIELD],
                }
            )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "properties": response_list,
                "document_count": document_count,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get List Of Recommended Properties Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get List Of Recommended Properties Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get List Of Recommended Properties Service")
    return response


def add_property_images(
    property_id: str,
    images: list,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Property Images Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if property_details is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        logger.debug(property_details)
        if property_details.get(constants.LISTED_BY_USER_ID_FIELD) != user_id:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't belongs to the user"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        images_list = []
        for image in images:
            base = constants.PROPERTY_IMAGES_BASE
            upload_response = jsonable_encoder(
                upload_image(
                    file=image,
                    base=base,
                    user_id=user_id,
                    object_id=property_id,
                )
            )
            if upload_response["type"] == constants.HTTP_RESPONSE_FAILURE:
                return upload_response
            images_list.append(upload_response["data"]["key"])

        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {"$set": {constants.IMAGES_FIELD: images_list}},
        )
        logger.debug(f"Images Added Successfully to Property at Index {property_id}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Images Added Successfully to Property"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Property Images Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Property Images Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Property Images Service")
    return response


def get_property_images(
    property_id: str, token: Annotated[str, Depends(oauth2_scheme)]
):
    logger.debug("Inside Get Property Images Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        logger.debug("Inside Get Property Images Service")
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if property_details is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        response_url = []
        for key in property_details[constants.IMAGES_FIELD]:
            profile_picture_url = core_cloudfront.cloudfront_sign(key)
            response_url.append(profile_picture_url)

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.IMAGES_FIELD: response_url},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Property Images Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"{e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Property Images Service")
    return response


def update_property_images(
    property_id: str,
    images: list,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if property_details is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        logger.debug(property_details)
        if property_details.get(constants.LISTED_BY_USER_ID_FIELD) != user_id:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't belongs to the user"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        images_list = []
        for image in images:
            base = constants.PROPERTY_IMAGES_BASE
            upload_response = jsonable_encoder(
                upload_image(
                    file=image,
                    base=base,
                    user_id=user_id,
                    object_id=property_id,
                )
            )
            if upload_response["type"] == constants.HTTP_RESPONSE_FAILURE:
                return upload_response
            images_list.append(upload_response["data"]["key"])

        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {"$set": {constants.IMAGES_FIELD: images_list}},
        )
        logger.debug(f"Images Added Successfully to Property at Index {property_id}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Images Added Successfully to Property"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Property Images Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Property Images Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Property Images Service")
    return response


def add_seed_property(
    request: ResidentialPropertyRequestSchema,
):
    logger.debug("Inside Add Residential Property Service")
    try:
        parnter_user_details = db[constants.USER_DETAILS_SCHEMA].find_one(
            {constants.USER_TYPE_FIELD: UserTypes.PARTNER.value}
        )
        if parnter_user_details is None:
            user_id = "change_user_id"
        else:
            user_id = str(parnter_user_details.get(constants.INDEX_ID))
        request = jsonable_encoder(request)
        residential_property_collection = db[
            constants.RESIDENTIAL_PROPERTY_DETAILS_SCHEMA
        ]
        # Property Details Index
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_index = PropertySchema(
            is_investment_property=request["is_investment_property"],
            listed_by_user_id=user_id,
            listing_type=request["listing_type"],
            listed_by=request["listed_by"],
            possession_type=request["possession_type"],
            category="residential",
            description=request["description"],
            project_logo="",
            project_title=request["project_title"],
            price=request["price"],
            view_count=0,
            video_url="",
            address=request["address"],
            location={
                "type": "Point",
                "coordinates": [
                    request["location"]["longitude"],
                    request["location"]["latitude"],
                ],
            },
            region_id="",
            verified=False,
            property_details_id="",
            candle_data_id="",
            roi_percentage=request["roi_percentage"],
        )
        property_index = property_details_collection.insert_one(
            jsonable_encoder(property_index)
        )
        # Residential Property Index
        residential_index = ResidentialPropertySchema(
            property_id=str(property_index.inserted_id),
            property_type=request["property_type"],
            bedrooms=request["bedrooms"],
            bathrooms=request["bathrooms"],
            furnishing=request["furnishing"],
            built_up_area=request["built_up_area"],
            carpet_area=request["carpet_area"],
            maintenance=request["maintenance"],
            floor_no=request["floor_no"],
            car_parking=request["car_parking"],
            facing=request["facing"],
            balcony=request["balcony"],
        )
        residential_index = residential_property_collection.insert_one(
            jsonable_encoder(residential_index)
        )

        # Candle Data Index
        candle_collection = db[constants.CANDLE_DETAILS_SCHEMA]
        candle_index = CandleDataSchema(
            property_id=str(property_index.inserted_id),
            property_gain=0,
            candle_data=[{"timestamp": time.time(), "price": request["price"]}],
        )
        candle_index = candle_collection.insert_one(jsonable_encoder(candle_index))

        # Update Property Details Index
        property_details_collection.update_one(
            {constants.INDEX_ID: property_index.inserted_id},
            {
                "$set": {
                    "candle_data_id": str(candle_index.inserted_id),
                    "property_details_id": str(residential_index.inserted_id),
                }
            },
        )
        logger.debug(
            f"Residential Property Added Successfully at Index {residential_index.inserted_id}"
        )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Residential Property Added Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Residential Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Residential Property Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Residential Property Service")
    return response


def add_project_logo(
    property_id: str,
    logo: UploadFile,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Project Logo Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if property_details is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        if property_details.get(constants.LISTED_BY_USER_ID_FIELD) != user_id:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't belongs to the user"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        base = constants.PROJECT_LOGO_BASE
        upload_response = jsonable_encoder(
            upload_image(
                file=logo,
                base=base,
                user_id=user_id,
                object_id=property_id,
            )
        )
        if upload_response["type"] == constants.HTTP_RESPONSE_FAILURE:
            return upload_response
        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {"$set": {constants.PROJECT_LOGO_FIELD: upload_response["data"]["key"]}},
        )

        logger.debug(
            f"Project Logo Added Successfully to Property at Index {property_id}"
        )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Project Logo Added Successfully to Property"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Project Logo Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Project Logo Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Project Logo Service")
    return response


def get_property_by_id(property_id: str):
    logger.debug("Inside Get Property By Id Service")
    try:
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        candle_details_collection = db[constants.CANDLE_DETAILS_SCHEMA]
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if property_details is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        property_details[constants.IMAGES_FIELD] = [
            core_cloudfront.cloudfront_sign(image_key)
            for image_key in property_details[constants.IMAGES_FIELD]
        ]

        if property_details.get(constants.PROJECT_LOGO_FIELD):
            property_details[
                constants.PROJECT_LOGO_FIELD
            ] = core_cloudfront.cloudfront_sign(
                property_details[constants.PROJECT_LOGO_FIELD]
            )

        if property_details.get(constants.CATEGORY_FIELD) == "residential":
            residential_property_collection = db[
                constants.RESIDENTIAL_PROPERTY_DETAILS_SCHEMA
            ]
            residential_property_details = residential_property_collection.find_one(
                {
                    constants.INDEX_ID: ObjectId(
                        property_details[constants.PROPERTY_DETAILS_ID_FIELD]
                    )
                },
                {"_id": 0},
            )
            if residential_property_details is None:
                response = admin_property_management_schemas.ResponseMessage(
                    type=constants.HTTP_RESPONSE_FAILURE,
                    data={constants.MESSAGE: f"Property doesn't Found!"},
                    status_code=HTTPStatus.BAD_REQUEST,
                )
                return response
            property_details["property_info"] = residential_property_details
        elif property_details.get(constants.CATEGORY_FIELD) == "commercial":
            commercial_property_collection = db[
                constants.COMMERCIAL_PROPERTY_DETAILS_SCHEMA
            ]
            commercial_property_details = commercial_property_collection.find_one(
                {
                    constants.INDEX_ID: ObjectId(
                        property_details[constants.PROPERTY_DETAILS_ID_FIELD]
                    )
                },
                {"_id": 0},
            )
            if commercial_property_details is None:
                response = admin_property_management_schemas.ResponseMessage(
                    type=constants.HTTP_RESPONSE_FAILURE,
                    data={constants.MESSAGE: f"Property doesn't Found!"},
                    status_code=HTTPStatus.BAD_REQUEST,
                )
                return response
            property_details["property_info"] = commercial_property_details
        elif property_details.get(constants.CATEGORY_FIELD) == "farm":
            farm_property_collection = db[constants.FARM_PROPERTY_DETAILS_SCHEMA]
            farm_property_details = farm_property_collection.find_one(
                {
                    constants.INDEX_ID: ObjectId(
                        property_details[constants.PROPERTY_DETAILS_ID_FIELD]
                    )
                },
                {"_id": 0},
            )
            if farm_property_details is None:
                response = admin_property_management_schemas.ResponseMessage(
                    type=constants.HTTP_RESPONSE_FAILURE,
                    data={constants.MESSAGE: f"Property doesn't Found!"},
                    status_code=HTTPStatus.BAD_REQUEST,
                )
                return response

            property_details["property_info"] = farm_property_details
        else:
            property_details["property_info"] = {}

        candle_data = candle_details_collection.find_one(
            {
                constants.INDEX_ID: ObjectId(
                    property_details[constants.CANDLE_DATA_ID_FIELD]
                )
            }
        )
        if candle_data is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Candle data doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        property_details["candle_data"] = candle_data["candle_data"]

        if property_details.get(constants.DOCUMENT_TITLE_FIELD):
            property_details[
                constants.PROPERTY_DOCUMENT_FIELD
            ] = core_cloudfront.cloudfront_sign(
                property_details[constants.PROPERTY_DOCUMENT_FIELD]
            )

        if property_details.get(constants.BROCHURE_TITLE_FIELD):
            property_details[
                constants.PROPERTY_BROCHURE_FIELD
            ] = core_cloudfront.cloudfront_sign(
                property_details[constants.PROPERTY_BROCHURE_FIELD]
            )

        property_details[constants.ID] = str(property_details[constants.INDEX_ID])
        del property_details[constants.INDEX_ID]
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data=property_details,
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Property By Id Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Property By Id Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Property By Id Service")
    return response


def get_property_list(
    page_number: int,
    per_page: int,
    filter_dict: dict,
    sort_dict: dict,
):
    logger.debug("Inside Get Property List Service")
    try:
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        properties = list(
            property_details_collection.find(
                filter_dict,
                {
                    constants.INDEX_ID: 1,
                    constants.PROJECT_TITLE_FIELD: 1,
                    constants.ADDRESS_FIELD: 1,
                    constants.PRICE_FIELD: 1,
                    constants.IMAGES_FIELD: 1,
                    constants.LISTED_BY_FIELD: 1,
                    constants.CREATED_AT_FIELD: 1,
                    constants.LOCATION_FIELD: 1,
                },
            )
            .sort([(key, value) for key, value in sort_dict.items()] if sort_dict else [(constants.CREATED_AT_FIELD,-1)])
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        document_count = property_details_collection.count_documents({})
        response_list = []
        for property in properties:
            response_list.append(
                {
                    constants.ID: str(property[constants.INDEX_ID]),
                    constants.PROJECT_TITLE_FIELD: property[
                        constants.PROJECT_TITLE_FIELD
                    ],
                    constants.ADDRESS_FIELD: property[constants.ADDRESS_FIELD],
                    constants.PRICE_FIELD: property[constants.PRICE_FIELD],
                    constants.IMAGES_FIELD: [
                        core_cloudfront.cloudfront_sign(image_key)
                        for image_key in property[constants.IMAGES_FIELD][:4]
                    ],
                    constants.LISTED_BY_FIELD: property[constants.LISTED_BY_FIELD],
                    constants.CREATED_AT_FIELD: property[constants.CREATED_AT_FIELD],
                    constants.LOCATION_FIELD: property[constants.LOCATION_FIELD],
                }
            )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "properties": response_list,
                "document_count": document_count,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Property List Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Property List Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Property List Service")
    return response


def upload_brochure_or_project_document(
    property_id: str,
    type: str,
    document: UploadFile,
    document_title: str,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Upload Brochure Or Project Document Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if property_details is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        if property_details.get(constants.LISTED_BY_USER_ID_FIELD) != user_id:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't belongs to the user"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        base = constants.PROPERTY_DOCUMENT_BASE
        upload_response = jsonable_encoder(
            upload_pdf(
                file=document,
                base=base,
                user_id=user_id,
                object_id=property_id,
            )
        )
        if upload_response["type"] == constants.HTTP_RESPONSE_FAILURE:
            return upload_response
        if type == "brochure":
            property_details_collection.update_one(
                {constants.INDEX_ID: ObjectId(property_id)},
                {
                    "$set": {
                        constants.PROPERTY_BROCHURE_FIELD: upload_response["data"][
                            "key"
                        ],
                        constants.BROCHURE_TITLE_FIELD: document_title,
                    }
                },
            )
        elif type == "project_document":
            property_details_collection.update_one(
                {constants.INDEX_ID: ObjectId(property_id)},
                {
                    "$set": {
                        constants.PROPERTY_DOCUMENT_FIELD: upload_response["data"][
                            "key"
                        ],
                        constants.DOCUMENT_TITLE_FIELD: document_title,
                    }
                },
            )
        else:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Invalid Type"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        logger.debug(
            f"Project Logo Added Successfully to Property at Index {property_id}"
        )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Project Logo Added Successfully to Property"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Upload Brochure Or Project Document Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Upload Brochure Or Project Document Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Upload Brochure Or Project Document Service")
    return response


def get_top_gainers():
    logger.debug("Inside Get Top Gainers Service")
    try:
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        candle_details_collection = db[constants.CANDLE_DETAILS_SCHEMA]
        region_details_collection = db[constants.REGION_DETAILS_SCHEMA]

        region_ids = region_details_collection.find(
            {constants.IS_ACTIVE_FIELD: True},
            {constants.INDEX_ID: 1, constants.TITLE_FIELD: 1},
        )
        region_id_list = [
            (region_id[constants.INDEX_ID], region_id[constants.TITLE_FIELD])
            for region_id in region_ids
        ]

        top_gainers_by_region_dict = {}
        for region in region_id_list:
            property_ids = list(
                map(
                    lambda x: str(x.get(constants.INDEX_ID)),
                    list(
                        property_details_collection.find(
                            {
                                constants.REGION_ID_FIELD: str(region[0]),
                            },
                            {constants.INDEX_ID: 1},
                        )
                    ),
                )
            )
            candle_data = list(
                candle_details_collection.aggregate(
                    [
                        {"$match": {"property_id": {"$in": property_ids}}},
                        {"$sort": {"property_gain": -1}},
                        {"$limit": 5},
                    ]
                )
            )
            formated_candle_data = []
            for data in candle_data:
                property_details = property_details_collection.find_one(
                    {constants.INDEX_ID: ObjectId(data.get("property_id"))}
                )
                property_details_dict = {
                    constants.ID: str(property_details.get(constants.INDEX_ID)),
                    constants.PROJECT_TITLE_FIELD: property_details.get(
                        constants.PROJECT_TITLE_FIELD
                    ),
                    constants.PROJECT_LOGO_FIELD: core_cloudfront.cloudfront_sign(
                        property_details.get(constants.PROJECT_LOGO_FIELD)
                    ),
                    constants.PRICE_FIELD: property_details.get(constants.PRICE_FIELD),
                }
                response_data = {
                    constants.ID: str(data.get(constants.INDEX_ID)),
                    "region_name": region[1],
                    "candle_data": data.get("candle_data"),
                    "property_gain": data.get("property_gain"),
                    "property_details": property_details_dict,
                }
                formated_candle_data.append(response_data)
            top_gainers_by_region_dict[str(region[0])] = formated_candle_data

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "gainers_dict": top_gainers_by_region_dict,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Top Gainers Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Top Gainers Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Top Gainers Service")
    return response


def get_similar_properties(region_id: str, page_number: int, per_page: int):
    logger.debug("Inside Get Similar Properties Service")
    try:
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_details = (
            property_details_collection.find(
                {constants.REGION_ID_FIELD: region_id},
                {
                    constants.INDEX_ID: 1,
                    constants.PROJECT_TITLE_FIELD: 1,
                    constants.ADDRESS_FIELD: 1,
                    constants.PRICE_FIELD: 1,
                    constants.IMAGES_FIELD: 1,
                    constants.LISTED_BY_FIELD: 1,
                    constants.CREATED_AT_FIELD: 1,
                    constants.LOCATION_FIELD: 1,
                    constants.DESCRIPTION_FIELD: 1,
                },
            )
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        document_count = property_details_collection.count_documents(
            {constants.REGION_ID_FIELD: region_id}
        )
        response_list = []
        for property in property_details:
            response_list.append(
                {
                    constants.ID: str(property[constants.INDEX_ID]),
                    constants.PROJECT_TITLE_FIELD: property[
                        constants.PROJECT_TITLE_FIELD
                    ],
                    constants.DESCRIPTION_FIELD: property[constants.DESCRIPTION_FIELD],
                    constants.ADDRESS_FIELD: property[constants.ADDRESS_FIELD],
                    constants.PRICE_FIELD: property[constants.PRICE_FIELD],
                    constants.IMAGES_FIELD: [
                        core_cloudfront.cloudfront_sign(image_key)
                        for image_key in property[constants.IMAGES_FIELD][:1]
                    ],
                    constants.LISTED_BY_FIELD: property[constants.LISTED_BY_FIELD],
                    constants.CREATED_AT_FIELD: property[constants.CREATED_AT_FIELD],
                    constants.LOCATION_FIELD: property[constants.LOCATION_FIELD],
                }
            )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "properties": response_list,
                "document_count": document_count,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Similar Properties Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Similar Properties Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Similar Properties Service")
    return response


def change_property_status(
    property_id: str,
    status: str,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Change Property Status Service")
    try:
        token = token_decoder(token)
        user_id = token.get(constants.ID)

        if status not in [property_status.value for property_status in PropertyStatus]:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Invalid Status It should be one of :"
                    + str([property_status.value for property_status in PropertyStatus])
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )
        if property_details is None:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't Found!"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        if property_details.get(constants.LISTED_BY_USER_ID_FIELD) != user_id:
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Property doesn't belongs to the user"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {"$set": {constants.STATUS_FIELD: status}},
        )

        logger.debug(f"Property Status Changed Successfully at Index {property_id}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Property Status Changed Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Change Property Status Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Change Property Status Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Change Property Status Service")
    return response


def add_todays_property_count():
    logger.debug("Inside Add Todays Property Count Service")
    try:
        customer_property_analytics_collection = db[
            constants.CUSTOMER_PROPERTY_ANALYTICS_SCHEMA
        ]
        customer_daily_property_analytics_collection = db[
            constants.CUSTOMER_DAILY_PROPERTY_ANALYTICS_SCHEMA
        ]
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_list = list(
            property_details_collection.find(
                {constants.STATUS_FIELD: PropertyStatus.ACTIVE.value},
                {
                    constants.INDEX_ID: 1,
                    constants.VIEW_COUNT_FIELD: 1,
                    constants.LISTED_BY_USER_ID_FIELD: 1,
                },
            )
        )
        for property in property_list:
            datetime_obj = datetime.utcfromtimestamp(time.time())

            formatted_date = datetime_obj.strftime("%Y-%m-%d")
            customer_daily_property_analytics_collection.insert_one(
                jsonable_encoder(
                    PropertyDailyViewCountSchema(
                        user_id=str(property.get(constants.LISTED_BY_USER_ID_FIELD)),
                        property_id=str(property.get(constants.INDEX_ID)),
                        view_count=property.get(constants.VIEW_COUNT_FIELD),
                        timestamp=time.time(),
                        data=formatted_date,
                    )
                )
            )

            previouse_count = customer_property_analytics_collection.find_one(
                {
                    constants.PROPERTY_ID_FIELD: str(property.get(constants.INDEX_ID)),
                }
            )
            print(previouse_count)
            if previouse_count is None:
                analytics_index = PropertyAnalyticsSchema(
                    user_id=str(property.get(constants.LISTED_BY_USER_ID_FIELD)),
                    property_id=str(property.get(constants.INDEX_ID)),
                    view_count=property.get(constants.VIEW_COUNT_FIELD),
                    timestamp=time.time(),
                )
            else:
                previous_count = previouse_count.get(constants.VIEW_COUNT_FIELD)
                todays_count = property.get(constants.VIEW_COUNT_FIELD) - previous_count
                analytics_index = PropertyAnalyticsSchema(
                    user_id=str(property.get(constants.LISTED_BY_USER_ID_FIELD)),
                    property_id=str(property.get(constants.INDEX_ID)),
                    view_count=todays_count,
                    timestamp=time.time(),
                )
            customer_property_analytics_collection.insert_one(
                jsonable_encoder(analytics_index)
            )

        logger.debug(f"Todays Property Count Added Successfully")

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Todays Property Count Added Successfully"},
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Add Todays Property Count Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Add Todays Property Count Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Todays Property Count Service")
    return response
