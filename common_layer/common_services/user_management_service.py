import time
import math
import os
import random
import hashlib
import jwt
import io
from bson import ObjectId
from http import HTTPStatus
from fastapi import HTTPException
from common_layer.common_schemas import user_schema
from database import db
from common_layer import constants
from fastapi.encoders import jsonable_encoder
from datetime import timedelta, datetime
from prospect_app.logging_module import logger
from fastapi.responses import FileResponse
from pydantic import EmailStr
from common_layer.common_services.utils import (
    send_sms_on_mobile,
    send_email_otp,
    token_decoder,
)
from core_layer.aws_s3 import s3
from common_layer.common_services.oauth_handler import (
    create_access_token,
    create_refresh_token,
    Hash,
    authenticate_user_by_username,
)
from common_layer.common_schemas.user_schema import UserTypes
from core_layer.aws_cloudfront import core_cloudfront
from auth_layer.prospect.prospect_schemas import device_details_schema
from common_layer import roles


def login_for_access_token(username: str, password: str, source: str = None):
    logger.debug(
        "User Login process started for user {email_id}".format(email_id=username)
    )
    user = authenticate_user_by_username(username, password)
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect mobile number or password"
        )
    if (
        source == constants.ADMIN_SOURCE
        and user.get(constants.USER_TYPE_FIELD) != UserTypes.SUPER_ADMIN.value
    ):
        logger.debug("User is not an admin user")
        raise HTTPException(status_code=400, detail="User is not an admin user")
    user = dict(user)
    data = {
        constants.ID: user.get(constants.INDEX_ID),
        constants.EMAIL_ID_FIELD: user.get(constants.EMAIL_ID_FIELD),
        constants.USER_TYPE_FIELD: user.get(constants.USER_TYPE_FIELD),
    }
    access_token_expires = timedelta(minutes=constants.ACCESS_TOKEN_EXPIRY_TIME)
    access_token = create_access_token(
        data=data,
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(data)

    return {
        constants.ACCESS_TOKEN: access_token,
        constants.REFRESH_TOKEN: refresh_token,
        constants.TOKEN_TYPE_KEY: constants.TOKEN_METHOD,
        constants.USER_TYPE_FIELD: user.get(constants.USER_TYPE_FIELD),
    }


def refresh_access_token(refresh_token: str):
    try:
        decoded_refresh_token = jwt.decode(
            refresh_token, constants.SECRET_KEY, algorithms=[constants.ALGORITHM]
        )
        if constants.TOKEN_EXPIRE_TIME_KEY not in decoded_refresh_token:
            raise jwt.InvalidTokenError(
                "Invalid refresh token. Missing 'expire' claim."
            )

        if (
            decoded_refresh_token.get(constants.TOKEN_TYPE_KEY)
            != constants.REFRESH_TOKEN
        ):
            raise jwt.InvalidTokenError(
                "Invalid token type. Token must be refresh Token."
            )

        refresh_token_expiration = datetime.utcfromtimestamp(
            decoded_refresh_token[constants.TOKEN_EXPIRE_TIME_KEY]
        )
        if refresh_token_expiration < datetime.utcnow():
            raise jwt.ExpiredSignatureError("Refresh token has expired.")

        user_data = {
            k: decoded_refresh_token[k]
            for k in decoded_refresh_token
            if k != constants.TOKEN_EXPIRE_TIME_KEY
        }
        data = {
            constants.ID: user_data.get(constants.INDEX_ID),
            constants.EMAIL_ID_FIELD: user_data.get(constants.EMAIL_ID_FIELD),
            constants.USER_TYPE_FIELD: user_data.get(constants.USER_TYPE_FIELD),
        }
        access_token_expires = timedelta(minutes=constants.ACCESS_TOKEN_EXPIRY_TIME)

        new_access_token = create_access_token(
            data=data,
            expires_delta=access_token_expires,
        )
        new_refresh_token = create_refresh_token(data)
        return {
            constants.ACCESS_TOKEN: new_access_token,
            constants.REFRESH_TOKEN: new_refresh_token,
            constants.TOKEN_TYPE_KEY: constants.TOKEN_METHOD,

        }

    except jwt.ExpiredSignatureError:
        response = user_schema.ResponseMessage(
            type="error",
            data={constants.MESSAGE: "Token Has Expired"},
            status_code=HTTPStatus.FORBIDDEN,
        )
        return response
    except jwt.InvalidTokenError as e:
        response = user_schema.ResponseMessage(
            type="error",
            data={constants.MESSAGE: f"{e}"},
            status_code=HTTPStatus.FORBIDDEN,
        )
        return response


def read_static_file(file_path: str):
    if os.path.isfile(f"./static/images/{file_path}.{constants.IMAGE_TYPE}"):
        response = FileResponse(f"./static/images/{file_path}.{constants.IMAGE_TYPE}")
        return response
    else:
        return {"type": "error", "message": "File not found"}


def delete_email_records(email_id: EmailStr):
    email_otp_collection = db[constants.EMAIL_OTP_DETAILS_SCHEMA]
    email_otp_collection.delete_one({constants.EMAIL_ID_FIELD: email_id})
    return {"type": constants.HTTP_RESPONSE_SUCCESS}


def generate_email_otp(email_id: EmailStr):
    digits = [i for i in range(0, 10)]
    OTP = ""
    for i in range(4):
        index = math.floor(random.random() * 10)
        OTP += str(digits[index])
    OTP = "1234"
    email_otp_collection = db[constants.EMAIL_OTP_DETAILS_SCHEMA]
    check_email = email_otp_collection.find_one({constants.EMAIL_ID_FIELD: email_id})
    if check_email:
        delete_email_records(email_id)
    passcode_details = user_schema.PasscodeDetails(email_id=email_id, email_otp=OTP)
    db_otp_details = jsonable_encoder(passcode_details)
    db_otp_details[constants.CREATED_AT_FIELD] = time.time()
    email_otp_collection.insert_one(db_otp_details)

    send_email_otp(email_id=email_id, otp=OTP, subject=constants.OTP_VERIFICATOIN_EMAIL)
    logger.debug("generated otp stored in database!")
    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={constants.MESSAGE: constants.EMAIL_OTP_SENT},
        status_code=HTTPStatus.ACCEPTED,
    )
    return response


def verify_email_otp(email_id: EmailStr, code: str):
    logger.debug(
        "Verification of code for Email started ! for email {email}".format(
            email=email_id
        )
    )
    code_details = db[constants.EMAIL_OTP_DETAILS_SCHEMA].find_one(
        {constants.EMAIL_ID_FIELD: email_id, constants.EMAIL_OTP_FIELD: code}
    )

    if not code_details:
        common_msg = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            status_code=HTTPStatus.FORBIDDEN,
            data={constants.MESSAGE: constants.OTP_NOT_GENERATED},
        )
        return common_msg

    time_diff = time.time() - code_details[constants.CREATED_AT_FIELD]
    minutes = time_diff / 60
    if minutes > 5:
        db[constants.EMAIL_OTP_DETAILS_SCHEMA].delete_one(
            {constants.EMAIL_ID_FIELD: email_id}
        )
        common_msg = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            status_code=HTTPStatus.FORBIDDEN,
            data={constants.MESSAGE: constants.OTP_DOES_NOT_MATCH},
        )
        return common_msg

    db[constants.EMAIL_OTP_DETAILS_SCHEMA].delete_one(
        {constants.EMAIL_ID_FIELD: email_id}
    )

    logger.debug("Verify code successfully ! for email {email}".format(email=email_id))
    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={constants.MESSAGE: constants.OTP_VERIFIED_SUCCESSFULLY},
        status_code=HTTPStatus.ACCEPTED,
    )
    return response


def generate_mobile_otp(mobile: str):
    mobile_otp_collection = db[constants.MOBILE_OTP_DETAILS_SCHEMA]

    digits = [i for i in range(0, 10)]
    OTP = ""
    for i in range(4):
        index = math.floor(random.random() * 10)
        OTP += str(digits[index])
    OTP = "1234"

    check_mobile = mobile_otp_collection.find_one(
        {constants.MOBILE_NUMBER_FIELD: mobile}
    )
    if check_mobile:
        mobile_otp_collection.delete_one({constants.MOBILE_NUMBER_FIELD: mobile})

    otp_entry = user_schema.MobileOtpDetails(mobile_number=mobile, mobile_otp=OTP)
    db_otp_details = jsonable_encoder(otp_entry)
    db_otp_details[constants.CREATED_AT_FIELD] = time.time()
    mobile_otp_collection.insert_one(db_otp_details)

    logger.debug("generated otp stored in database!")
    send_sms_on_mobile(mobile_number=mobile, otp=OTP)
    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={constants.MESSAGE: constants.MOBILE_OTP_SENT},
        status_code=HTTPStatus.ACCEPTED,
    )
    return response


def verify_mobile_otp(mobile: str, code: str):
    logger.debug(
        "Verification of mobile otp process started ! for mobile {mobile}".format(
            mobile=mobile
        )
    )

    code_details = db[constants.MOBILE_OTP_DETAILS_SCHEMA].find_one(
        {constants.MOBILE_NUMBER_FIELD: mobile, constants.MOBILE_OTP_FIELD: code}
    )
    if not code_details:
        common_msg = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            status_code=HTTPStatus.FORBIDDEN,
            data={constants.MESSAGE: constants.OTP_NOT_GENERATED},
        )
        return common_msg

    time_diff = time.time() - code_details[constants.CREATED_AT_FIELD]
    minutes = time_diff / 60
    if minutes > 5:
        db[constants.MOBILE_OTP_DETAILS_SCHEMA].delete_one(
            {constants.MOBILE_NUMBER_FIELD: mobile}
        )
        common_msg = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            status_code=HTTPStatus.FORBIDDEN,
            data={constants.MESSAGE: constants.OTP_DOES_NOT_MATCH},
        )
        return common_msg

    db[constants.MOBILE_OTP_DETAILS_SCHEMA].delete_one(
        {constants.MOBILE_NUMBER_FIELD: mobile}
    )

    logger.debug("Verify code successfully ! for mobile {mobile}".format(mobile=mobile))
    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={constants.MESSAGE: constants.OTP_VERIFIED_SUCCESSFULLY},
        status_code=HTTPStatus.ACCEPTED,
    )
    return response


def register_user(
    user_request: user_schema.RegisterRequest,
    device_details: device_details_schema.DeviceDetailsInput = None,
):
    user_collection = db[constants.USER_DETAILS_SCHEMA]
    device_collection = db[constants.DEVICE_DETAILS_SCHEMA]
    user_wallet_collection = db[constants.USER_WALLET_SCHEMA]

    user_details = user_collection.find_one(
        {
            constants.OR_INDEX_OPERATOR: [
                {constants.EMAIL_ID_FIELD: user_request.email_id},
                {constants.MOBILE_NUMBER_FIELD: user_request.mobile_number},
            ]
        }
    )

    if user_details:
        if user_details.get(constants.EMAIL_ID_FIELD) == user_request.email_id:
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: constants.EMAIL_ALREADY_USED},
                status_code=HTTPStatus.NOT_ACCEPTABLE,
            )
            logger.debug("Email Already Exist!")
            return response

        if (
            user_details.get(constants.MOBILE_NUMBER_FIELD)
            == user_request.mobile_number
        ):
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: constants.MOBLIE_NO_ALREADY_USED},
                status_code=HTTPStatus.NOT_ACCEPTABLE,
            )
            logger.debug("Mobile Number Already Exist!")
            return response

    if user_request.password != user_request.password_confirmed:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: constants.PASSWORD_NOT_MATCH},
            status_code=HTTPStatus.NOT_ACCEPTABLE,
        )
        logger.debug("Password and Confirm Password did not Match!")
        return response

    user_request.password = Hash.get_password_hash(user_request.password)
    username = user_request.email_id.split("@")[0] + user_request.mobile_number[-4:]
    validated_index = user_schema.Register(
        username=username,
        legal_name=user_request.legal_name,
        email_id=user_request.email_id,
        password=user_request.password,
        mobile_number=user_request.mobile_number,
        password_confirmed=user_request.password_confirmed,
        user_type=user_request.user_type,
    )
    collection_index = jsonable_encoder(validated_index)
    inserted_index = user_collection.insert_one(collection_index)

    user_id = str(inserted_index.inserted_id)

    if user_request.user_type in [UserTypes.CUSTOMER.value, UserTypes.PARTNER.value]:
        device_collection.insert_one(
            jsonable_encoder(
                device_details_schema.DeviceDetails(
                    user_id=user_id,
                    device_id=device_details.device_id if device_details else "",
                    device_token=device_details.device_token if device_details else "",
                )
            )
        )
        logger.debug("Device Details Created")

        user_wallet = user_schema.UserWallet(user_id=user_id)
        user_wallet_collection.insert_one(jsonable_encoder(user_wallet))
        logger.debug("User wallet Created")

    subject = {
        constants.EMAIL_ID_FIELD: user_request.email_id,
        constants.ID: user_id,
        constants.USER_TYPE_FIELD: user_request.user_type,
    }
    access_token = create_access_token(
        data=subject,
        expires_delta=timedelta(seconds=constants.ACCESS_TOKEN_EXPIRY_TIME),
    )
    refresh_token = create_refresh_token(
        data=subject,
    )
    logger.debug("Access token and Refress Token Created")

    key = f"{constants.PROFILE_PICTURE_BASE}/{user_id}/{constants.PROFILE_PICTURE_PATH}"

    user_collection.find_one_and_update(
        {constants.INDEX_ID: inserted_index.inserted_id},
        {constants.UPDATE_INDEX_DATA: {constants.PROFILE_PICTURE_FIELD: key}},
    )

    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={
            constants.USER_DETAILS: validated_index,
            constants.INDEX_ID: str(inserted_index.inserted_id),
            constants.ACCESS_TOKEN: access_token,
            constants.REFRESH_TOKEN: refresh_token,
            constants.PROFILE_PICTURE_FIELD: key,
            constants.ROLES_AND_PERMISSIONS: roles.permissions.get(
                user_request.user_type
            ),
        },
        status_code=HTTPStatus.ACCEPTED,
    )
    return response


def get_user_details(token: str):
    decoded_token = token_decoder(token)
    try:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: "Fetched User Details",
                constants.ID: decoded_token.get(constants.ID),
                constants.EMAIL_ID_FIELD: decoded_token.get(constants.EMAIL_ID_FIELD),
            },
            status_code=HTTPStatus.ACCEPTED,
        )

        return response
    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: e},
            status_code=HTTPStatus.FORBIDDEN,
        )

        return response


def check_user_exist(mobile_number: str):
    user_collection = db[constants.USER_DETAILS_SCHEMA]
    user_details = user_collection.find_one(
        {constants.MOBILE_NUMBER_FIELD: mobile_number}
    )

    if user_details is None:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: constants.USER_NOT_FOUND},
            status_code=HTTPStatus.NOT_FOUND,
        )
        return response

    if (
        user_details
        and user_details.get(constants.MOBILE_NUMBER_FIELD)
        and user_details.get(constants.SECURE_PIN_FIELD)
    ):
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: constants.PROFILE_DETAILS_COMPLETED},
            status_code=HTTPStatus.ACCEPTED,
        )
        return response
    response = user_schema.ResponseMessage(
        type=constants.HTTP_RESPONSE_FAILURE,
        data={constants.MESSAGE: constants.PROFILE_DETAILS_INCOMPLETE},
        status_code=HTTPStatus.PARTIAL_CONTENT,
    )
    return response


def add_secure_pin(secure_pin: str, token: str):
    decoded_token = token_decoder(token)
    try:
        user_id = ObjectId(decoded_token.get(constants.ID))
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_details = user_collection.find_one({constants.INDEX_ID: user_id})
        if user_details is None:
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_SUCCESS,
                data={
                    constants.MESSAGE: constants.USER_NOT_FOUND,
                },
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        user_collection.find_one_and_update(
            {constants.INDEX_ID: user_id},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.SECURE_PIN_FIELD: secure_pin,
                    constants.SECURE_PIN_SET_FIELD: True,
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
        )

        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: constants.SECURE_PIN_CHANGED,
            },
            status_code=HTTPStatus.ACCEPTED,
        )
        return response
    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: e},
            status_code=HTTPStatus.FORBIDDEN,
        )

        return response


def update_secure_pin(secure_pin: str, token: str):
    decoded_token = token_decoder(token)
    try:
        user_id = ObjectId(decoded_token.get(constants.ID))
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_details = user_collection.find_one({constants.INDEX_ID: user_id})
        if user_details is None:
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_SUCCESS,
                data={
                    constants.MESSAGE: constants.USER_DOES_NOT_EXIST,
                },
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        user_collection.find_one_and_update(
            {constants.INDEX_ID: user_id},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.SECURE_PIN_FIELD: secure_pin,
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
        )

        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: constants.SECURE_PIN_UPDATED,
            },
            status_code=HTTPStatus.ACCEPTED,
        )
        return response
    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: e},
            status_code=HTTPStatus.FORBIDDEN,
        )

        return response


def post_profile_picture(profile_image, token):
    logger.debug("Inside the Post Profile Picture Service")
    decoded_token = token_decoder(token)
    try:
        user_id = ObjectId(decoded_token.get(constants.ID))
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_details = user_collection.find_one({constants.INDEX_ID: user_id})
        if user_details is None:
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: constants.USER_DOES_NOT_EXIST,
                },
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        profile_key = user_details.get(constants.PROFILE_PICTURE_FIELD)
        if profile_key and user_details.get(constants.PROFILE_PICTURE_UPLOADED_FIELD):
            s3.delete_uploaded_object(profile_key)
        file_name = profile_image.filename
        if file_name == "":
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Please select image"
            )
        hash_format = hashlib.sha256(file_name.encode())
        hashable_filename = str(hash_format.hexdigest())
        key = f"{constants.PROFILE_PICTURE_BASE}/{user_id}/{hashable_filename}.{constants.IMAGE_TYPE}"
        contents = profile_image.file.read()
        fileobj = io.BytesIO()
        fileobj.write(contents)
        fileobj.seek(0)
        response_status = s3.upload_file_via_upload_object_url(key, fileobj)
        user_collection.find_one_and_update(
            {constants.INDEX_ID: user_id},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.PROFILE_PICTURE_UPLOADED_FIELD: True,
                    constants.UPDATED_AT_FIELD: time.time(),
                    constants.PROFILE_PICTURE_FIELD: key,
                }
            },
        )

        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: constants.PROFILE_PICTURE_UPLOADED,
            },
            status_code=response_status,
        )
        return response
    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: e},
            status_code=HTTPStatus.FORBIDDEN,
        )

        return response


def get_profile_picture(token):
    logger.debug("Inside the Get Profile Picture Service")
    decoded_token = token_decoder(token)
    try:
        user_id = ObjectId(decoded_token.get(constants.ID))
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_details = user_collection.find_one({constants.INDEX_ID: user_id})
        if user_details is None:
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: constants.USER_NOT_FOUND,
                },
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        key = user_details.get(constants.PROFILE_PICTURE_FIELD)
        profile_picture_url = core_cloudfront.cloudfront_sign(key)

        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.MESSAGE: constants.PROFILE_PICTURE_FETCHED,
                constants.PROFILE_PICTURE_FIELD: profile_picture_url,
            },
            status_code=HTTPStatus.ACCEPTED,
        )
        return response
    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: e},
            status_code=HTTPStatus.FORBIDDEN,
        )

        return response


def update_mobile_number(mobile_number, token):
    logger.debug("Inside Update Mobile Number Endpoint")
    decoded_token = token_decoder(token)
    user_id = decoded_token.get(constants.ID)
    try:
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(user_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.MOBILE_NUMBER_FIELD: mobile_number,
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
        )
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Mobile Number Updated Successfully"},
            status_code=HTTPStatus.ACCEPTED,
        )
    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: "Mobile Number Update Failed"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
    return response


def update_email_id(email_id, token):
    logger.debug("Inside Update Email Id Endpoint")
    decoded_token = token_decoder(token)
    user_id = decoded_token.get(constants.ID)
    try:
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(user_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.EMAIL_ID_FIELD: email_id,
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
        )
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Email Id Updated Successfully"},
            status_code=HTTPStatus.ACCEPTED,
        )
    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: "Email Id Update Failed"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
    return response


def change_password(old_password, new_password, token):
    logger.debug("Inside Change Password Endpoint")
    decoded_token = token_decoder(token)
    user_id = decoded_token.get(constants.ID)
    try:
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_details = user_collection.find_one({constants.INDEX_ID: ObjectId(user_id)})
        if not Hash.verify_password(
            user_details[constants.PASSWORD_FIELD], old_password
        ):
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: constants.PASSWORD_NOT_MATCH},
                status_code=HTTPStatus.FORBIDDEN,
            )
            return response
        user_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(user_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.PASSWORD_FIELD: Hash.get_password_hash(new_password),
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
        )
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Password Updated Successfully"},
            status_code=HTTPStatus.ACCEPTED,
        )
    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: "Password Update Failed"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
    return response


def convert_investor_to_customer(token):
    logger.debug("Inside Convert Investor to Customer Endpoint")
    decoded_token = token_decoder(token)
    user_id = decoded_token.get(constants.ID)
    try:
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(user_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.USER_TYPE_FIELD: UserTypes.CUSTOMER.value,
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
        )
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "User Type Updated Successfully"},
            status_code=HTTPStatus.ACCEPTED,
        )
    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: "User Type Update Failed"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
    return response


def reset_user_password(mobile_number: str, password: str):
    logger.debug("Inside Reset Password Endpoint")
    try:
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_details = user_collection.find_one(
            {constants.MOBILE_NUMBER_FIELD: mobile_number}
        )
        if user_details is None:
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: constants.USER_NOT_FOUND},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        user_collection.find_one_and_update(
            {constants.MOBILE_NUMBER_FIELD: mobile_number},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.PASSWORD_FIELD: Hash.get_password_hash(password),
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
        )
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Password Updated Successfully"},
            status_code=HTTPStatus.ACCEPTED,
        )
        return response

    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: "Password Update Failed"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
        return response


def reset_admin_password(email_id: str, password: str):
    logger.debug("Inside Reset Password Endpoint")
    try:
        user_collection = db[constants.USER_DETAILS_SCHEMA]
        user_details = user_collection.find_one({constants.EMAIL_ID_FIELD: email_id})
        if user_details is None:
            response = user_schema.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: constants.USER_NOT_FOUND},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        user_collection.find_one_and_update(
            {constants.EMAIL_ID_FIELD: email_id},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.PASSWORD_FIELD: Hash.get_password_hash(password),
                    constants.UPDATED_AT_FIELD: time.time(),
                }
            },
        )
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.MESSAGE: "Password Updated Successfully"},
            status_code=HTTPStatus.ACCEPTED,
        )
        return response

    except Exception as e:
        response = user_schema.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: "Password Update Failed"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
        return response
