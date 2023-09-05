import datetime
import rsa
from common_layer import constants
from botocore.signers import CloudFrontSigner
import time
from prospect_app.logging_module import logger
AWS_CLOUDFRONT_KEY_ID = constants.AWS_CLOUDFRONT_KEY_ID
AWS_CLOUDFRONT_PRIVATE_KEY = constants.AWS_CLOUDFRONT_PRIVATE_KEY


def rsa_signer(message):
    private_key = AWS_CLOUDFRONT_PRIVATE_KEY
    return rsa.sign(
        message, rsa.PrivateKey.load_pkcs1(private_key.encode("utf-8")), "SHA-1"
    )


def get_cloudfront_signer_instance():
    cloudfront_signer = CloudFrontSigner(AWS_CLOUDFRONT_KEY_ID, rsa_signer)
    return cloudfront_signer


def cloudfront_sign(s3_key_path, expires_days=1):
    logger.debug("Inside Cloudfront Sign")
    date = datetime.datetime.fromtimestamp(time.time() + 86400 * 2)
    cloudfront_signer_instance = get_cloudfront_signer_instance()
    url_base = constants.CLOUDFRONT_URL
    if s3_key_path.startswith("/"):
        s3_key_path = s3_key_path[1:]
    url = f"{url_base}{s3_key_path}"
    signed_url = cloudfront_signer_instance.generate_presigned_url(
        url, date_less_than=date
    )
    logger.debug("Returning From Cloudfront Sign")
    return signed_url
