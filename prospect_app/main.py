import os
import sys
import json
import random

sys.path.append(os.path.realpath(".."))
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
)
from auth_layer.prospect.prospect_services import customer_property_service
from pymongo import GEOSPHERE
from database import db
from common_layer import constants
from common_layer.common_services import user_management_service
from common_layer.common_schemas.user_schema import UserTypes
from common_layer.common_schemas.property_schema import ResidentialPropertyRequestSchema

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
        with open("./seed_data/map.json") as f:
            data = json.load(f)
            for location in data:
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

                response = customer_property_service.add_seed_property(request)
                logger.debug("Seed data inserted: " + str(response))
