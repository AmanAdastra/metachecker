import os
import sys
import json
import random

sys.path.append(os.path.realpath(".."))
from datetime import timedelta
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware import Middleware
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from logging_module import logger
from fastapi.staticfiles import StaticFiles
from routers import (
    customer_router,
    customer_property_router,
    customer_investment_router,
    customer_leads_management_router,
    customer_conversation_router
)
from auth_layer.prospect.prospect_services import customer_property_service
from pymongo import GEOSPHERE
from database import db
from common_layer import constants
from common_layer.common_services import user_management_service, oauth_handler
from common_layer.common_schemas.user_schema import UserTypes, RegisterRequest
from common_layer.common_schemas.property_schema import (
    ResidentialPropertyRequestSchema,
    CommercialPropertyRequestSchema,
    FarmPropertyRequestSchema,
    ResidentialType,
    CommercialType,
    FarmType,
)


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


@app.on_event("startup")
def seed_data():
    logger.debug("Inserting seed data")
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
        logger.debug("Inserting the property seed data")

        user_details = db[constants.USER_DETAILS_SCHEMA].find_one(
            {"user_type": UserTypes.PARTNER.value}
        )
        if not user_details:
            logger.debug("No partner user found")
            return

        subject = {
        constants.EMAIL_ID_FIELD: user_details[constants.EMAIL_ID_FIELD],
        constants.ID: str(user_details[constants.INDEX_ID]),
        constants.USER_TYPE_FIELD: user_details[constants.USER_TYPE_FIELD],
        }
        access_token = oauth_handler.create_access_token(
            data=subject,
            expires_delta=timedelta(seconds=constants.ACCESS_TOKEN_EXPIRY_TIME),
        )

        with open("./seed_data/map.json") as f:
            data = json.load(f)
            for location in data[:5]:
                request = ResidentialPropertyRequestSchema(
                    is_investment_property=random.choice([True, False]),
                    listing_type=random.choice(["sell", "rent", "lease"]),
                    listed_by=random.choice(["owner", "broker"]),
                    property_type=random.choice(
                        ["apartment", "flat", "farm_house", "houses_and_villa"]
                    ),
                    bedrooms=random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
                    bathrooms=random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
                    furnishing=random.choice(
                        ["furnished", "semi_furnished", "unfurnished"]
                    ),
                    built_up_area=random.choice(
                        [1000, 2000, 3000, 4000, 5000, 6000, 7000]
                    ),
                    carpet_area=random.choice(
                        [1000, 2000, 3000, 4000, 5000, 6000, 7000]
                    ),
                    maintenance=random.choice(
                        [1000, 2000, 3000, 4000, 5000, 6000, 7000]
                    ),
                    floor_no=random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
                    car_parking=random.choice([True, False]),
                    facing=random.choice(["north", "south", "east", "west"]),
                    balcony=random.choice([True, False]),
                    possession_type=random.choice(
                        ["ready_to_move", "under_construction", "new_launch"]
                    ),
                    description="This is a beautiful property",
                    project_title=random.choice(
                        [
                            "Beautiful property",
                            "Amazing property",
                            "Awesome property",
                            "Great property",
                        ]
                    ),
                    price=random.choice([100, 200, 300, 400, 500, 600, 700]),
                    video_url="https://www.youtube.com/watch?v=6n3pFFPSlW4",
                    images=[],
                    address=location["address"],
                    location={
                        "latitude": location["latitude"],
                        "longitude": location["longitude"],
                    },
                    region_id="put_region_id_here",
                    roi_percentage=random.choice([4, 5, 6, 7, 8, 9, 10]),
                )

                response = customer_property_service.add_residential_property(request, access_token)
                logger.debug("Seed data inserted: " + str(response))

            for location in data[5:10]:
                request = CommercialPropertyRequestSchema(
                    is_investment_property=random.choice([True, False]),
                    listing_type=random.choice(["sell", "rent", "lease"]),
                    listed_by=random.choice(["owner", "broker"]),
                    property_type=random.choice(
                        [ x.value for x in CommercialType]
                    ),
                    furnishing=random.choice(
                        ["furnished", "semi_furnished", "unfurnished"]
                    ),
                    built_up_area=random.choice(
                        [1000, 2000, 3000, 4000, 5000, 6000, 7000]
                    ),
                    carpet_area=random.choice(
                        [1000, 2000, 3000, 4000, 5000, 6000, 7000]
                    ),
                    maintenance=random.choice(
                        [1000, 2000, 3000, 4000, 5000, 6000, 7000]
                    ),
                    car_parking=random.choice([True, False]),
                    facing=random.choice(["north", "south", "east", "west"]),
                    balcony=random.choice([True, False]),
                    bathrooms=random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
                    possession_type=random.choice(
                        ["ready_to_move", "under_construction", "new_launch"]
                    ),
                    description="This is a beautiful property",
                    project_title=random.choice(
                        [
                            "Beautiful property",
                            "Amazing property",
                            "Awesome property",
                            "Great property",
                        ]
                    ),
                    price=random.choice([100, 200, 300, 400, 500, 600, 700]),
                    video_url="https://www.youtube.com/watch?v=6n3pFFPSlW4",
                    images=[],
                    address=location["address"],
                    location={
                        "latitude": location["latitude"],
                        "longitude": location["longitude"],
                    },
                    region_id="put_region_id_here",
                    roi_percentage=random.choice([4, 5, 6, 7, 8, 9, 10]),
                )

                response = customer_property_service.add_commercial_property(request, access_token)
                logger.debug("Seed data inserted: " + str(response))

            for location in data[10:]:
                request = FarmPropertyRequestSchema(
                    is_investment_property=random.choice([True, False]),
                    listing_type=random.choice(["sell", "rent", "lease"]),
                    listed_by=random.choice(["owner", "broker"]),
                    property_type=random.choice(
                        [ x.value for x in FarmType]
                    ),
                    length=random.choice([1000, 2000, 3000, 4000, 5000, 6000, 7000]),
                    breadth=random.choice(
                        [1000, 2000, 3000, 4000, 5000, 6000, 7000]
                    ),
                    plot_area=random.choice(
                        [1000, 2000, 3000, 4000, 5000, 6000, 7000]
                    ),
                    facing=random.choice(["north", "south", "east", "west"]),
                    possession_type=random.choice(
                        ["ready_to_move", "under_construction", "new_launch"]
                    ),
                    description="This is a beautiful property",
                    project_title=random.choice(
                        [
                            "Beautiful property",
                            "Amazing property",
                            "Awesome property",
                            "Great property",
                        ]
                    ),
                    price=random.choice([100, 200, 300, 400, 500, 600, 700]),
                    video_url="https://www.youtube.com/watch?v=6n3pFFPSlW4",
                    images=[],
                    address=location["address"],
                    location={
                        "latitude": location["latitude"],
                        "longitude": location["longitude"],
                    },
                    region_id="put_region_id_here",
                    roi_percentage=random.choice([4, 5, 6, 7, 8, 9, 10]),
                )

                response = customer_property_service.add_farm_property(request, access_token)
                logger.debug("Seed data inserted: " + str(response))