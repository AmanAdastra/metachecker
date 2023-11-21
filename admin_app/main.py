import os
import sys

sys.path.append(os.path.realpath(".."))
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware import Middleware
from logging_module import logger
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from admin_app.routers import admin_property_management_router, admin_user_management_router, admin_ads_management_router
from auth_layer.admin.admin_services import admin_user_management_service

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(middleware=middleware, title="Square Admin", description="Trading Platform", version="0.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_user_management_router.router)
app.include_router(admin_property_management_router.router)
app.include_router(admin_ads_management_router.router)


@app.get("/privacy-policy", response_class=HTMLResponse)
def get_privacy_policy(request: Request):
    response = admin_user_management_service.terms_and_policy_render(request, "policy")
    return response

@app.get("/terms-and-conditions", response_class=HTMLResponse)
def get_terms_and_conditions(request: Request):
    response = admin_user_management_service.terms_and_policy_render(request, "terms")
    return response



@app.on_event("startup")
async def startup_event():
    logger.debug("App startup: " + str(datetime.now()))
