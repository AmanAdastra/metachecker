from common_layer import constants
import boto3
from botocore.client import Config
import requests
from fastapi import HTTPException
import json

s3_client = boto3.client(
    constants.S3_SERVICE,
    aws_access_key_id=constants.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=constants.AWS_SECRET_ACCESS_KEY,
    region_name=constants.AWS_REGION,
    config=Config(signature_version=constants.SIGNATURE_VERSION),
)


def generate_upload_object_url(key):
    response = s3_client.generate_presigned_post(
        Bucket=constants.S3_BUCKET_NAME,
        Key=key,
        ExpiresIn=int(constants.S3_PRESIGNED_EXPIRATION),
        Fields={constants.AWS_CONTENT_TYPE_KEY: constants.JPEG_CONTENT_TYPE},
        Conditions=[{constants.AWS_CONTENT_TYPE_KEY: constants.JPEG_CONTENT_TYPE}],
    )
    return response


def upload_file_via_upload_object_url(key, file_object):
    response = generate_upload_object_url(key)
    try:
        r = requests.post(
            response["url"],
            data=response["fields"],
            files={"file": file_object},
        )
    except Exception as e:
        print("Exception Occurred: ", e)
        raise HTTPException(status_code=500, detail=f"{e}")
    return r.status_code


def get_download_url(key):
    client_method = constants.GET_S3_OBJECT
    method_parameters = {
        constants.S3_BUCKET: constants.S3_BUCKET_NAME,
        constants.S3_KEY: key,
        constants.AWS_RESPONSE_CONTENT_TYPE_KEY: constants.JPEG_CONTENT_TYPE,
    }
    get_url = s3_client.generate_presigned_url(
        ClientMethod=client_method,
        Params=method_parameters,
        ExpiresIn=constants.S3_PRESIGNED_EXPIRATION,
    )

    return get_url

def delete_uploaded_object(key):
    try:
        response = s3_client.delete_object(
            Bucket=constants.S3_BUCKET_NAME,
            Key=key,
        )
    except Exception as e:
        print("Exception Occurred: ", e)
        raise HTTPException(status_code=500, detail=f"{e}")
    return response


def generate_pdf_upload_object_url(key):
    response = s3_client.generate_presigned_post(
        Bucket=constants.S3_BUCKET_NAME,
        Key=key,
        ExpiresIn=int(constants.S3_PRESIGNED_EXPIRATION),
        Fields={constants.AWS_CONTENT_TYPE_KEY: constants.PDF_CONTENT_TYPE},
        Conditions=[{constants.AWS_CONTENT_TYPE_KEY: constants.PDF_CONTENT_TYPE}],
    )
    return response

def upload_pdf_file_via_upload_object_url(key, file_object):
    response = generate_pdf_upload_object_url(key)
    try:
        r = requests.post(
            response["url"],
            data=response["fields"],
            files={"file": file_object},
        )
    except Exception as e:
        print("Exception Occurred: ", e)
        raise HTTPException(status_code=500, detail=f"{e}")
    return r.status_code