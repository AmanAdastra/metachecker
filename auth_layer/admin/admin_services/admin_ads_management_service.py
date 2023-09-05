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
from common_layer.common_services.utils import token_decoder, upload_image
from auth_layer.admin.admin_schemas import ads_management_schemas
from common_layer.common_services.oauth_handler import oauth2_scheme
from core_layer.aws_s3 import s3
from core_layer.aws_cloudfront import core_cloudfront


def get_welcome_card_info():
    logger.debug("Inside Get Welcome Card Info Service")
    try:
        welcome_card_info_collection = db[constants.WELCOME_CARD_DETAILS_SCHEMA]
        welcome_card_info = list(
            welcome_card_info_collection.find({}).sort(constants.CREATED_AT_FIELD, -1)
        )
        response_welcome_card_info = []
        for welcome_card in welcome_card_info:
            welcome_card[constants.ID] = str(welcome_card[constants.INDEX_ID])
            if welcome_card.get(constants.WELCOME_CARD_IMAGE_FIELD):
                welcome_card[constants.WELCOME_CARD_IMAGE_FIELD] = core_cloudfront.cloudfront_sign(
                welcome_card[constants.WELCOME_CARD_IMAGE_FIELD]
                )
            
            del welcome_card[constants.INDEX_ID]
            response_welcome_card_info.append(welcome_card)
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"welcome_card_info": response_welcome_card_info},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Welcome Card Info Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Welcome Card Info Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Welcome Card Info Service")
    return response


def add_welcome_card(
    request: ads_management_schemas.AddWelcomeCardRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Welcome Card Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Welcome Card Info added by User Id: {user_id}")

        welcome_card_info_collection = db[constants.WELCOME_CARD_DETAILS_SCHEMA]
        request.title = request.title.title()
        welcome_card_image_key = (
            f"{constants.WELCOME_CARD_BASE}/{request.title}.{constants.IMAGE_TYPE}"
        )
        validated_index = ads_management_schemas.WelcomeCardInDB(
            **request.dict(), welcome_card_image=welcome_card_image_key
        )
        request = jsonable_encoder(validated_index)
        welcome_card_info_collection.insert_one(request)
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Welcome Card Info Added Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Welcome Card Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Welcome Card Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Welcome Card Service")
    return response


def update_welcome_card(
    request: ads_management_schemas.UpdateWelcomeCardRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Welcome Card Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Welcome Card Info updated by User Id: {user_id}")
        welcome_card_info_collection = db[constants.WELCOME_CARD_DETAILS_SCHEMA]
        request.title = request.title.title()
        card_id = request.card_id
        validated_index = ads_management_schemas.UpdateWelcomeCardInDB(
            **request.model_dump()
        )
        request = jsonable_encoder(validated_index)
        welcome_card_info_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(card_id)},
            {constants.UPDATE_INDEX_DATA: request},
            return_document=True,
        )
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Welcome Card Info Updated Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update Welcome Card Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update Welcome Card Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Welcome Card Service")
    return response


def upload_welcome_card_image(card_id, welcome_card_image, token):
    logger.debug("Inside Add Welcome Card Image Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Welcome Card Image uploaded by User Id: {user_id}")
        welcome_card_details_collection = db[constants.WELCOME_CARD_DETAILS_SCHEMA]
        welcome_card_details = welcome_card_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(card_id)}
        )
        if not welcome_card_details:
            logger.error(f"Welcome Card with Id: {card_id} does not exist")
            response = ads_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Welcome Card with Id: {card_id} does not exist"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        base = constants.WELCOME_CARD_BASE

        image_upload_response = jsonable_encoder(
            upload_image(
                file=welcome_card_image, user_id=user_id, base=base, object_id=card_id
            )
        )
        if image_upload_response.get("type") == "error":
            return image_upload_response

        key = image_upload_response["data"]["key"]

        welcome_card_details_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(card_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.WELCOME_CARD_IMAGE_FIELD: key,
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
            return_document=True,
        )

        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.WELCOME_CARD_IMAGE_FIELD: key},
            status_code=HTTPStatus.OK,
        )

        return response

    except Exception as e:
        logger.error(f"Error in Add Welcome Card Image Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Welcome Card Image Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Welcome Card Image Service")
    return response


def update_welcome_card_image(card_id, welcome_card_image, token):
    logger.debug("Inside Update Welcome Card Image Service")
    try:
        response = upload_welcome_card_image(card_id, welcome_card_image, token)
        if response.status_code != HTTPStatus.OK:
            return response
        welcome_card_details_collection = db[constants.WELCOME_CARD_DETAILS_SCHEMA]
        welcome_card_details_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(card_id)},
            {constants.UPDATE_INDEX_DATA: {constants.UPDATED_AT_FIELD: time.time()}},
            return_document=True,
        )
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Welcome Card Image Updated Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update Welcome Card Image Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Update Welcome Card Image Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Welcome Card Image Service")
    return response


def add_ads_card(
    request: ads_management_schemas.AddAdsCardRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Ads Card Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Ads Card Info added by User Id: {user_id}")

        ads_card_info_collection = db[constants.ADS_CARD_DETAILS_SCHEMA]

        validated_index = ads_management_schemas.AdsInDB(
            title=request.title.title(),
            cta_text=request.cta_text,
            cta_url=request.cta_url,
        )

        request = jsonable_encoder(validated_index)
        index = ads_card_info_collection.insert_one(request)
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "Ads Card Info Added Successfully.",
                "card_id": str(index.inserted_id),
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Ads Card Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Ads Card Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Ads Card Service")
    return response


def update_ads_card(
    request: ads_management_schemas.UpdateAdsRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Ads Card Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Ads Card Info updated by User Id: {user_id}")
        ads_card_info_collection = db[constants.ADS_CARD_DETAILS_SCHEMA]
        request.title = request.title.title()
        card_id = request.card_id
        validated_index = ads_management_schemas.UpdateAdsInDB(**request.model_dump())
        request = jsonable_encoder(validated_index)
        index = ads_card_info_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(card_id)},
            {constants.UPDATE_INDEX_DATA: request},
            return_document=True,
        )
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "Ads Card Info Updated Successfully",
                "card_id": str(index.get(constants.INDEX_ID)),
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update Ads Card Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update Ads Card Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Ads Card Service")
    return response


def get_ads_card_info():
    logger.debug("Inside Get Ads Card Info Service")
    try:
        ads_card_info_collection = db[constants.ADS_CARD_DETAILS_SCHEMA]
        ads_card_info = list(
            ads_card_info_collection.find({}).sort(constants.CREATED_AT_FIELD, -1)
        )
        response_ads_card_info = []
        for ads_card in ads_card_info:
            ads_card[constants.ID] = str(ads_card[constants.INDEX_ID])
            if ads_card.get(constants.ADS_CARD_IMAGE_FIELD):
                ads_card[
                    constants.ADS_CARD_IMAGE_FIELD
                ] = core_cloudfront.cloudfront_sign(
                    ads_card[constants.ADS_CARD_IMAGE_FIELD]
                )
            del ads_card[constants.INDEX_ID]
            response_ads_card_info.append(ads_card)
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"ads_card_info": response_ads_card_info},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Ads Card Info Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Ads Card Info Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Ads Card Info Service")
    return response


def upload_ads_card_image(card_id, ads_card_image, token):
    logger.debug("Inside Add Ads Card Image Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Ads Card Image uploaded by User Id: {user_id}")
        ads_card_details_collection = db[constants.ADS_CARD_DETAILS_SCHEMA]
        ads_card_details = ads_card_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(card_id)}
        )
        if not ads_card_details:
            logger.error(f"Ads Card with Id: {card_id} does not exist")
            response = ads_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Ads Card with Id: {card_id} does not exist"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        base = constants.ADS_CARD_BASE

        image_upload_response = jsonable_encoder(
            upload_image(
                file=ads_card_image, user_id=user_id, base=base, object_id=card_id
            )
        )
        if image_upload_response.get("type") == "error":
            logger.error(f"Error in in uploading the image")
            return image_upload_response
        key = image_upload_response["data"]["key"]
        cloudfront_url = core_cloudfront.cloudfront_sign(key)
        ads_card_details_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(card_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.ADS_CARD_IMAGE_FIELD: key,
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
            return_document=True,
        )

        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.ADS_CARD_IMAGE_FIELD: cloudfront_url},
            status_code=HTTPStatus.OK,
        )

        return response

    except Exception as e:
        logger.error(f"Error in Add Ads Card Image Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Ads Card Image Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Ads Card Image Service")
    return response


def update_ads_card_image(card_id, ads_card_image, token):
    logger.debug("Inside Update Ads Card Image Service")
    try:
        response = upload_ads_card_image(card_id, ads_card_image, token)
        if response.status_code != HTTPStatus.OK:
            return response
        ads_card_details_collection = db[constants.ADS_CARD_DETAILS_SCHEMA]

        ads_card_details_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(card_id)},
            {constants.UPDATE_INDEX_DATA: {constants.UPDATED_AT_FIELD: time.time()}},
            return_document=True,
        )

        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Ads Card Image Updated Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update Ads Card Image Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update Ads Card Image Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Ads Card Image Service")
    return response


def add_cta_card(
    request: ads_management_schemas.AddCTARequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add CTA Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"CTA Info added by User Id: {user_id}")

        cta_card_info_collection = db[constants.CTA_CARD_DETAILS_SCHEMA]

        validated_index = ads_management_schemas.CTAInDB(
            title=request.title.title(),
            description=request.description,
            cta_text=request.cta_text,
            cta_url=request.cta_url,
        )

        request = jsonable_encoder(validated_index)
        index = cta_card_info_collection.insert_one(request)
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "CTA Info Added Successfully.",
                "card_id": str(index.inserted_id),
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add CTA Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add CTA Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add CTA Service")
    return response


def update_cta_card(
    request: ads_management_schemas.UpdateCTARequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update CTA Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"CTA Info updated by User Id: {user_id}")
        cta_card_info_collection = db[constants.CTA_CARD_DETAILS_SCHEMA]
        request.title = request.title.title()
        card_id = request.card_id
        validated_index = ads_management_schemas.UpdateCTAInDB(**request.model_dump())
        request = jsonable_encoder(validated_index)
        index = cta_card_info_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(card_id)},
            {constants.UPDATE_INDEX_DATA: request},
            return_document=True,
        )
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "CTA Info Updated Successfully",
                "card_id": str(index.get(constants.INDEX_ID)),
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update CTA Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update CTA Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update CTA Service")
    return response

def get_cta_card_info():
    logger.debug("Inside Get CTA Card Info Service")
    try:
        cta_card_info_collection = db[constants.CTA_CARD_DETAILS_SCHEMA]
        cta_card_info = list(
            cta_card_info_collection.find({}).sort(constants.CREATED_AT_FIELD, -1)
        )
        response_cta_card_info = []
        for cta_card in cta_card_info:
            cta_card[constants.ID] = str(cta_card[constants.INDEX_ID])
            if cta_card.get(constants.CTA_CARD_IMAGE_FIELD):
                cta_card[
                    constants.CTA_CARD_IMAGE_FIELD
                ] = core_cloudfront.cloudfront_sign(
                    cta_card[constants.CTA_CARD_IMAGE_FIELD]
                )
            del cta_card[constants.INDEX_ID]
            response_cta_card_info.append(cta_card)
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"cta_card_info": response_cta_card_info},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get CTA Card Info Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get CTA Card Info Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get CTA Card Info Service")
    return response


def upload_cta_card_image(card_id, cta_card_image, token):
    logger.debug("Inside Add CTA Card Image Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"CTA Card Image uploaded by User Id: {user_id}")
        cta_card_details_collection = db[constants.CTA_CARD_DETAILS_SCHEMA]
        cta_card_details = cta_card_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(card_id)}
        )
        if not cta_card_details:
            logger.error(f"CTA Card with Id: {card_id} does not exist")
            response = ads_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"CTA Card with Id: {card_id} does not exist"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        base = constants.CTA_CARD_BASE

        image_upload_response = jsonable_encoder(
            upload_image(
                file=cta_card_image, user_id=user_id, base=base, object_id=card_id
            )
        )
        if image_upload_response.get("type") == "error":
            return image_upload_response

        key = image_upload_response["data"]["key"]

        cta_card_details_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(card_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.CTA_CARD_IMAGE_FIELD: key,
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
            return_document=True,
        )

        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.CTA_CARD_IMAGE_FIELD: core_cloudfront.cloudfront_sign(key)},
            status_code=HTTPStatus.OK,
        )

        return response

    except Exception as e:
        logger.error(f"Error in Add CTA Card Image Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add CTA Card Image Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add CTA Card Image Service")
    return response


def update_cta_card_image(card_id, cta_card_image, token):
    logger.debug("Inside Update CTA Card Image Service")
    try:
        response = upload_cta_card_image(card_id, cta_card_image, token)
        if response.status_code != HTTPStatus.OK:
            return response
        cta_card_details_collection = db[constants.CTA_CARD_DETAILS_SCHEMA]

        cta_card_details_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(card_id)},
            {constants.UPDATE_INDEX_DATA: {constants.UPDATED_AT_FIELD: time.time()}},
            return_document=True,
        )

        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "CTA Card Image Updated Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update CTA Card Image Service: {e}")
        response = ads_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update CTA Card Image Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update CTA Card Image Service")
    return response