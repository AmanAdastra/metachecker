import jwt
from dateutil import relativedelta
from datetime import datetime
from prospect_app.logging_module import logger
from common_layer import constants
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email
from auth_layer.prospect.prospect_services import html_text
from fastapi import HTTPException, Header
from core_layer.firebase.firebase_services import firebase_service
from database import db
from bson import ObjectId
from http import HTTPStatus
import hashlib
import io
from core_layer.aws_s3 import s3
from common_layer.common_schemas.user_schema import ResponseMessage


def token_decoder(token):
    try:
        decoded_refresh_token = jwt.decode(
            token, constants.SECRET_KEY, algorithms=[constants.ALGORITHM]
        )
        logger.debug("Token Decoded Successfully")
        return decoded_refresh_token
    except:
        logger.debug("Token Decoding Failed")
        raise HTTPException(
            status_code=401, detail={"data": {"message": "Token Expired"}}
        )


def default_text(OTP):
    mobile_message = f"Dear User, your OTP is {OTP}. Please use this to validate your action and NEVER share this with anyone."
    return mobile_message


def send_sms_on_mobile(mobile_number, otp):
    logger.debug("Sending sms on mobile number : " + str(mobile_number))
    logger.debug("Otp : " + str(otp))

    body = default_text(otp)
    client = Client(constants.TWILIO_ACCOUNT_SID, constants.TWILIO_AUTH_TOKEN)
    try:
        client.messages.create(
            from_=constants.SENDER_PHONE_NUMBER, to=f"{mobile_number}", body=body
        )
    except Exception as e:
        logger.debug(str(e))


def send_email_otp(email_id, otp, subject):
    text = html_text.generate_otp(otp)
    subject = constants.EMAIL_OTP_FOR_REGISTRATION
    message = Mail(
        from_email=Email(constants.MY_EMAIL, "SquareF"),
        to_emails=email_id,
        subject=subject,
        html_content=text,
    )
    try:
        sg = SendGridAPIClient(constants.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.debug(response.status_code)
        logger.debug(response.body)
        logger.debug(response.headers)
    except Exception as e:
        logger.error(str(e))


def valid_content_length(
    content_length: int = Header(..., lt=constants.IMAGE_CONTENT_SIZE)
):
    return content_length


def fcm_push_notification(user_id, title, description, module, seconds=0, extra={}):
    device_collection = db[constants.DEVICE_DETAILS_SCHEMA]
    device_record = device_collection.find_one(
        {constants.USER_ID_FIELD: ObjectId(user_id)}
    )
    datetime_now = datetime.now()
    scheduled_time = datetime_now + relativedelta.relativedelta(seconds=seconds)
    time_stamp = scheduled_time.timestamp()
    time_stamp = float("{0:.3f}".format(time_stamp))
    firebase_data = {
        "to": device_record[constants.DEVICE_TOKEN_FIELD] if device_record else "",
        "title": title,
        "description": description,
        "is_scheduled": True,
        "scheduled_time": time_stamp,
        "module": module,
        "extra": extra,
    }
    logger.debug("FCM notification to user : " + str(user_id))
    response = firebase_service.push_notification_in_firebase(firebase_data)
    logger.debug("FCM notification response : " + str(response.json()))
    return response.json()


def upload_image(file, user_id, base, object_id):
    logger.debug("Inside the Upload Image Router")
    try:
        file_name = file.filename
        if file_name == "":
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Please select image"
            )
        hash_format = hashlib.sha256(file_name.encode())
        hashable_filename = str(hash_format.hexdigest())
        key = f"{base}/{user_id}/{object_id}/{hashable_filename}.{constants.IMAGE_TYPE}"
        contents = file.file.read()
        fileobj = io.BytesIO()
        fileobj.write(contents)
        fileobj.seek(0)
        response_status = s3.upload_file_via_upload_object_url(key, fileobj)
        if response_status != 204:
            raise HTTPException(
                status_code=e.status_code if hasattr(e, "status_code") else 500,
                detail="Error while uploading image",
            )
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"key": key},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(str(e))
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={"message": "Error while uploading image"},
            status_code=e.status_code if hasattr(e, "status_code") else 500
        )
    logger.debug("Returning from the Upload Image Router")
    return response

def get_nearest_region_id(location):
    region_collection = db[constants.REGION_DETAILS_SCHEMA]
    region_record = list(region_collection.find(
        {
            constants.LOCATION_FIELD: {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [location.get("longitude"), location.get("latitude")],
                    }
                }
            }
        }, {constants.INDEX_ID: 1}
    ).limit(1))
    return region_record if region_record else None

def upload_pdf(file, user_id, base, object_id):
    logger.debug("Inside the Upload PDF Router")
    try:
        file_name = file.filename
        if file_name == "":
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Please select pdf"
            )
        hash_format = hashlib.sha256(file_name.encode())
        hashable_filename = str(hash_format.hexdigest())
        key = f"{base}/{user_id}/{object_id}/{hashable_filename}.pdf"
        contents = file.file.read()
        fileobj = io.BytesIO()
        fileobj.write(contents)
        fileobj.seek(0)
        response_status = s3.upload_pdf_file_via_upload_object_url(key, fileobj)
        if response_status != 204:
            raise HTTPException(
                status_code=e.status_code if hasattr(e, "status_code") else 500,
                detail="Error while uploading pdf",
            )
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"key": key},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(str(e))
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={"message": "Error while uploading pdf"},
            status_code=e.status_code if hasattr(e, "status_code") else 500
        )
    logger.debug("Returning from the Upload PDF Router")
    return response