import time
from uuid import uuid4
from common_layer.common_services.utils import token_decoder
from prospect_app.logging_module import logger
from database import db
from common_layer import constants
from common_layer.common_schemas.user_schema import ResponseMessage
from auth_layer.prospect.prospect_schemas.customer_investment_schema import (
    CustomerSharesInDb,
    CustomerTransactionSchemaInDB,
)
from http import HTTPStatus
from bson import ObjectId
from fastapi.encoders import jsonable_encoder


def get_user_wallet(token):
    logger.debug("Inside Get User Wallet Service")
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

        portfolio_details = {}

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


def buy_investment_quanity(token, quantity, property_id):
    logger.debug("Inside Buy Investment Quanity Service")
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
        current_available_shares = 1000
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
        logger.error(f"Error in Buy Investment Quanity Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Buy Investment Quanity Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Buy Investment Quanity Service")
    return response


def sell_investment_quantity(token, quantity, property_id):
    logger.debug("Inside Sell Investment Quantity Service")
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
        logger.error(f"Error in Sell Investment Quantity Service: {e}")
        response = ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Sell Investment Quantity Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )

    logger.debug("Returning From the Sell Investment Quantity Service")
    return response
