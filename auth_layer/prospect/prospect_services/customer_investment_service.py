import time
from uuid import uuid4
from common_layer.common_services.utils import token_decoder
from prospect_app.logging_module import logger
from database import db
from common_layer import constants
from http import HTTPStatus
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from common_layer.common_schemas.user_schema import ResponseMessage
from core_layer.aws_cloudfront.core_cloudfront import cloudfront_sign
from auth_layer.prospect.prospect_schemas.customer_investment_schema import (
    CustomerSharesInDb,
    CustomerTransactionSchemaInDB,
)


def get_user_wallet(token):
    logger.debug("Inside Get User Wallet Service")
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        logger.debug("Getting User Wallet for User: " + str(user_id))
        user_wallet_collection = db[constants.USER_WALLET_SCHEMA]
        user_wallet = user_wallet_collection.find_one({"user_id": user_id})
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        candlestick_data_collection = db[constants.CANDLE_DETAILS_SCHEMA]
        if user_wallet is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "User Wallet Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        portfolio_details = []
        property_ids = []

        for property_id in user_wallet.keys():
            if property_id in ["_id", "user_id", "balance", "updated_at", "created_at"]:
                continue
            property_ids.append(ObjectId(property_id))

        property_details = property_details_collection.find(
            {constants.INDEX_ID: {"$in": property_ids}},
            {"project_title": 1, "address": 1, "price": 1, "project_logo": 1, "_id": 1},
        )
        candlestick_data = candlestick_data_collection.find(
            {
                constants.PROPERTY_ID_FIELD: {
                    "$in": [str(property_id) for property_id in property_ids]
                }
            },
            {"candle_data": 1, "property_id": 1},
        )
        candle_dict = {}
        for candle in candlestick_data:
            candle_dict[str(candle.get(constants.PROPERTY_ID_FIELD))] = candle.get(
                "candle_data"
            )

        for property_detail in property_details:
            wallet_quantity = user_wallet.get(
                str(property_detail.get(constants.INDEX_ID))
            ).get("quantity")
            if wallet_quantity > 0:
                portfolio_details.append(
                    {
                        str(property_detail.get(constants.INDEX_ID)): {
                            "project_title": property_detail.get("project_title"),
                            "address": property_detail.get("address"),
                            "price": property_detail.get("price"),
                            "quantity": user_wallet.get(
                                str(property_detail.get(constants.INDEX_ID))
                            ).get("quantity"),
                            "project_logo": cloudfront_sign(
                                property_detail.get("project_logo")
                            ),
                            "candle_data": candle_dict.get(
                                str(property_detail.get(constants.INDEX_ID))
                            ),
                        }
                    }
                )

        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "portfolio_detail": portfolio_details,
                "balance": user_wallet.get("balance"),
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get User Wallet Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get User Wallet Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get User Wallet Service")
    return response


def add_balance(token, amount):
    logger.debug("Inside Add Balance Service")
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        logger.debug("Getting User Wallet for User: " + str(user_id))
        user_wallet_collection = db[constants.USER_WALLET_SCHEMA]
        user_wallet = user_wallet_collection.find_one({"user_id": user_id})
        if user_wallet is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "User Wallet Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        balance = user_wallet.get("balance")
        balance = balance + amount
        user_wallet_collection.update_one(
            {"user_id": user_id}, {"$set": {"balance": balance}}
        )
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"balance": balance},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Balance Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Balance Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Balance Service")
    return response


def fetch_available_shared(property_details):
    if property_details.get(constants.CATEGORY_FIELD) == "residential":
        residentail_category_collection = db[
            constants.RESIDENTIAL_PROPERTY_DETAILS_SCHEMA
        ]
        residential_category = residentail_category_collection.find_one(
            {
                constants.INDEX_ID: ObjectId(
                    property_details.get(constants.PROPERTY_DETAILS_ID_FIELD)
                )
            }
        )
        if residential_category is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Residential Category Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        current_available_shares = residential_category.get("carpet_area")
    elif property_details.get(constants.CATEGORY_FIELD) == "commercial":
        commercial_category_collection = db[
            constants.COMMERCIAL_PROPERTY_DETAILS_SCHEMA
        ]
        commercial_category = commercial_category_collection.find_one(
            {
                constants.INDEX_ID: ObjectId(
                    property_details.get(constants.PROPERTY_DETAILS_ID_FIELD)
                )
            }
        )
        if commercial_category is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Commercial Category Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        current_available_shares = commercial_category.get("carpet_area")

    elif property_details.get(constants.CATEGORY_FIELD) == "farm":
        farm_category_collection = db[constants.FARM_PROPERTY_DETAILS_SCHEMA]
        farm_category = farm_category_collection.find_one(
            {
                constants.INDEX_ID: ObjectId(
                    property_details.get(constants.PROPERTY_DETAILS_ID_FIELD)
                )
            }
        )
        if farm_category is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Farm Category Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        current_available_shares = farm_category.get("plot_area")
    else:
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: "Invalid Category"},
            status_code=HTTPStatus.NOT_FOUND,
        )
        return response
    response = ResponseMessage(
        type=constants.HTTP_RESPONSE_SUCCESS,
        data={"available_shares": current_available_shares},
        status_code=HTTPStatus.OK,
    )
    return response


def buy_investment_share(token, quantity, property_id):
    logger.debug("Inside Buy Investment Share Service")
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        logger.debug("Getting User Wallet for User: " + str(user_id))
        user_wallet_collection = db[constants.USER_WALLET_SCHEMA]
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        customer_transaction_details_collection = db[
            constants.CUSTOMER_TRANSACTION_SCHEMA
        ]
        user_wallet = user_wallet_collection.find_one({"user_id": user_id})
        if user_wallet is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "User Wallet Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )

        if property_details is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Property Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response
        if property_details.get("available_shares") is None:
            fetch_available_shared_response = jsonable_encoder(
                fetch_available_shared(property_details)
            )
            if (
                fetch_available_shared_response.get("type")
                == constants.HTTP_RESPONSE_FAILURE
            ):
                return fetch_available_shared_response
            current_available_shares = fetch_available_shared_response.get("data").get(
                "available_shares"
            )
        else:
            current_available_shares = property_details.get("available_shares")

        current_price = property_details.get("price")
        if current_available_shares < quantity:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: "Insufficient Shares, Please enter less quantity"
                },
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        if quantity * current_price > user_wallet.get("balance"):
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: "Insufficient Balance, You need at least "
                    + str(quantity * current_price)
                    + " to buy "
                    + str(quantity)
                    + " shares"
                },
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        if user_wallet.get(property_id) is None:
            logger.debug("Property Not Exists in User Wallet")
            user_wallet[property_id] = jsonable_encoder(
                CustomerSharesInDb(quantity=quantity, avg_price=current_price)
            )
        else:
            logger.debug("Property Already Exists in User Wallet")
            user_wallet[property_id]["quantity"] = (
                user_wallet[property_id]["quantity"] + quantity
            )
            user_wallet[property_id]["avg_price"] = (
                user_wallet[property_id]["avg_price"] + current_price
            ) / 2
            user_wallet[property_id]["updated_at"] = time.time()
        user_wallet["balance"] = user_wallet.get("balance") - (quantity * current_price)

        user_wallet_collection.update_one({"user_id": user_id}, {"$set": user_wallet})

        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {"$set": {"available_shares": current_available_shares - quantity}},
        )

        customer_transaction_index = CustomerTransactionSchemaInDB(
            user_id=user_id,
            property_id=property_id,
            transaction_type="BUY",
            transaction_amount=quantity * current_price,
            transaction_id=str(uuid4()),
            transaction_status="SUCCESS",
        )

        transaction_index = customer_transaction_details_collection.insert_one(
            jsonable_encoder(customer_transaction_index)
        )

        del user_wallet["_id"]
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "user_wallet": user_wallet,
                "transaction_id": str(transaction_index.inserted_id),
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Buy Investment Share Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Buy Investment Share Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Buy Investment Share Service")
    return response


def sell_investment_share(token, quantity, property_id):
    logger.debug("Inside Sell Investment Share Service")
    try:
        logger.debug("Decoding Token")
        decoded_token = token_decoder(token)
        user_id = decoded_token.get(constants.ID)
        logger.debug("Getting User Wallet for User: " + str(user_id))
        user_wallet_collection = db[constants.USER_WALLET_SCHEMA]
        property_details_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        user_wallet = user_wallet_collection.find_one({"user_id": user_id})
        customer_transaction_details_collection = db[
            constants.CUSTOMER_TRANSACTION_SCHEMA
        ]
        if user_wallet is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "User Wallet Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        property_details = property_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )

        if property_details is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "Property Not Found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        if user_wallet.get(property_id) is None:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "You do not have any shares of this property"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        if user_wallet.get(property_id).get("quantity") < quantity:
            response = ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: "You do not have enough shares to sell"},
                status_code=HTTPStatus.NOT_FOUND,
            )
            return response

        current_available_shares = property_details.get("available_shares")

        current_price = property_details.get("price")

        user_wallet[property_id]["quantity"] = (
            user_wallet[property_id]["quantity"] - quantity
        )
        user_wallet[property_id]["updated_at"] = time.time()

        user_wallet["balance"] = user_wallet.get("balance") + (quantity * current_price)

        user_wallet_collection.update_one({"user_id": user_id}, {"$set": user_wallet})

        property_details_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {"$set": {"available_shares": current_available_shares + quantity}},
        )

        transaction_index = CustomerTransactionSchemaInDB(
            user_id=user_id,
            property_id=property_id,
            transaction_type="SELL",
            transaction_amount=quantity * current_price,
            transaction_id=str(uuid4()),
            transaction_status="SUCCESS",
        )

        customer_transaction_index = customer_transaction_details_collection.insert_one(
            jsonable_encoder(transaction_index)
        )

        del user_wallet["_id"]
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "user_wallet": user_wallet,
                "transaction_id": str(customer_transaction_index.inserted_id),
            },
            status_code=HTTPStatus.OK,
        )

    except Exception as e:
        logger.error(f"Error in Sell Investment Share Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Sell Investment Share Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )

    logger.debug("Returning From the Sell Investment Share Service")
    return response
