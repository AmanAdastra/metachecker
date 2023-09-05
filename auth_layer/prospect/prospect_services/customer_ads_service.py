import time
import io
from typing import Annotated
from fastapi import Depends, HTTPException
from database import db
from bson import ObjectId
from common_layer import constants
from http import HTTPStatus
from admin_app.logging_module import logger
from fastapi.encoders import jsonable_encoder
from common_layer.common_services.utils import token_decoder
from auth_layer.admin.admin_schemas import admin_property_management_schemas
from common_layer.common_services.oauth_handler import oauth2_scheme
from core_layer.aws_s3 import s3
from core_layer.aws_cloudfront import core_cloudfront


def get_regions():
    logger.debug("Inside Get Regions Service")
    try:
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        regions = list(region_collection.find({constants.IS_ACTIVE_FIELD: True}).sort(constants.CREATED_AT_FIELD, -1))
        response_regions = []
        for region in regions:
            region[constants.ID] = str(region[constants.INDEX_ID])
            region["region_icon_image"] = core_cloudfront.cloudfront_sign(
                region[constants.ICON_IMAGE_FIELD]
            )
            del region[constants.INDEX_ID]
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