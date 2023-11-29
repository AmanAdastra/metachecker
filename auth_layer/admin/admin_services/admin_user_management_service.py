from datetime import timedelta
import time
import requests
from http import HTTPStatus
from common_layer import constants
from common_layer.common_schemas import user_schema
from database import db
from fastapi import UploadFile, Depends, Request
from typing import Annotated
from admin_app.logging_module import logger
from common_layer.common_services.oauth_handler import (
    create_access_token,
    create_refresh_token,
    Hash,
    oauth2_scheme,
)
from common_layer.common_services.utils import templates
from common_layer import roles
from bson import ObjectId
from common_layer.common_schemas.user_schema import ResponseMessage
from common_layer.common_services.utils import token_decoder
from core_layer.aws_cloudfront import core_cloudfront


def login_user(
    user_request: user_schema.AdminUserLogin,
):
    logger.debug(
        "User Login process started for user {email_id}".format(
            email_id=user_request.email_id
        )
    )

    user_collection = db[constants.USER_DETAILS_SCHEMA]

    user_details = user_collection.find_one(
        {constants.EMAIL_ID_FIELD: user_request.email_id}
    )
    if user_details is None:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: constants.USER_NOT_FOUND},
            status_code=HTTPStatus.NOT_FOUND,
        )
        return response

    if not user_details[constants.IS_ACTIVE_FIELD]:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: constants.USER_IS_INACTIVE},
            status_code=HTTPStatus.FORBIDDEN,
        )
        return response

    if user_details[constants.USER_TYPE_FIELD] == user_schema.UserTypes.CUSTOMER.value:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: constants.CUSTOMERS_NOT_ALLOWED},
            status_code=HTTPStatus.FORBIDDEN,
        )
        return response

    if not Hash.verify_password(
        user_details[constants.PASSWORD_FIELD], user_request.password
    ):
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: constants.PASSWORD_NOT_MATCH},
            status_code=HTTPStatus.FORBIDDEN,
        )
        return response

    subject = {
        constants.EMAIL_ID_FIELD: user_details[constants.EMAIL_ID_FIELD],
        constants.ID: str(user_details[constants.INDEX_ID]),
        constants.USER_TYPE_FIELD: user_details[constants.USER_TYPE_FIELD],
    }
    access_token = create_access_token(
        data=subject,
        expires_delta=timedelta(seconds=constants.ACCESS_TOKEN_EXPIRY_TIME),
    )
    refresh_token = create_refresh_token(data=subject)

    logger.debug(
        "User logged in successfully ! for user {email_id}".format(
            email_id=user_request.email_id
        )
    )
    user_collection.find_one_and_update(
        {constants.EMAIL_ID_FIELD: user_request.email_id},
        {constants.UPDATE_INDEX_DATA: {constants.LAST_LOGIN_AT: time.time()}},
    )

    user_details[constants.ID] = str(user_details[constants.INDEX_ID])
    user_details["profile_picture_url_key"] = core_cloudfront.cloudfront_sign(
        user_details["profile_picture_url_key"]
    )
    del user_details[constants.INDEX_ID]
    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={
            constants.ACCESS_TOKEN: access_token,
            constants.REFRESH_TOKEN: refresh_token,
            constants.USER_DETAILS: user_details,
            constants.ROLES_AND_PERMISSIONS: roles.permissions.get(
                user_details[constants.USER_TYPE_FIELD]
            ),
        },
        status_code=HTTPStatus.ACCEPTED,
    )
    return response


def get_users_list():
    logger.debug("Get Users List process started")
    user_collection = db[constants.USER_DETAILS_SCHEMA]
    user_list = list(user_collection.find().sort(constants.CREATED_AT_FIELD, -1))
    for user in user_list:
        user[constants.INDEX_ID] = str(user[constants.INDEX_ID])
    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={
            constants.USER_DETAILS: user_list,
        },
        status_code=HTTPStatus.ACCEPTED,
    )
    return response


# Upload Terms and Conditions Pdf into s3 bucket


def upload_terms_or_policy_txt_file(source_type, html_text, token):
    logger.debug("Upload Terms Or Policy Txt File process started")
    try:
        terms_and_policy_collection = db[constants.TERMS_AND_POLICY_SCHEMA]

        terms_and_policy_record = terms_and_policy_collection.find_one(
            {constants.SOURCE_TYPE_FIELD: source_type}
        )
        if terms_and_policy_record is None:
            terms_and_policy_collection.insert_one(
                {
                    "source_type": source_type,
                    "html_text": html_text,
                    constants.CREATED_AT_FIELD: time.time(),
                }
            )
        else:
            terms_and_policy_collection.find_one_and_update(
                {constants.SOURCE_TYPE_FIELD: source_type},
                {
                    constants.UPDATE_INDEX_DATA: {
                        "html_text": html_text,
                        constants.UPDATED_AT_FIELD: time.time(),
                    }
                },
            )
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Terms and Policy updated successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(str(e))
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={"message": "Error while uploading txt file"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    return response


def terms_and_policy_render(request, source_type):
    terms_and_policy_collection = db[constants.TERMS_AND_POLICY_SCHEMA]
    terms_and_policy_record = terms_and_policy_collection.find_one(
        {constants.SOURCE_TYPE_FIELD: source_type}
    )
    if terms_and_policy_record is None:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={"message": "No record found"},
            status_code=HTTPStatus.NOT_FOUND,
        )
        return response
    html_text = terms_and_policy_record.get("html_text")
    return templates.TemplateResponse(
        "privacy_policy.html",
        {"request": request, "source_type": source_type, "html_text": html_text},
    )


def get_terms_or_policy_html_text(source_type):
    try:
        terms_and_policy_collection = db[constants.TERMS_AND_POLICY_SCHEMA]
        terms_and_policy_record = terms_and_policy_collection.find_one(
            {constants.SOURCE_TYPE_FIELD: source_type}
        )
        if terms_and_policy_record is None:
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={"message": "No record found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        html_text = terms_and_policy_record.get("html_text")
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"html_text": html_text},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(str(e))
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={"message": "Error while getting html text"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    return response


def get_customers_transactions(
    page_number, per_page, transaction_type, userid, quantity, amount,avg_price, token
):
    logger.debug("Inside Get Customers Transactions Service")
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        admin_id = ObjectId(decoded_token.get(constants.ID))
        customer_transaction_details_collection = db[
            constants.CUSTOMER_TRANSACTION_SCHEMA
        ]

        filter_dict = {"user_id": (userid)}
        if transaction_type != "ALL":
            filter_dict["transaction_type"] = transaction_type

        if quantity != 0:
            filter_dict["transaction_quantity"] = {"$gte": quantity}

        if amount != 0:
            filter_dict["transaction_amount"] = {"$gte": amount}
        
        if avg_price != 0:
            filter_dict["transaction_avg_price"] = {"$gte": avg_price}

        customer_transaction_details = (
            customer_transaction_details_collection.find(
                filter_dict,
                {
                    "_id": 1,
                    "property_id": 1,
                    "transaction_type": 1,
                    "transaction_amount": 1,
                    "transaction_quantity": 1,
                    "transaction_avg_price": 1,
                    "transaction_id": 1,
                    "transaction_status": 1,
                    "transaction_date": 1,
                },
            )
            .sort("transaction_date", -1)
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        if customer_transaction_details is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Transaction Details Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        customer_transaction_details = list(customer_transaction_details)
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_ids = [
            ObjectId(transaction.get("property_id"))
            for transaction in customer_transaction_details
        ]
        property_details = property_details_collection.find(
            {constants.INDEX_ID: {"$in": property_ids}},
            {"project_title": 1, "_id": 1},
        )

        property_dict = {}
        for property_detail in property_details:
            property_dict[
                str(property_detail.get(constants.INDEX_ID))
            ] = property_detail.get("project_title")

        transactions = []
        for transaction in customer_transaction_details:
            transaction["_id"] = str(transaction.get("_id"))
            transaction["property_title"] = property_dict.get(
                transaction.get("property_id")
            )
            transactions.append(transaction)
        total_documents = customer_transaction_details_collection.count_documents(
            filter_dict
        )
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "transactions": transactions,
                "total_documents": total_documents,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Customers Transactions Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get Customers Transactions Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Customers Transactions Service")
    return response


def get_customers_fiat_transactions(
    page_number, per_page, transaction_type, userid, token
):
    logger.debug("Inside Get Customers Fiat Transactions Service")
    try:
        print(userid)
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        admin_id = ObjectId(decoded_token.get(constants.ID))
        customer_transaction_details_collection = db[
            constants.CUSTOMER_FIAT_TRANSACTIONS_SCHEMA
        ]

        filter_dict = {"user_id": (userid)}

        if transaction_type != "ALL":
            filter_dict["transaction_type"] = transaction_type

        customer_transaction_details = (
            customer_transaction_details_collection.find(
                filter_dict,
                {
                    "_id": 1,
                    "transaction_type": 1,
                    "transaction_amount": 1,
                    "transaction_id": 1,
                    "transaction_status": 1,
                    "transaction_date": 1,
                },
            )
            .sort("transaction_date", -1)
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        if customer_transaction_details is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Transaction Details Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        customer_transaction_details = list(customer_transaction_details)

        transactions = []
        for transaction in customer_transaction_details:
            transaction[constants.ID] = str(transaction.get("_id"))
            del transaction["_id"]
            transactions.append(transaction)

        total_documents = customer_transaction_details_collection.count_documents(
            filter_dict
        )
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "transactions": customer_transaction_details,
                "total_documents": total_documents,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Customers Fiat Transactions Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get Customers Fiat Transactions Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Customers Fiat Transactions Service")
    return response


def update_admin_details(request: user_schema.UpdateAdminDetail, token):
    logger.debug("Inside Update Admin Details Endpoint")
    token_details = token_decoder(token)
    user_id = token_details.get(constants.ID)
    user_collection = db[constants.USER_DETAILS_SCHEMA]
    user_details = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})
    request.password = Hash.get_password_hash(request.password)

    # Check if mobile number is already registered
    if request.mobile != user_details.get(constants.MOBILE_NUMBER_FIELD):
        user_exists = user_collection.find_one(
            {constants.MOBILE_NUMBER_FIELD: request.mobile}
        )
        if user_exists is not None:
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Mobile Number Already Registered"},
                status_code=HTTPStatus.CONFLICT,
            )
            return response

    if user_details is None:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: constants.USER_NOT_FOUND},
            status_code=HTTPStatus.NOT_FOUND,
        )
        return response
    user_collection.find_one_and_update(
        {constants.INDEX_ID: ObjectId(user_id)},
        {
            constants.UPDATE_INDEX_DATA: {
                "legal_name": request.legal_name,
                "email_id": request.email,
                "password": request.password,
                "mobile_number": request.mobile,
                constants.UPDATED_AT_FIELD: time.time(),
            }
        },
    )
    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={constants.MESSAGE: "User Details Updated Successfully"},
        status_code=HTTPStatus.ACCEPTED,
    )
    return response
