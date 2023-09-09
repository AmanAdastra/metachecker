import time
import io
from typing import Annotated
from fastapi import Depends, HTTPException
from database import db
from bson import ObjectId
from common_layer import constants
from http import HTTPStatus
from admin_app.logging_module import logger
from fastapi.encoders import jsonable_encoder
from common_layer.common_services.utils import token_decoder
from common_layer.common_services.oauth_handler import oauth2_scheme
from core_layer.aws_s3 import s3
from core_layer.aws_cloudfront import core_cloudfront
from auth_layer.prospect.prospect_schemas.customer_leads_management_schema import (
    ResponseMessage,
    CustomerLeadsInDB,
    LeadStatus,
)


def get_investors_projects(page_number: int, per_page: int, token: str):
    logger.debug("Inside Get Investors Projects Service")
    try:
        decoded_token = token_decoder(token)
        logger.debug("Decoded Token : " + str(decoded_token))
        user_id = decoded_token.get(constants.ID)
        logger.debug("User Id : " + str(user_id))

        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        candle_details_collection = db[constants.CANDLE_DETAILS_SCHEMA]
        """
            Title, address, logo, candle, change, change_percent
        """

        property_details = (
            property_details_collection.find(
                {constants.LISTED_BY_USER_ID_FIELD: (user_id)},
                {
                    constants.INDEX_ID: 1,
                    constants.PROJECT_TITLE_FIELD: 1,
                    constants.PROJECT_LOGO_FIELD: 1,
                    constants.ADDRESS_FIELD: 1,
                    constants.PRICE_FIELD: 1,
                },
            )
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )

        response_list = []
        for property_detail in property_details:
            candle_data = candle_details_collection.find_one(
                {constants.PROPERTY_ID_FIELD: str(property_detail[constants.INDEX_ID])},
                {constants.INDEX_ID: 0, "candle_data": 1},
            )
            property_detail[constants.ID] = str(property_detail[constants.INDEX_ID])
            property_detail[
                constants.PROJECT_LOGO_FIELD
            ] = core_cloudfront.cloudfront_sign(
                property_detail[constants.PROJECT_LOGO_FIELD]
            )
            property_detail["candle_data"] = candle_data["candle_data"]
            property_detail["change"] = (
                candle_data[-1].get("price") - candle_data[0].get("price")
                if len(candle_data) > 1
                else 0
            )
            property_detail["change_percent"] = (
                (property_detail["change"] / candle_data[0].get("price")) * 100
                if len(candle_data) > 1
                else 0
            )
            del property_detail[constants.INDEX_ID]
            response_list.append(property_detail)
        document_count = property_details_collection.count_documents(
            {constants.LISTED_BY_USER_ID_FIELD: (user_id)}
        )
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"projects": response_list, "total_count": document_count},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Regions Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Investors Projects Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Investors Projects Service")
    return response


def generate_lead_for_property(property_id: str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Generate Lead For Property Service")
    try:
        decoded_token = token_decoder(token)
        logger.debug("Decoded Token : " + str(decoded_token))
        user_id = decoded_token.get(constants.ID)
        logger.debug("User Id : " + str(user_id))

        project_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        customer_leads_collection = db[constants.CUSTOMER_LEADS_SCHEMA]

        project_details = project_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {constants.INDEX_ID: 0, constants.LISTED_BY_USER_ID_FIELD: 1},
        )

        if not project_details:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={"message": "Project Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        leads_index = jsonable_encoder(
            CustomerLeadsInDB(
                listed_by_user_id=project_details[constants.LISTED_BY_USER_ID_FIELD],
                user_id=user_id,
                property_id=property_id,
                status="active",
            )
        )

        inserted_index = customer_leads_collection.insert_one(leads_index)

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "message": "Lead Generated Successfully",
                "lead_id": str(inserted_index.inserted_id),
            },
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Generate Lead For Property Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Generate Lead For Property Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Generate Lead For Property Service")
    return response


def check_already_lead_exist(property_id: str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Check Already Lead Exist Service")
    try:
        decoded_token = token_decoder(token)
        logger.debug("Decoded Token : " + str(decoded_token))
        user_id = decoded_token.get(constants.ID)
        logger.debug("User Id : " + str(user_id))

        customer_leads_collection = db[constants.CUSTOMER_LEADS_SCHEMA]

        if customer_leads_collection.find_one(
            {
                constants.PROPERTY_ID_FIELD: property_id,
                constants.USER_ID_FIELD: user_id,
                "status": "active",
            }
        ):
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={"message": "Lead Already Exist"},
                status_code=HTTPStatus.OK,
            )
            return response
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"message": "Lead Not Exist"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Check Already Lead Exist Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Check Already Lead Exist Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Check Already Lead Exist Service")
    return response


def get_candle_of_property(property_id: str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Candle Of Property Service")
    try:
        decoded_token = token_decoder(token)
        logger.debug("Decoded Token : " + str(decoded_token))
        user_id = decoded_token.get(constants.ID)
        logger.debug("User Id : " + str(user_id))

        candle_details_collection = db[constants.CANDLE_DETAILS_SCHEMA]

        candle_data = candle_details_collection.find_one(
            {constants.PROPERTY_ID_FIELD: property_id},
        )

        if not candle_data:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={"message": "Candle Data Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        candle_data[constants.ID] = str(candle_data[constants.INDEX_ID])
        del candle_data[constants.INDEX_ID]

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"candle_data": candle_data},
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Get Candle Of Property Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Candle Of Property Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Candle Of Property Service")
    return response


def get_investors_leads(page_number: int, per_page: int, token: str):
    logger.debug("Inside Get Investors Leads Service")
    try:
        decoded_token = token_decoder(token)
        logger.debug("Decoded Token : " + str(decoded_token))
        user_id = decoded_token.get(constants.ID)
        logger.debug("User Id : " + str(user_id))

        customer_leads_collection = db[constants.CUSTOMER_LEADS_SCHEMA]
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        """
            Name, email, phone, property name, property address, property logo, property candle, property change, property change percent
        """
        customer_leads = (
            customer_leads_collection.find(
                {constants.LISTED_BY_USER_ID_FIELD: (user_id)},
                {
                    constants.INDEX_ID: 1,
                    constants.USER_ID_FIELD: 1,
                    constants.PROPERTY_ID_FIELD: 1,
                    "status": 1,
                },
            )
            .skip((page_number - 1) * per_page)
            .limit(per_page)
        )
        response_list = []
        for customer_lead in customer_leads:
            property_details = property_details_collection.find_one(
                {
                    constants.INDEX_ID: ObjectId(
                        customer_lead[constants.PROPERTY_ID_FIELD]
                    )
                },
                {
                    constants.INDEX_ID: 1,
                    constants.PROJECT_TITLE_FIELD: 1,
                    constants.PROJECT_LOGO_FIELD: 1,
                    constants.ADDRESS_FIELD: 1,
                },
            )
            property_details[constants.ID] = str(property_details[constants.INDEX_ID])
            property_details[
                constants.PROJECT_LOGO_FIELD
            ] = core_cloudfront.cloudfront_sign(
                property_details[constants.PROJECT_LOGO_FIELD]
            )
            del property_details[constants.INDEX_ID]
            customer_lead[constants.ID] = str(customer_lead[constants.INDEX_ID])
            del customer_lead[constants.INDEX_ID]
            customer_lead["property_details"] = property_details
            response_list.append(customer_lead)
        document_count = customer_leads_collection.count_documents(
            {constants.LISTED_BY_USER_ID_FIELD: (user_id)}
        )
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "leads": response_list,
                "total_count": document_count,
                "page_number": page_number,
                "per_page": per_page,
            },
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Get Investors Leads Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Investors Leads Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Investors Leads Service")
    return response


def get_investors_leads_details(lead_id: str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Investors Leads Details Service")
    try:
        decoded_token = token_decoder(token)
        logger.debug("Decoded Token : " + str(decoded_token))
        user_id = decoded_token.get(constants.ID)
        logger.debug("User Id : " + str(user_id))

        customer_leads_collection = db[constants.CUSTOMER_LEADS_SCHEMA]

        customer_lead = customer_leads_collection.find_one(
            {constants.INDEX_ID: ObjectId(lead_id)},
            {
                constants.INDEX_ID: 1,
                constants.USER_ID_FIELD: 1,
                constants.PROPERTY_ID_FIELD: 1,
                "status": 1,
            },
        )

        if not customer_lead:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={"message": "Lead Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        customer_lead[constants.ID] = str(customer_lead[constants.INDEX_ID])
        del customer_lead[constants.INDEX_ID]

        user_details_collection = db[constants.USER_DETAILS_SCHEMA]

        user_details = user_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(customer_lead[constants.USER_ID_FIELD])},
            {
                constants.INDEX_ID: 0,
                "legal_name": 1,
                "email_id": 1,
                "mobile_number": 1,
                "profile_picture_url_key": 1,
                "profile_picture_uploaded": 1,
            },
        )
        if user_details.get("profile_picture_uploaded"):
            user_details["profile_picture_url_key"] = core_cloudfront.cloudfront_sign(
                user_details["profile_picture_url_key"]
            )
        else:
            user_details["profile_picture_url_key"] = ""
        customer_lead["user_details"] = user_details

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"lead_details": customer_lead},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Investors Leads Details Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Get Investors Leads Details Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Investors Leads Details Service")
    return response


def get_dashboard_details(token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Dashboard Details Service")
    try:
        decoded_token = token_decoder(token)
        logger.debug("Decoded Token : " + str(decoded_token))
        user_id = decoded_token.get(constants.ID)
        logger.debug("User Id : " + str(user_id))

        customer_leads_collection = db[constants.CUSTOMER_LEADS_SCHEMA]
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        no_of_views = property_details_collection.aggregate(
            [
                {"$match": {constants.LISTED_BY_USER_ID_FIELD: (user_id)}},
                {"$group": {"_id": None, "view_count": {"$sum": "$view_count"}}},
            ]
        )
        no_of_views_list = (list(no_of_views))
        no_of_views = no_of_views_list[0]["view_count"] if no_of_views_list else 0

        engagement = property_details_collection.count_documents(
            {constants.LISTED_BY_USER_ID_FIELD: (user_id), "status": "sold"}
        )
        engagement_rate = (engagement / no_of_views if no_of_views > 0 else 0) * 100

        total_leads = customer_leads_collection.count_documents(
            {constants.LISTED_BY_USER_ID_FIELD: (user_id)}
        )

        leads_completed = customer_leads_collection.count_documents(
            {constants.LISTED_BY_USER_ID_FIELD: (user_id), "status": LeadStatus.MEETING_COMPLETED.value}
        )

        leads_reamining = total_leads - leads_completed

        meeting_scheduled = customer_leads_collection.count_documents(
            {
                constants.LISTED_BY_USER_ID_FIELD: (user_id),
                "status": LeadStatus.MEETING_SCHEDULED.value,
            }
        )

        meeting_completed = customer_leads_collection.count_documents(
            {
                constants.LISTED_BY_USER_ID_FIELD: (user_id),
                "status": LeadStatus.MEETING_COMPLETED.value,
            }
        )

        # Count of total property
        total_property = property_details_collection.count_documents(
            {constants.LISTED_BY_USER_ID_FIELD: (user_id)}
        )

        # Count of total property sold
        total_property_sold = property_details_collection.count_documents(
            {constants.LISTED_BY_USER_ID_FIELD: (user_id), "status": "sold"}
        )

        progress = (total_property_sold / total_property) * 100 if total_property > 0 else 0

        total_meetings = meeting_scheduled + meeting_completed

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "no_of_views": no_of_views,
                "engagement_rate": engagement_rate,
                "total_leads": total_leads,
                "leads_completed": leads_completed,
                "leads_reamining": leads_reamining,
                "meeting_scheduled": meeting_scheduled,
                "meeting_completed": meeting_completed,
                "total_meetings": total_meetings,
                "progress": progress,
            },
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Get Dashboard Details Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Dashboard Details Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )

    logger.debug("Returning From the Get Dashboard Details Service")
    return response


def change_lead_status(lead_id: str, status: str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Change Lead Status Service")
    try:
        decoded_token = token_decoder(token)
        logger.debug("Decoded Token : " + str(decoded_token))
        user_id = decoded_token.get(constants.ID)
        logger.debug("User Id : " + str(user_id))

        if status not in [status.value for status in LeadStatus]:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    "message": "Invalid Status Please enter valid status : "
                    + str([status.value for status in LeadStatus])
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        customer_leads_collection = db[constants.CUSTOMER_LEADS_SCHEMA]

        customer_lead = customer_leads_collection.find_one(
            {constants.INDEX_ID: ObjectId(lead_id)},
            {
                constants.INDEX_ID: 1,
                constants.USER_ID_FIELD: 1,
                constants.PROPERTY_ID_FIELD: 1,
                "status": 1,
            },
        )

        if not customer_lead:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={"message": "Lead Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        customer_leads_collection.update_one(
            {constants.INDEX_ID: ObjectId(lead_id)}, {"$set": {"status": status}}
        )

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"message": "Lead Status Updated Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Change Lead Status Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Change Lead Status Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Change Lead Status Service")
    return response
