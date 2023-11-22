import os
import sys
import schedule
sys.path.append(os.path.realpath(".."))
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware import Middleware
from fastapi_utils.tasks import repeat_every
from datetime import datetime
from logging_module import logger
from fastapi.staticfiles import StaticFiles
from routers import (
    customer_router,
    customer_property_router,
    customer_investment_router,
    customer_leads_management_router,
    customer_conversation_router,
    customer_kyc_router
)
from auth_layer.prospect.prospect_services import customer_property_service, customer_investment_service
from auth_layer.admin.admin_services import admin_user_management_service
from database import db
from common_layer import constants
from common_layer.common_services import user_management_service
from common_layer.common_schemas.user_schema import UserTypes, RegisterRequest
from pymongo import GEOSPHERE


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]


app = FastAPI(
    middleware=middleware,
    title="Square Mobile",
    description="Trading Platform",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(customer_router.router)
app.include_router(customer_property_router.router)
app.include_router(customer_investment_router.router)
app.include_router(customer_leads_management_router.router)
app.include_router(customer_conversation_router.router)
app.include_router(customer_kyc_router.router)


schedule.every().day.at("00:05").do(customer_property_service.add_todays_property_count)

@app.on_event("startup")
@repeat_every(seconds=60)
async def auto_update_property_count()->None:
        schedule.run_pending()

@app.on_event("startup")
def add_seed_users():
    logger.debug("Adding admin user")
    if (
        db[constants.USER_DETAILS_SCHEMA].count_documents(
            {"user_type": UserTypes.SUPER_ADMIN.value}
        )
        == 0
    ):
        admin_user = RegisterRequest(
            legal_name="Admin",
            mobile_number="919999999991",
            email_id="admin@mailinator.com",
            password="Test@123",
            password_confirmed="Test@123",
            user_type=UserTypes.SUPER_ADMIN.value,
        )
        response = user_management_service.register_user(admin_user)
        logger.debug("Admin user added")
    if (
        db[constants.USER_DETAILS_SCHEMA].count_documents(
            {"user_type": UserTypes.PARTNER.value}
        )
        == 0
    ):
        partner_user = RegisterRequest(
            legal_name="Partner",
            mobile_number="919999999992",
            email_id="partner@mailinator.com",
            password="Test@123",
            password_confirmed="Test@123",
            user_type=UserTypes.PARTNER.value,
        )
        response = user_management_service.register_user(partner_user)
        logger.debug("Partner user added" )

    if (
        db[constants.USER_DETAILS_SCHEMA].count_documents(
            {"user_type": UserTypes.CUSTOMER.value}
        )
        == 0
    ):
        customer_user = RegisterRequest(
            legal_name="John Doe",
            mobile_number="919999999999",
            email_id="johndoe@mailinator.com",
            password="Test@123",
            password_confirmed="Test@123",
            user_type=UserTypes.CUSTOMER.value,
        )
        response = user_management_service.register_user(customer_user)
        logger.debug("Customer user added ")
    if db[constants.PROPERTY_DETAILS_SCHEMA].count_documents({}) == 0:
        response = db[constants.PROPERTY_DETAILS_SCHEMA].create_index(
            [("location", GEOSPHERE)]
        )
        logger.debug("Index created: " + str(response))
        response2 = db[constants.REGION_DETAILS_SCHEMA].create_index(
            [("location", GEOSPHERE)]
        )
        logger.debug("Index created: " + str(response2))
        logger.debug("App startup: " + str(datetime.now()))




schedule.every().day.at("23:50").do(customer_investment_service.user_wallet_snapshot_handler)
@app.on_event("startup")
@repeat_every(seconds=60)
async def user_wallet_snapshot_cron()->None:
        schedule.run_pending()


@app.get("/privacy-policy", response_class=HTMLResponse)
def get_privacy_policy(request: Request):
    response = admin_user_management_service.terms_and_policy_render(request, "policy")
    return response

@app.get("/terms-and-conditions", response_class=HTMLResponse)
def get_terms_and_conditions(request: Request):
    response = admin_user_management_service.terms_and_policy_render(request, "terms")
    return response