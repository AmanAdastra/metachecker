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
from fastapi.encoders import jsonable_encoder


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


def add_bank_account(request: kyc_schema.BankDetails, token):
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        bank_account_collection = db[constants.CUSTOMER_BANK_DETAILS_SCHEMA]
        logger.debug("Getting User Wallet for User: " + str(user_id))
        logger.debug(
            "Inside Add Bank Account Service function for user_id: {user_id}".format(
                user_id=user_id
            )
        )
        user_record = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})
        if not user_record:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.USER_DOES_NOT_EXIST},
            )
            return common_msg

        if bank_account_collection.find_one(
            {constants.ACCOUNT_NUMBER: request.account_number}
        ):
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: constants.BANK_ACCOUNT_ALREADY_EXIST},
            )
            return common_msg

        if bank_account_collection.find_one({constants.IS_PRIMARY_ACCOUNT: True}):
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: constants.PRIMARY_ACCOUNT_EXIST},
            )
            return common_msg

        bank_details = jsonable_encoder(request)
        bank_details[constants.USER_ID_FIELD] = user_id
        inserted_id = bank_account_collection.insert_one(bank_details).inserted_id
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            status_code=status.HTTP_202_ACCEPTED,
            data={constants.MESSAGE: "Account Added Successfully", constants.ID:str(inserted_id)},
        )
        return response

    except Exception as e:
        logger.error(f"Error in Add Bank Account Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Bank Account Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Bank Account Service")
    return response


# Edit this
def update_bank_account(request: kyc_schema.UpdateBankDetailsSchema, token):
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        bank_account_collection = db[constants.CUSTOMER_BANK_DETAILS_SCHEMA]
        logger.debug("Getting User Wallet for User: " + str(user_id))
        logger.debug(
            "Inside Update Bank Account function for user_id: {user_id}".format(
                user_id=user_id
            )
        )
        user_record = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})
        if not user_record:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.USER_DOES_NOT_EXIST},
            )
            return common_msg

        if not bank_account_collection.find_one(
            {constants.INDEX_ID: ObjectId(request.record_id)}
        ):
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.RECORD_DOES_NOT_FOUND},
            )
            return common_msg

        if request.is_primary and bank_account_collection.find_one(
            {constants.USER_ID_FIELD: user_id, constants.IS_PRIMARY_ACCOUNT: True}
        ):
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: constants.PRIMARY_ACCOUNT_EXIST},
            )
            return common_msg

        updated_data = jsonable_encoder(request)
        del updated_data["record_id"]
        bank_account_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(request.record_id)},
            {constants.UPDATE_INDEX_DATA: updated_data},
        )

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            status_code=status.HTTP_202_ACCEPTED,
            data={constants.MESSAGE: "Account Updated Successfully"},
        )
        return response

    except Exception as e:
        logger.error(f"Error in Update Bank Account Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update Bank Account Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Bank Account Service")
    return response


def get_bank_account_details(token):
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        bank_account_collection = db[constants.CUSTOMER_BANK_DETAILS_SCHEMA]
        logger.debug("Getting User Wallet for User: " + str(user_id))
        logger.debug(
            "Inside Get Bank Account function for user_id: {user_id}".format(
                user_id=user_id
            )
        )
        user_record = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})
        if not user_record:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.USER_DOES_NOT_EXIST},
            )
            return common_msg

        bank_details = bank_account_collection.find({constants.USER_ID_FIELD: user_id})
        if bank_details is None:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: "Bank Deails Not Found"},
            )
            return common_msg
        bank_details_list = []
        for details in bank_details:
            details[constants.ID] = str(details[constants.INDEX_ID])
            del details[constants.INDEX_ID]
            bank_details_list.append(details)

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            status_code=status.HTTP_200_OK,
            data={
                constants.MESSAGE: "Get Bank Details Successfully",
                "data": bank_details_list,
            },
        )
        return response

    except Exception as e:
        logger.error(f"Error in Get Bank Account Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Bank Account Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Bank Account Service")
    return response


def delete_bank_account_details(record_id: str, token):
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        bank_account_collection = db[constants.CUSTOMER_BANK_DETAILS_SCHEMA]
        logger.debug("Getting User Wallet for User: " + str(user_id))
        logger.debug(
            "Inside Delete Bank Account function for user_id: {user_id}".format(
                user_id=user_id
            )
        )
        user_record = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})
        if not user_record:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.USER_DOES_NOT_EXIST},
            )
            return common_msg
        bank_record = bank_account_collection.find_one(
            {constants.INDEX_ID: ObjectId(record_id)}
        )
        if not bank_record:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.RECORD_DOES_NOT_FOUND},
            )
            return common_msg

        if bank_record.get(constants.IS_PRIMARY_ACCOUNT):
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: constants.DELETE_PRIMARY_ACCOUNT},
            )
            return common_msg

        bank_account_collection.delete_one({constants.INDEX_ID: ObjectId(record_id)})

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            status_code=status.HTTP_200_OK,
            data={constants.MESSAGE: "Bank Account Deleted Successfully!"},
        )
        return response

    except Exception as e:
        logger.error(f"Error in Delete Bank Account Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Delete Bank Account Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Delete Bank Account Service")
    return response


def add_kyc_details(request: kyc_schema.KycDetailsSchema, token):
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        customer_kyc_collection = db[constants.CUSTOMER_KYC_DETAILS_SCHEMA]
        logger.debug(
            "Inside Add Kyc Details Service function for user_id: {user_id}".format(
                user_id=user_id
            )
        )
        user_record = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})
        if not user_record:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.USER_DOES_NOT_EXIST},
            )
            return common_msg

        if customer_kyc_collection.find_one(
            {constants.AADHAR_NUMBER: request.aadhar_number}
        ):
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: constants.AADHAR_ALREADY_EXIST},
            )
            return common_msg

        if customer_kyc_collection.find_one({constants.PAN_NUMBER: request.pan_number}):
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: constants.PAN_NUMBER_ALREADY_EXIST},
            )
            return common_msg

        kyc_details = jsonable_encoder(request)
        print(kyc_details,"kyc details")
        kyc_details[constants.USER_ID_FIELD] = user_id
        inserted_id = customer_kyc_collection.insert_one(kyc_details).inserted_id
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            status_code=status.HTTP_202_ACCEPTED,
            data={
                constants.MESSAGE: "Account Added Successfully",
                constants.ID: str(inserted_id),
            },
        )
        return response

    except Exception as e:
        logger.error(f"Error in Add Bank Account Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Bank Account Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Bank Account Service")
    return response


def update_kyc_details(request: kyc_schema.UpdateBankDetailsSchema, token):
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        customer_kyc_collection = db[constants.CUSTOMER_KYC_DETAILS_SCHEMA]
        logger.debug(
            "Inside Update Kyc Details Service function for user_id: {user_id}".format(
                user_id=user_id
            )
        )
        user_record = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})
        if not user_record:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.USER_DOES_NOT_EXIST},
            )
            return common_msg

        if customer_kyc_collection.find_one(
            {
                constants.AADHAR_NUMBER: request.aadhar_number,
                constants.USER_ID_FIELD: {constants.NOT_EQUAL_TO_OPERATOR: user_id},
            }
        ):
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: constants.AADHAR_ALREADY_EXIST},
            )
            return common_msg

        if customer_kyc_collection.find_one(
            {
                constants.PAN_NUMBER: request.pan_number,
                constants.USER_ID_FIELD: {constants.NOT_EQUAL_TO_OPERATOR: user_id},
            }
        ):
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_400_BAD_REQUEST,
                data={constants.MESSAGE: constants.PAN_NUMBER_ALREADY_EXIST},
            )
            return common_msg

        updated_data = jsonable_encoder(request)
        del updated_data["record_id"]
        customer_kyc_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(request.record_id)},
            {constants.UPDATE_INDEX_DATA: updated_data},
        )

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            status_code=status.HTTP_202_ACCEPTED,
            data={
                constants.MESSAGE: "Kyc Details Updated Successfully",
            },
        )
        return response

    except Exception as e:
        logger.error(f"Error in Update KYC Details Account Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Bank Account Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update KYC Details Service")
    return response

def get_kyc_details(token):
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        customer_kyc_collection = db[constants.CUSTOMER_KYC_DETAILS_SCHEMA]
        logger.debug(
            "Inside Get KYC Details function for user_id: {user_id}".format(
                user_id=user_id
            )
        )
        user_record = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})
        if not user_record:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: constants.USER_DOES_NOT_EXIST},
            )
            return common_msg

        kyc_details = customer_kyc_collection.find({constants.USER_ID_FIELD: user_id})
        if kyc_details is None:
            common_msg = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                status_code=status.HTTP_404_NOT_FOUND,
                data={constants.MESSAGE: "KYC Deails Not Found"},
            )
            return common_msg
        kyc_details = list(kyc_details)[0]
        print(kyc_details,"kyc details")
        kyc_details[constants.ID] = str(kyc_details.get(constants.INDEX_ID))
        del kyc_details[constants.INDEX_ID]
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            status_code=status.HTTP_200_OK,
            data={
                constants.MESSAGE: "Get KYC Details Successfully",
                "data": kyc_details,
            },
        )
        return response

    except Exception as e:
        logger.error(f"Error in Get KYC Details Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get KYC Details Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get KYC Details Service")
    return response
