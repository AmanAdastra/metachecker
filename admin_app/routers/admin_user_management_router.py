from fastapi import APIRouter, Depends, File, Form, UploadFile, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from common_layer.common_services.oauth_handler import oauth2_scheme
from logging_module import logger
from pydantic import EmailStr
from typing import Annotated
from common_layer.common_services import user_management_service, utils
from common_layer.common_schemas import user_schema
from common_layer import constants
from auth_layer.admin.admin_services import admin_user_management_service
from fastapi.responses import HTMLResponse


router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
    tags=["User Management"],
)


@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    logger.debug("Inside Login For Access Token Router")
    response = user_management_service.login_for_access_token(
        form_data.username, form_data.password, constants.ADMIN_SOURCE
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
):
    logger.debug("Inside the Register User Router")
    response = user_management_service.register_user(user_request)
    logger.debug("Returning from the Register User Router")
    return response


@router.post("/login")
def login_user(
    user_request: user_schema.AdminUserLogin,
):
    logger.debug("Inside the Login User Router")
    response = admin_user_management_service.login_user(user_request)
    logger.debug("Returning from the Login User Router")
    return response


@router.get("/get-user-details")
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside Get User Details Router")
    response = user_management_service.get_user_details(token)
    logger.debug("Returning From the Get User Details Router")
    return response

@router.get("/get-user-details-by-id")
def get_user_details_by_id(user_id: str, token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside Get User Details By Id Router")
    response = user_management_service.get_user_details_by_id(user_id, token)
    logger.debug("Returning From the Get User Details By Id Router")
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


@router.post(
    "/post-profile-picture", dependencies=[Depends(utils.valid_content_length)]
)
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
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside the Get Profile Picture Router")

    response = user_management_service.get_profile_picture(token)
    logger.debug("Returning from Get Profile Picture Router")
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

    response = user_management_service.change_password(
        old_password, new_password, token
    )
    logger.debug("Returning from the Change Password Router")
    return response


@router.put("/convert-investor-to-customer")
def convert_investor_to_customer(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside the Convert Investor To Customer Router")

    response = user_management_service.convert_investor_to_customer(token)
    logger.debug("Returning from the Convert Investor To Customer Router")
    return response


@router.get("/get-users-list")
def get_users_list(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside the Get Users List Router")

    response = admin_user_management_service.get_users_list()
    logger.debug("Returning from the Get Users List Router")
    return response


@router.put("/reset-password")
def reset_password(
    email_id: EmailStr,
    password: str,
):
    logger.debug("Inside the Reset Password Router")

    response = user_management_service.reset_admin_password(email_id, password)
    logger.debug("Returning from the Reset Password Router")
    return response

@router.post("/upload-terms-or-policy-txt-file")
def upload_terms_or_policy_txt_file(
    source_type: Annotated[str, Query(..., regex="^(terms|policy)$")],
    html_text: str = Form(...),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside the Upload Terms Or Policy Txt File Router")

    response = admin_user_management_service.upload_terms_or_policy_txt_file(
        source_type, html_text, token
    )
    logger.debug("Returning from the Upload Terms Or Policy Txt File Router")
    return response

@router.get("/get-terms-or-policy-html-text")
def get_terms_or_policy_html_text(
    source_type: Annotated[str, Query(..., regex="^(terms|policy)$")],
):
    logger.debug("Inside the Get Terms Or Policy Html Text Router")

    response = admin_user_management_service.get_terms_or_policy_html_text(source_type)
    logger.debug("Returning from the Get Terms Or Policy Html Text Router")
    return response