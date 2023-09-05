from datetime import timedelta
import time
from http import HTTPStatus
from common_layer import constants
from common_layer.common_schemas import user_schema
from database import db
from admin_app.logging_module import logger
from common_layer.common_services.oauth_handler import (
    create_access_token,
    create_refresh_token,
    Hash,
)
from common_layer import roles


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

    user_details[constants.INDEX_ID] = str(user_details[constants.INDEX_ID])
    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={
            constants.ACCESS_TOKEN: access_token,
            constants.REFRESH_TOKEN: refresh_token,
            constants.USER_DETAILS: user_details,
            constants.ROLES_AND_PERMISSIONS: roles.permissions.get(user_details[constants.USER_TYPE_FIELD]),

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