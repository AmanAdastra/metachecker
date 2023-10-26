from fastapi import status, HTTPException
import requests
import json
from common_layer import constants
from prospect_app.logging_module import logger
from core_layer.signzy_kyc import kyc_schema
from common_layer.common_services.utils import token_decoder
from common_layer.common_schemas.user_schema import ResponseMessage
from database import db
from http import HTTPStatus
from bson import ObjectId

def test_signzy_login():
    url = "https://preproduction.signzy.tech/api/v2/patrons/login"
    payload = json.dumps(
        {"username": constants.SIGNZY_USERNAME, "password": constants.SIGNZY_PASSWORD}
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)
    return response_dict


def digilocker():
    signzy_login = test_signzy_login()
    user_id = signzy_login.get("userId")
    access_token = signzy_login.get("id")
    url = (
        "https://preproduction.signzy.tech/api/v2/patrons/"
        + str(user_id)
        + "/digilockers"
    )
    payload = json.dumps({"task": "url", "essentials": {"signup": False}})
    headers = {"Content-Type": "application/json", "Authorization": access_token}
    response = requests.request("POST", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)
    if "error" in response_dict:
        return {
            "type": "error",
            "status": "400",
            "message": response_dict["error"]["message"],
        }
    data = {
        "type": "SUCCESS",
        "message": "Web Url fetched successfully",
        "data": {
            "web_url": response_dict["result"]["url"],
            "request_id": response_dict["result"]["requestId"],
        },
    }
    return data


def digilocker_verification(request_id):
    signzy_login = test_signzy_login()
    user_id = signzy_login.get("userId")
    access_token = signzy_login.get("id")
    url = (
        "https://preproduction.signzy.tech/api/v2/patrons/"
        + str(user_id)
        + "/digilockers"
    )
    payload = json.dumps(
        {"task": "getEadhaar", "essentials": {"requestId": str(request_id)}}
    )
    headers = {"Content-Type": "application/json", "Authorization": access_token}
    response = requests.request("POST", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)
    if "error" in response_dict:
        return response_dict
    return response_dict


def digilocker_verification_endpoint(
    request: kyc_schema.DigilockerVerificationRequest, token
):
    logger.debug("Inside Digilocker Verification Service")
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        logger.debug("Getting User Wallet for User: " + str(user_id))
        logger.debug(
            "Inside digilocker verification service function for user_id: {user_id}".format(
                user_id=user_id
            )
        )
        response = digilocker_verification(request_id=request.request_id)
        if "error" in response:
            response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Digilocker Verification Service: {response['error']['message']}"},
            status_code=HTTPStatus.NOT_ACCEPTABLE,
        )
            return response
        if user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)}):
            user_collection.update_one(
                {constants.INDEX_ID: ObjectId(user_id)},
                {constants.UPDATE_INDEX_DATA: {"kyc_verified": True}},
            )
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_SUCCESS,
                data={"message": "Kyc Completed"},
                status_code=HTTPStatus.ACCEPTED,
            )
            return response
        logger.debug("User not found")
    except Exception as e:
        logger.error(f"Error in Digilocker Verification Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Digilocker Verification Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Digilocker Verification Service")
    return response
