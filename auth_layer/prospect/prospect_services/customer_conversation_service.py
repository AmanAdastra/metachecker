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
    CustomerConversationRequest,
)


def get_customer_conversations(page_number: int, per_page: int, token: str):
    logger.debug("Inside Get Customer Conversations Service")

    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        logger.debug("Getting Customer Conversation for User: " + str(user_id))

        customer_conversation_collection = db[constants.CUSTOMER_CONVERSATION_SCHEMA]

        customer_conversation = (
            customer_conversation_collection.find({"$or": [{constants.SENDER_ID_FIELD: user_id}, {constants.RECIEVER_ID_FIELD: user_id}]})
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )

        response_list = []

        for conversation in customer_conversation:
            conversation[constants.ID] = str(conversation[constants.INDEX_ID])
            del conversation[constants.INDEX_ID]
            response_list.append(conversation)

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "User Conversations Retrieved Successfully",
                "conversations": response_list,
            },
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Get Customer Conversation Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Customer Conversation Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Balance Service")
    return response

def get_customer_conversation_by_id(conversation_id: str, token: str):
    logger.debug("Inside Get Customer Conversation By Id Service")

    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        logger.debug("Get Customer Conversation for User: " + str(user_id))

        customer_conversation_collection = db[constants.CUSTOMER_CONVERSATION_SCHEMA]

        customer_conversation = customer_conversation_collection.find_one(
            {constants.INDEX_ID: ObjectId(conversation_id)}
        )

        if not customer_conversation:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Conversation Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        customer_conversation[constants.ID] = str(customer_conversation[constants.INDEX_ID])
        del customer_conversation[constants.INDEX_ID]

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "User Conversations Retrieved Successfully",
                "conversation": customer_conversation,
            },
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Get Customer Conversation Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Customer Conversation Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Customer Conversatione Service")
    return response

def add_customer_conversation(property_id: str, token: str):
    logger.debug("Inside Add Customer Conversation Service")

    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        logger.debug("Adding Conversation For the for User: " + str(user_id))

        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )

        if not property_details:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Property Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        reciever_id = property_details.get(constants.LISTED_BY_USER_ID_FIELD)

        customer_conversation_collection = db[constants.CUSTOMER_CONVERSATION_SCHEMA]

        if customer_conversation_collection.find_one(
            {
                constants.SENDER_ID_FIELD: user_id,
                constants.RECIEVER_ID_FIELD: reciever_id,
                constants.PROPERTY_ID_FIELD: property_id,
            }
        ):
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Conversation Already Exist"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        customer_conversation = jsonable_encoder(
            CustomerConversationInDB(
                sender_id=user_id,
                reciever_id=reciever_id,
                property_id=property_id,
                status="active",
            )
        )

        conversation_index = customer_conversation_collection.insert_one(
            customer_conversation
        )

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "Conversation Created",
                constants.ID: str(conversation_index.inserted_id),
            },
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Add Balance Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Balance Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From Add Customer Conversation Service")
    return response


def chat_with_customer(conversation_id: str, message: str, token: str):
    logger.debug("Inside Chat With Customer Service")

    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        user_type = decoded_token.get(constants.USER_TYPE_FIELD)
        logger.debug("Chatting with the User: " + str(user_id))

        customer_conversation_collection = db[constants.CUSTOMER_CONVERSATION_SCHEMA]

        customer_conversation = customer_conversation_collection.find_one(
            {constants.INDEX_ID: ObjectId(conversation_id)}
        )

        if not customer_conversation:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Conversation Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        customer_conversation_collection.update_one(
            {constants.INDEX_ID: ObjectId(conversation_id)},
            {
                "$push": {
                    "messages": {
                        "message": message,
                        "sender_id": user_id,
                        "message_id": str(uuid4()),
                        "created_at": time.time(),
                        "sender_type": user_type,
                    }
                }
            },
        )

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Message Sent Successfully"},
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Add Balance Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Chat with Customer: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Chat with Customer Service")
    return response
