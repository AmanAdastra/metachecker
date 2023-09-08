import time
from uuid import uuid4
from common_layer.common_services.utils import token_decoder
from prospect_app.logging_module import logger
from database import db
from common_layer import constants
from http import HTTPStatus
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from core_layer.aws_cloudfront.core_cloudfront import cloudfront_sign
from auth_layer.prospect.prospect_schemas.customer_conversation_schema import (
    ResponseMessage,
    CustomerConversationInDB,
)


def get_customer_conversations(page_number: int, per_page: int, token: str):
    logger.debug("Inside Get Customer Conversations Service")

    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        logger.debug("Getting User Wallet for User: " + str(user_id))

        customer_conversation_collection = db[constants.CUSTOMER_CONVERSATION_SCHEMA]

        customer_conversation = customer_conversation_collection.find(
            {constants.SENDER_ID_FIELD: user_id}
        ).skip((page_number - 1) * per_page).limit(per_page)

        response_list = []

        for conversation in customer_conversation:
            conversation[constants.ID] = str(conversation[constants.INDEX_ID])
            del conversation[constants.INDEX_ID]
            response_list.append(conversation)

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "User Wallet Retrieved Successfully"},
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Add Balance Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Balance Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Balance Service")
    return response
