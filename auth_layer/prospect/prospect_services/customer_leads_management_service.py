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
from common_layer.common_services.oauth_handler import oauth2_scheme
from core_layer.aws_s3 import s3
from core_layer.aws_cloudfront import core_cloudfront
from auth_layer.prospect.prospect_schemas.customer_leads_management_schema import (
    ResponseMessage,
)


def get_investors_projects(token:str):
    logger.debug("Inside Get Investors Projects Service")
    try:
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Regions Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Investors Projects Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Investors Projects Service")
    return response
