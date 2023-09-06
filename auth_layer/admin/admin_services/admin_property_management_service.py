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
from auth_layer.admin.admin_schemas import admin_property_management_schemas
from common_layer.common_schemas.property_schema import UpdateCandleDataSchema
from common_layer.common_services.oauth_handler import oauth2_scheme
from core_layer.aws_s3 import s3
from core_layer.aws_cloudfront import core_cloudfront


def get_regions(token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside Get Regions Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Regions fetched by User Id: {user_id}")
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        regions = list(region_collection.find({}).sort(constants.CREATED_AT_FIELD, -1))
        response_regions = []
        for region in regions:
            region[constants.ID] = str(region[constants.INDEX_ID])
            region["region_icon_image"] = core_cloudfront.cloudfront_sign(
                region[constants.ICON_IMAGE_FIELD]
            )
            del region[constants.INDEX_ID]
            response_regions.append(region)
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"regions": response_regions},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Regions Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Regions Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Regions Service")
    return response


def add_region(
    request: admin_property_management_schemas.AddRegionSchemaRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Region Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Region added by User Id: {user_id}")
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        request.title = request.title.title()
        if region_collection.find_one({constants.TITLE_FIELD: request.title}):
            logger.error(f"Region with Title: {request.title} already exists")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Region with Title: {request.title} already exists"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        icon_image_key = (
            f"{constants.REGION_ICON_BASE}/{request.title}.{constants.IMAGE_TYPE}"
        )
        validated_index = jsonable_encoder(
            admin_property_management_schemas.AddRegionsInDBSchema(
                title=request.title,
                description=request.description,
                icon_image_key=icon_image_key,
                location={
                    "type": "Point",
                    "coordinates": [request.longitude, request.latitude],
                },
            )
        )
        inserted_index = region_collection.insert_one(validated_index)
        logger.debug(f"Region Added Successfully with Id: {inserted_index.inserted_id}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "region_id": str(inserted_index.inserted_id),
                "region_icon_image": icon_image_key,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Region Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Region Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Region Service")
    return response


def get_region_by_id(region_id: str, token: Annotated[str, Depends(oauth2_scheme)]):
    logger.debug("Inside Get Region By Id Service")
    try:
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS, data={}, status_code=HTTPStatus.OK
        )
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Region fetched by User Id: {user_id}")
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        region = region_collection.find_one({constants.INDEX_ID: ObjectId(region_id)})
        if not region:
            logger.error(f"Region with Id: {region_id} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region with Id: {region_id} does not exist"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        region[constants.ID] = str(region[constants.INDEX_ID])
        region["region_icon_image"] = core_cloudfront.cloudfront_sign(
            region[constants.ICON_IMAGE_FIELD]
        )
        del region[constants.INDEX_ID]
        response.data = {"region": region}

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"region": region},
            status_code=HTTPStatus.OK,
        )


    except Exception as e:
        logger.error(f"Error in Get Region By Id Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Region By Id Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Region By Id Service")
    return response


def upload_region_icon(
    region_id,
    region_icon_image,
    token,
):
    logger.debug("Inside Upload Region Icon Image Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Region Icon Image uploaded by User Id: {user_id}")
        region_details_collection = db[constants.REGION_DETAILS_SCHEMA]
        region_details = region_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(region_id)}
        )
        if not region_details:
            logger.error(f"Region with Id: {region_id} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Region with Id: {region_id} does not exist"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        key = region_details.get(constants.ICON_IMAGE_FIELD)

        file_name = region_icon_image.filename
        if file_name == "":
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Please select image"
            )
        contents = region_icon_image.file.read()
        fileobj = io.BytesIO()
        fileobj.write(contents)
        fileobj.seek(0)
        response_status = s3.upload_file_via_upload_object_url(key, fileobj)
        cloudfront_url = core_cloudfront.cloudfront_sign(key)
        if response_status != HTTPStatus.NO_CONTENT:
            logger.error(f"Error in uploading Region Icon Image")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Error in uploading Region Icon Image"},
                status_code=e.status_code,
            )
            return response

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.ICON_IMAGE_FIELD: cloudfront_url},
            status_code=HTTPStatus.OK,
        )

        return response

    except Exception as e:
        logger.error(f"Error in Upload Region Icon Image Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Upload Region Icon Image Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Upload Region Icon Image Service")
    return response


def update_region_icon(
    region_id,
    region_icon_image,
    token,
):
    logger.debug("Inside Update Region Icon Image Service")
    try:
        response = upload_region_icon(region_id, region_icon_image, token)
        if response.status_code != HTTPStatus.OK:
            return response
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Region Icon Image updated by User Id: {user_id}")

        region_details_collection = db[constants.REGION_DETAILS_SCHEMA]
        region_details = region_details_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(region_id)},
            {constants.UPDATE_INDEX_DATA: {constants.UPDATED_AT_FIELD: time.time()}},
        )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.ICON_IMAGE_FIELD: core_cloudfront.cloudfront_sign(region_details.get(
                    constants.ICON_IMAGE_FIELD
                ))
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update Region Icon Image Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update Region Icon Image Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Region Icon Image Service")
    return response


def update_region(
    request: admin_property_management_schemas.UpdateRegionSchemaRequest,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Update Region Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Region updated by User Id: {user_id}")
        region_collection = db[constants.REGION_DETAILS_SCHEMA]
        request.title = request.title.title()
        if not region_collection.find_one({constants.INDEX_ID: ObjectId(request.id)}):
            logger.error(f"Region with Id: {request.id} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Region with Id: {request.id} does not exist"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        if region_collection.find_one(
            {
                constants.TITLE_FIELD: request.title,
                constants.INDEX_ID: {"$ne": ObjectId(request.id)},
            }
        ):
            logger.error(f"Region with Title: {request.title} already exists")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Region with Title: {request.title} already exists"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        validated_index = jsonable_encoder(
            admin_property_management_schemas.UpdateRegionSchemaRequest(
                **request.model_dump()
            )
        )
        del validated_index[constants.ID]
        inserted_index = region_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(request.id)},
            {constants.UPDATE_INDEX_DATA: validated_index},
            return_document=True,
        )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.REGION_ID_FIELD: str(inserted_index.get(constants.INDEX_ID)),
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update Region Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update Region Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Region Service")
    return response


def add_property_category(
    request: admin_property_management_schemas.AddPropertyCategoryRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    logger.debug("Inside Add Property Category Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Property Category added by User Id: {user_id}")
        property_category_collection = db[constants.PROPERTY_CATEGORY_DETAILS_SCHEMA]
        request.title = request.title.title()
        if property_category_collection.find_one(
            {constants.TITLE_FIELD: request.title}
        ):
            logger.error(
                f"Property Category with Title: {request.title} already exists"
            )
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property Category with Title: {request.title} already exists"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        icon_image_key = (
            f"{constants.CATEGORY_ICON_BASE}/{request.title}.{constants.IMAGE_TYPE}"
        )
        validated_index = jsonable_encoder(
            admin_property_management_schemas.AddPropertyCategoryInDBSchema(
                **request.model_dump(), icon_image_key=icon_image_key
            )
        )
        inserted_index = property_category_collection.insert_one(validated_index)
        logger.debug(
            f"Property Category Added Successfully with Id: {inserted_index.inserted_id}"
        )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                "property_category_id": str(inserted_index.inserted_id),
                "property_category_icon_image": icon_image_key,
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Add Property Category Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Add Property Category Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Add Property Category Service")
    return response


def update_property_category(
    request: admin_property_management_schemas.UpdatePropertyCategoryRequest,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Update Property Category Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Property Category updated by User Id: {user_id}")

        property_category_collection = db[constants.PROPERTY_CATEGORY_DETAILS_SCHEMA]
        request.title = request.title.title()
        if not property_category_collection.find_one(
            {constants.INDEX_ID: ObjectId(request.id)}
        ):
            logger.error(f"Property Category with Id: {request.id} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property Category with Id: {request.id} does not exist"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        if property_category_collection.find_one(
            {
                constants.TITLE_FIELD: request.title,
                constants.INDEX_ID: {"$ne": ObjectId(request.id)},
            }
        ):
            logger.error(
                f"Property Category with Title: {request.title} already exists"
            )
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property Category with Title: {request.title} already exists"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        validated_index = jsonable_encoder(
            admin_property_management_schemas.UpdatePropertyCategoryRequest(
                **request.model_dump()
            )
        )
        del validated_index[constants.ID]
        inserted_index = property_category_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(request.id)},
            {constants.UPDATE_INDEX_DATA: validated_index},
            return_document=True,
        )
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.PROPERTY_CATEGORY_ID_FIELD: str(
                    inserted_index.get(constants.INDEX_ID)
                ),
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update Property Category Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Update Property Category Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Property Category Service")
    return response


def upload_property_category_icon(
    property_category_id,
    property_category_icon_image,
    token,
):
    logger.debug("Inside Upload Property Category Icon Image Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Property Category Icon Image uploaded by User Id: {user_id}")

        property_category_details_collection = db[
            constants.PROPERTY_CATEGORY_DETAILS_SCHEMA
        ]
        property_category_details = property_category_details_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_category_id)}
        )
        if not property_category_details:
            logger.error(
                f"Property Category with Id: {property_category_id} does not exist"
            )
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property Category with Id: {property_category_id} does not exist"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        key = property_category_details.get(constants.ICON_IMAGE_FIELD)

        file_name = property_category_icon_image.filename
        if file_name == "":
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Please select image"
            )

        contents = property_category_icon_image.file.read()
        fileobj = io.BytesIO()
        fileobj.write(contents)
        fileobj.seek(0)
        response_status = s3.upload_file_via_upload_object_url(key, fileobj)

        if response_status != HTTPStatus.NO_CONTENT:
            logger.error(f"Error in uploading Property Category Icon Image")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Error in uploading Property Category Icon Image"
                },
                status_code=e.status_code,
            )
            return response

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={constants.ICON_IMAGE_FIELD: key},
            status_code=HTTPStatus.OK,
        )

        return response

    except Exception as e:
        logger.error(f"Error in Upload Property Category Icon Image Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Upload Property Category Icon Image Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Upload Property Category Icon Image Service")
    return response


def update_property_category_icon(
    property_category_id,
    property_category_icon_image,
    token,
):
    logger.debug("Inside Update Property Category Icon Image Service")
    try:
        response = upload_property_category_icon(
            property_category_id, property_category_icon_image, token
        )
        if response.status_code != HTTPStatus.OK:
            return response
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Property Category Icon Image updated by User Id: {user_id}")

        property_category_details_collection = db[
            constants.PROPERTY_CATEGORY_DETAILS_SCHEMA
        ]
        property_category_details = (
            property_category_details_collection.find_one_and_update(
                {constants.INDEX_ID: ObjectId(property_category_id)},
                {
                    constants.UPDATE_INDEX_DATA: {
                        constants.UPDATED_AT_FIELD: time.time()
                    }
                },
            )
        )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={
                constants.ICON_IMAGE_FIELD: property_category_details.get(
                    constants.ICON_IMAGE_FIELD
                )
            },
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Update Property Category Icon Image Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Update Property Category Icon Image Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Update Property Category Icon Image Service")
    return response


def get_property_categories(token):
    logger.debug("Inside Get Property Category Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Property Category fetched by User Id: {user_id}")
        property_category_collection = db[constants.PROPERTY_CATEGORY_DETAILS_SCHEMA]
        property_categories = list(
            property_category_collection.find({}).sort(constants.CREATED_AT_FIELD, -1)
        )
        response_property_categories = []
        for property_category in property_categories:
            property_category[constants.ID] = str(property_category[constants.INDEX_ID])
            property_category[
                "property_category_icon_image"
            ] = core_cloudfront.cloudfront_sign(
                property_category[constants.ICON_IMAGE_FIELD]
            )
            del property_category[constants.INDEX_ID]
            response_property_categories.append(property_category)
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"property_categories": response_property_categories},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Property Category Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Property Category Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Property Category Service")
    return response


def set_top_properties(
    request: admin_property_management_schemas.SetTopPropertiesRequest,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Set Top Properties Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Top Properties set by User Id: {user_id}")

        region_collection = db[constants.REGION_DETAILS_SCHEMA]

        region_details = region_collection.find_one(
            {constants.INDEX_ID: ObjectId(request.region_id)}
        )

        if not region_details:
            logger.error(f"Region with Id: {request.region_id} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Region with Id: {request.region_id} does not exist"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        property_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        property_details = property_collection.find(
            {
                constants.INDEX_ID: {
                    "$in": [
                        ObjectId(property_id) for property_id in request.property_ids
                    ]
                }
            }
        )
        property_count = len(list(property_details))

        if len(request.property_ids) != property_count:
            logger.error(f"Property with Id: {request.property_ids} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property  with Id: {request.property_ids} does not exist, Please check the ids"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        region_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(request.region_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.TOP_PROPERTIES_FIELD: request.property_ids
                }
            },
            return_document=True,
        )
        # Logic Here
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"message": "Top Properties Set Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Set Top Properties Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Set Top Properties Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Set Top Properties Service")
    return response


def set_featured_properties(
    request: admin_property_management_schemas.SetFeaturedPropertiesRequest,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Set Featured Properties Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Top Featured set by User Id: {user_id}")

        region_collection = db[constants.REGION_DETAILS_SCHEMA]

        region_details = region_collection.find_one(
            {constants.INDEX_ID: ObjectId(request.region_id)}
        )

        if not region_details:
            logger.error(f"Region with Id: {request.region_id} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Region with Id: {request.region_id} does not exist"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        property_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        property_details = property_collection.find(
            {
                constants.INDEX_ID: {
                    "$in": [
                        ObjectId(property_id) for property_id in request.property_ids
                    ]
                }
            }
        )
        property_count = len(list(property_details))
        if len(request.property_ids) != property_count:
            logger.error(
                f"Property Category with Id: {request.property_ids} does not exist"
            )
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property Category with Id: {request.property_ids} does not exist, Please check the ids"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        region_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(request.region_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.FEATURED_PROPERTIES_FIELD: request.property_ids
                }
            },
            return_document=True,
        )
        # Logic Here
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"message": "Featured Properties Set Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Set Featured Properties Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Set Featured Properties Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Set Featured Properties Service")
    return response


def set_recommended_properties(
    request: admin_property_management_schemas.SetRecommendedPropertiesRequest,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Set Recommended Properties Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Top Recommended set by User Id: {user_id}")

        region_collection = db[constants.REGION_DETAILS_SCHEMA]

        region_details = region_collection.find_one(
            {constants.INDEX_ID: ObjectId(request.region_id)}
        )

        if not region_details:
            logger.error(f"Region with Id: {request.region_id} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Region with Id: {request.region_id} does not exist"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        property_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        property_details = property_collection.find(
            {
                constants.INDEX_ID: {
                    "$in": [
                        ObjectId(property_id) for property_id in request.property_ids
                    ]
                }
            }
        )
        property_count = len(list(property_details))
        if len(request.property_ids) != property_count:
            logger.error(
                f"Property Category with Id: {request.property_ids} does not exist"
            )
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property Category with Id: {request.property_ids} does not exist, Please check the ids"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        region_collection.find_one_and_update(
            {constants.INDEX_ID: ObjectId(request.region_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.RECOMMENDED_PROPERTIES_FIELD: request.property_ids
                }
            },
            return_document=True,
        )
        # Logic Here
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"message": "Recommended Properties Set Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Set Recommended Properties Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={
                constants.MESSAGE: f"Error in Set Recommended Properties Service: {e}"
            },
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Set Recommended Properties Service")
    return response


def get_candles_of_property(
    property_id: str,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    logger.debug("Inside Get Candles of Property Service")
    try:
        decoded_token = token_decoder(token)
        user_id = ObjectId(decoded_token.get(constants.ID))
        logger.debug(f"Candles of Property fetched by User Id: {user_id}")

        property_collection = db[constants.PROPERTY_DETAILS_SCHEMA]

        property_details = property_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )

        if not property_details:
            logger.error(f"Property with Id: {property_id} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property with Id: {property_id} does not exist"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        candle_collection = db[constants.CANDLE_DETAILS_SCHEMA]

        candle_details = candle_collection.find(
            {constants.PROPERTY_ID_FIELD: property_id}, {"_id": 1, "candle_data": 1}
        ).sort(constants.CREATED_AT_FIELD, -1)

        response_candle_details = []
        for candle_detail in candle_details:
            candle_detail[constants.ID] = str(candle_detail[constants.INDEX_ID])
            del candle_detail[constants.INDEX_ID]
            response_candle_details.append(candle_detail)

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"candles": response_candle_details},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Get Candles of Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Get Candles of Property Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Get Candles of Property Service")
    return response


def set_candles_of_property(request: UpdateCandleDataSchema, token):
    logger.debug("Inside Set Candles of Property Service")
    try:
        property_collection = db[constants.PROPERTY_DETAILS_SCHEMA]
        property_id = request.property_id
        property_details = property_collection.find_one(
            {constants.INDEX_ID: ObjectId(property_id)}
        )

        if not property_details:
            logger.error(f"Property with Id: {property_id} does not exist")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={
                    constants.MESSAGE: f"Property with Id: {property_id} does not exist"
                },
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response

        candle_collection = db[constants.CANDLE_DETAILS_SCHEMA]
        candle_list = [dict(candle) for candle in list(request.candle_data)]

        if len(candle_list) == 0:
            logger.error(f"Candle Data is empty")
            response = admin_property_management_schemas.ResponseMessage(
                type=constants.HTTP_RESPONSE_FAILURE,
                data={constants.MESSAGE: f"Candle Data is empty"},
                status_code=HTTPStatus.BAD_REQUEST,
            )
            return response
        
        latest_candle_price = candle_list[-1].get("price")

        candle_collection.update_one(
            {constants.PROPERTY_ID_FIELD: property_id},
            {constants.UPDATE_INDEX_DATA: {constants.CANDLE_DATA_FIELD: candle_list}},
        )

        property_collection.update_one(
            {constants.INDEX_ID: ObjectId(property_id)},
            {
                constants.UPDATE_INDEX_DATA: {
                    constants.PRICE_FIELD: latest_candle_price
                }
            },
        )

        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_SUCCESS,
            data={"message": "Candles Set Successfully"},
            status_code=HTTPStatus.OK,
        )
    except Exception as e:
        logger.error(f"Error in Set Candles of Property Service: {e}")
        response = admin_property_management_schemas.ResponseMessage(
            type=constants.HTTP_RESPONSE_FAILURE,
            data={constants.MESSAGE: f"Error in Set Candles of Property Service: {e}"},
            status_code=e.status_code if hasattr(e, "status_code") else 500,
        )
    logger.debug("Returning From the Set Candles of Property Service")
    return response
