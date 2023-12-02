from fastapi import APIRouter, Depends, Form, UploadFile, File, Query
from common_layer.common_schemas import user_schema
from logging_module import logger
from pydantic import EmailStr
from typing import Annotated
from auth_layer.prospect.prospect_schemas import device_details_schema
from common_layer.common_services import user_management_service
from common_layer.common_services.oauth_handler import oauth2_scheme
from common_layer.common_services.utils import valid_content_length
from fastapi.security import OAuth2PasswordRequestForm
from auth_layer.prospect.prospect_services import customer_management_service
from auth_layer.admin.admin_services import admin_ads_management_service
from common_layer import constants

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
    tags=["USER MANAGEMENT"],
)


@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    logger.debug("Inside Login For Access Token Router")
    response = user_management_service.login_for_access_token(
        form_data.username, form_data.password, constants.PROSPECT_SOURCE
    )
    logger.debug("Returning from Login For Access Token Router")
    return response


@router.get("/static/{file_path:path}")
def read_static_file(file_path: str):
    logger.debug("Inside Read Static Files Router")
    response = user_management_service.read_static_file(file_path)
    logger.debug("Returning from Read Static Files Router")
    return response


@router.post("/register")
def register_user(
    user_request: user_schema.RegisterRequest,
    device_details: device_details_schema.DeviceDetailsInput,
):
    logger.debug("Inside the Register User Router")
    response = user_management_service.register_user(user_request, device_details)
    logger.debug("Returning from the Register User Router")
    return response


@router.post("/login")
def login_user(
    user_request: user_schema.UserLogin,
    device_details: device_details_schema.DeviceDetailsInput,
):
    logger.debug("Inside the Login User Router")
    response = customer_management_service.login_user(user_request, device_details)
    logger.debug("Returning from the Login User Router")
    return response


@router.post("/generate-mobile-otp")
def generate_mobile_otp(mobile: str):
    logger.debug("Inside Generate Mobile OTP Router")
    response = user_management_service.generate_mobile_otp(mobile)
    logger.debug("Returning from Generate Mobile OTP Router")
    return response


@router.post("/verify-mobile-otp")
def verify_mobile_otp(mobile: str, code: str):
    logger.debug("Inside Verify Mobile OTP Router")
    response = user_management_service.verify_mobile_otp(mobile, code)
    logger.debug("Returning from Verify Mobile OTP Router")
    return response


@router.post("/generate-email-otp")
def generate_email_otp(email_id: EmailStr):
    logger.debug("Inside Generate Email OTP Router")
    response = user_management_service.generate_email_otp(email_id)
    logger.debug("Returning from Generate Email OTP Router")
    return response


@router.post("/verify-email-otp")
def verify_email_otp(email_id: EmailStr, code: str):
    logger.debug("Inside Verify Email OTP Router")
    response = user_management_service.verify_email_otp(email_id, code)
    logger.debug("Returning from Verify Email OTP Router")
    return response


@router.get("/get-user-details")
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside Get User Details Router")
    response = user_management_service.get_user_details(token)
    logger.debug("Returning From the Get User Details Router")
    return response


@router.post("/refresh-access-token")
def refresh_access_token(refresh_token: str = Form(...)):
    logger.debug("Inside Get Refresh Token Router")
    response = user_management_service.refresh_access_token(refresh_token)
    logger.debug("Returning From the Get Refresh Token Router")
    return response


@router.get("/check-user-exist")
def check_user_exist(mobile_number: str):
    logger.debug("Inside the Check User Exist Router")
    response = user_management_service.check_user_exist(mobile_number)
    logger.debug("Returning from Check User Exist Router")
    return response


@router.post("/add-secure-pin")
def add_secure_pin(secure_pin: str, token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside the Add Secure Pin Router")
    response = user_management_service.add_secure_pin(secure_pin, token)
    logger.debug("Returning from Add Secure Pin Router")
    return response


@router.put("/update-secure-pin")
def update_secure_pin(secure_pin: str, token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside the Update Secure Pin Router")
    response = user_management_service.update_secure_pin(secure_pin, token)
    logger.debug("Returning from Update Secure Pin Router")
    return response

@router.put("/forgot-secure-pin")
def forgot_secure_pin(mobile_number: str, secure_pin: str):
    logger.debug("Inside the Forgot Secure Pin Router")
    response = user_management_service.forgot_secure_pin(mobile_number, secure_pin)
    logger.debug("Returning from Forgot Secure Pin Router")
    return response


@router.post("/post-profile-picture", dependencies=[Depends(valid_content_length)])
def post_profile_picture(
    profile_image: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside the Post Profile Picture Router")

    response = user_management_service.post_profile_picture(
        profile_image,
        token,
    )
    logger.debug("Returning from Post Profile Picture Router")
    return response


@router.get("/get-profile-picture")
def get_profile_picture(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside the Get Profile Picture Router")

    response = user_management_service.get_profile_picture(token)
    logger.debug("Returning from Get Profile Picture Router")
    return response


@router.get("/test-firebase-push-notification")
def test_firebase_push_notification(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside the Test Firebase Push Notification Router")

    response = customer_management_service.firebase_endpoint(token)
    logger.debug("Returning from the Test Firebase Push Notification Router")
    return response


@router.put("/update-mobile-number")
def update_mobile_number(
    mobile_number: str,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside the Update Mobile Number Router")

    response = user_management_service.update_mobile_number(mobile_number, token)
    logger.debug("Returning from the Update Mobile Number Router")
    return response

@router.put("/update-email-id")
def update_email_id(
    email_id: EmailStr,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside the Update Email Id Router")

    response = user_management_service.update_email_id(email_id, token)
    logger.debug("Returning from the Update Email Id Router")
    return response

@router.put("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside the Change Password Router")

    response = user_management_service.change_password(old_password, new_password, token)
    logger.debug("Returning from the Change Password Router")
    return response

@router.post("/verify-secure-pin")
def verify_secure_pin(mobile_number: str, code: str):
    logger.debug("Inside Verify Secure Pin Router")
    response = customer_management_service.verify_secure_pin(mobile_number, code)
    logger.debug("Returning from Verify Secure Pin Router")
    return response

@router.put("/reset-password")
def reset_user_password(mobile_number: str, password: str):
    logger.debug("Inside Reset Password Router")
    response = user_management_service.reset_user_password(mobile_number, password)
    logger.debug("Returning from Reset Password Router")
    return response


@router.get("/get-welcome-card-info")
def get_welcome_card_info():
    logger.debug("Inside Get Welcome Card Info Router")
    response = admin_ads_management_service.get_welcome_card_info()
    logger.debug("Returning From the Get Welcome Card Info Router")
    return response


@router.get("/get-notifications")
def get_notifications(
    page_number: int,
    per_page: int,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Get Notifications Router")
    response = customer_management_service.get_notifications(page_number,per_page,token)
    logger.debug("Returning From the Get Notifications Router")
    return response

@router.get("/get-notification-count")
def get_notification_count(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Get Notification Count Router")
    response = customer_management_service.get_notification_count(token)
    logger.debug("Returning From the Get Notification Count Router")
    return response

@router.put("/update-notification-status")
def update_notification_status(
    notification_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Update Notification Status Router")
    response = customer_management_service.update_notification_status(notification_id, token)
    logger.debug("Returning From the Update Notification Status Router")
    return response

@router.post("/add-notification")
def add_notifications(
    source_type: Annotated[str, Query(..., regex="^(buy|sell|deposit|withdrawal|other)$")],
    title: str,
    body: str,
    redirection: str,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Notification Router")
    response = customer_management_service.add_notifications(source_type, title, body, redirection,  token)
    logger.debug("Returning From the Add Notification Router")
    return response