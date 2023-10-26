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
                data={
                    constants.MESSAGE: f"Error in Digilocker Verification Service: {response['error']['message']}"
                },
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


def bank_account_transfer(data: kyc_schema.AccountTransfer):
    signzy_login = test_signzy_login()
    user_id = signzy_login.get("userId")
    access_token = signzy_login.get("id")
    data = dict(data)
    url = "https://preproduction.signzy.tech/api/v2/patrons/" + user_id + "/bankaccountverifications"
    payload = json.dumps(
        {
            "task": "bankTransfer",
            "essentials": {
                "beneficiaryAccount": data["bank_account"],
                "beneficiaryIFSC": data["bank_ifsc"],
                "beneficiaryMobile": "",
            },
        }
    )
    headers = {"Authorization": access_token, "Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)
    return response_dict


def verify_transfer(data: kyc_schema.VerifyTransfer):
    signzy_login = test_signzy_login()
    user_id = signzy_login.get("userId")
    access_token = signzy_login.get("id")
    data = dict(data)
    url = "https://preproduction.signzy.tech/api/v2/patrons/" + user_id + "/bankaccountverifications"
    payload = json.dumps(
        {
            "task": "verifyAmount",
            "essentials": {
                "amount": data["amount"],
                "signzyId": data["signzyId"],
            },
        }
    )
    headers = {"Authorization": access_token, "Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)
    return response_dict


def add_bank_account(request: kyc_schema.BankDetails, token):
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

        user_record = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})

        if not user_record:
            common_msg = ResponseMessage(
                type=constants.ERROR_MESSAGE,
                status=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.USER_DOES_NOT_EXIST},
            )
            return common_msg

        # Verify the ifsc code using razorpay
        URL = constants.RAZORPAY_IFSC_URL
        data = requests.get(URL + "/" + request.ifsc_code).json()
        if data == "Not Found":
            common_msg = ResponseMessage(
                type=constants.ERROR_MESSAGE,
                status=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: "IFSC Code not Found"},
            )
            return common_msg
        verify_data = {
            "bank_account": request.account_number,
            "bank_ifsc": request.ifsc_code,
        }
        try:
            response = bank_account_transfer(verify_data)
        except:
            common_msg = ResponseMessage(
                type=constants.ERROR_MESSAGE,
                status=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: "Invalid Bank Account Number"},
            )
            return common_msg

        if response["result"]["active"] == "no":
            common_msg = ResponseMessage(
                type=constants.ERROR_MESSAGE,
                status=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: "INVALID_BANK_ACCOUNT"},
            )
            return common_msg

        beneficiary_name = response["result"]["bankTransfer"]["beneName"]
        signzyReferenceId = response["result"]["signzyReferenceId"]
        beneficiary_ifsc = response["result"]["bankTransfer"]["beneIFSC"]
        signzy_data = {
            "amount": 1.01,
            "signzyId": signzyReferenceId,
        }
        response = verify_transfer(signzy_data)
        if response["result"]["amountMatch"]:
            owner_name = response["result"]["owerName"]
            if (
                owner_name.strip().lower() != beneficiary_name.strip().lower()
            ) and beneficiary_ifsc != request.ifsc_code:
                common_msg = ResponseMessage(
                    type=constants.ERROR_MESSAGE,
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        constants.MESSAGE: "Owner name and beneficiary Account Info does not match"
                    },
                )
                return common_msg
            else:
                bank_details = {
                    "user_id": user_id,
                    "account_number": request.account_number,
                    "ifsc_code": request.ifsc_code,
                    "beneficiary_name": beneficiary_name,
                    "signzyReferenceId": signzyReferenceId,
                    "beneficiary_ifsc": beneficiary_ifsc,
                    "branch_name": data["BRANCH"],
                    "bank_name": data["BANK"],
                }
                bank_details_collection = db["user_bank_account"]
                bank_details_collection.insert_one(bank_details)
                bank_details["_id"] = str(bank_details["_id"])
                response = {
                    "type": constants.HTTP_RESPONSE_SUCCESS,
                    "message": "Bank account added successfully",
                    "data": bank_details,
                }
                return response
        else:
            common_msg = ResponseMessage(
                type=constants.ERROR_MESSAGE,
                status=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: "BANK_ACCOUNT_VERIFICATION_FAILED"},
            )
            return common_msg
    except Exception as e:
        logger.error(f"Error in Digilocker Verification Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Digilocker Verification Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Digilocker Verification Service")
    return response
