import os

# Configuration
LOG_LEVEL = "DEBUG"
HTTP_RESPONSE_SUCCESS = "success"
HTTP_RESPONSE_FAILURE = "error"
MONGODB_URL = os.getenv("MONGODB_URL")
UPDATE_INDEX_DATA = "$set"
OR_INDEX_OPERATOR = "$or"
NOT_EQUAL_TO_OPERATOR = "$ne"
IMAGE_CONTENT_SIZE = int(os.getenv("IMAGE_CONTENT_SIZE"))


# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
SENDER_PHONE_NUMBER = os.getenv("SENDER_PHONE_NUMBER")
PROJECT_STATIC_CONTENT_URL = os.getenv("PROJECT_STATIC_CONTENT_URL")

# Sendgrid
MY_EMAIL = os.getenv("MY_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# JWT Token 
ACCESS_TOKEN_EXPIRY_TIME = float(os.getenv("ACCESS_TOKEN_EXPIRY_TIME"))
REFRESH_TOKEN_EXPIRY_TIME = float(os.getenv("REFRESH_TOKEN_EXPIRY_TIME"))
TOKEN_EXPIRE_TIME_KEY = "exp"
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Signzy
SIGNZY_USERNAME=os.getenv("SIGNZY_USERNAME")
SIGNZY_PASSWORD=os.getenv("SIGNZY_PASSWORD")
RAZORPAY_IFSC_URL = os.getenv("RAZORPAY_IFSC_URL")

# AWS Configuration
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_PRESIGNED_EXPIRATION = os.getenv("S3_PRESIGNED_EXPIRATION")
GET_S3_OBJECT = "get_object"
PUT_S3_OBJECT = "put_object"
SIGNATURE_VERSION = "s3v4"
S3_SERVICE = "s3"
S3_BUCKET = "Bucket"
S3_KEY = "Key"
JPEG_CONTENT_TYPE = "image/jpeg"
IMAGE_TYPE = "jpeg"
PDF_CONTENT_TYPE = "application/pdf"
PDF_TYPE = "pdf"
# AWS Cloudfront Configuration
AWS_CLOUDFRONT_KEY_ID = os.getenv("AWS_CLOUDFRONT_KEY_ID")
AWS_CLOUDFRONT_PRIVATE_KEY = os.getenv("AWS_CLOUDFRONT_PRIVATE_KEY")
CLOUDFRONT_URL = os.getenv("CLOUDFRONT_URL")

REGION_ICON_BASE = "region_icons"
WELCOME_CARD_BASE = "welcome_card"
ADS_CARD_BASE = "ads_card"
CTA_CARD_BASE = "cta_card"
CATEGORY_ICON_BASE = "category_icons"
PROPERTY_IMAGES_BASE = "property_images"
PROJECT_LOGO_BASE = "project_logo"
ADS_IMAGES_BASE = "ads_images"
PROPERTY_DOCUMENT_BASE = "property_documents"


# Firebase
FIREBASE_URL = os.getenv("FIREBASE_URL")

# Schemas
USER_DETAILS_SCHEMA = "user_details"
DEVICE_DETAILS_SCHEMA = "device_details"
USER_WALLET_SCHEMA = "user_wallet"
EMAIL_OTP_DETAILS_SCHEMA = "email_otp_details"
MOBILE_OTP_DETAILS_SCHEMA = "mobile_otp_details"
REGION_DETAILS_SCHEMA = "region_details"
WELCOME_CARD_DETAILS_SCHEMA = "welcome_card_details"
PROPERTY_CATEGORY_DETAILS_SCHEMA = "property_category_details"
RESIDENTIAL_PROPERTY_DETAILS_SCHEMA = "residential_property_details"
COMMERCIAL_PROPERTY_DETAILS_SCHEMA = "commercial_property_details"
FARM_PROPERTY_DETAILS_SCHEMA = "farm_property_details"
PROPERTY_DETAILS_SCHEMA = "property_details"
CANDLE_DETAILS_SCHEMA = "candle_details"
ADS_CARD_DETAILS_SCHEMA = "ads_card_details"
CTA_CARD_DETAILS_SCHEMA = "cta_card_details"
CUSTOMER_TRANSACTION_SCHEMA = "customer_transactions"
CUSTOMER_FIAT_TRANSACTIONS_SCHEMA = "customer_fiat_transactions"
CUSTOMER_LEADS_SCHEMA = "customer_leads"
CUSTOMER_CONVERSATION_SCHEMA = "customer_conversations"
CUSTOMER_PROPERTY_ANALYTICS_SCHEMA = "customer_property_analytics"
CUSTOMER_DAILY_PROPERTY_ANALYTICS_SCHEMA = "customer_daily_property_analytics"
CUSTOMER_BANK_DETAILS_SCHEMA = "customer_bank_details_schema"
CUSTOMER_KYC_DETAILS_SCHEMA = "kyc_details_schema"

# Schemas Fields
STATUS_FIELD = "status"
WELCOME_CARD_IMAGE_FIELD = "welcome_card_image"
ADS_CARD_IMAGE_FIELD = "ads_card_image"
CTA_CARD_IMAGE_FIELD = "cta_card_image"
EMAIL_ID_FIELD = "email_id"
MOBILE_NUMBER_FIELD = "mobile_number"
SECURE_PIN_FIELD = "secure_pin"
SECURE_PIN_SET_FIELD = "secure_pin_set"
PASSWORD_FIELD = "password"
IS_ACTIVE_FIELD = "is_active"
USER_ID_FIELD = "user_id"
USERNAME_FIELD = "username"
DEVICE_TOKEN_FIELD = "device_token"
DEVICE_ID_FIELD = "device_id"
LAST_LOGIN_AT = "last_login_at"
INDEX_ID = "_id"
MOBILE_OTP_FIELD = "mobile_otp"
EMAIL_OTP_FIELD = "email_otp"
CREATED_AT_FIELD = "created_at"
UPDATED_AT_FIELD = "updated_at"
PROFILE_PICTURE_FIELD = "profile_picture_url_key"
PROFILE_PICTURE_UPLOADED_FIELD = "profile_picture_uploaded"
PROFILE_PICTURE_BASE = "user_persona"
PROFILE_PICTURE_PATH = "profile_picture.jpeg"
USER_TYPE_FIELD = "user_type"
DEVICE_TOKEN_FIELD = "device_token"
ADMIN_SOURCE = "admin"
PROSPECT_SOURCE = "prospect"
TITLE_FIELD = "title"
DESCRIPTION_FIELD = "description"
LATITUDE_FIELD = "latitude"
LONGITUDE_FIELD = "longitude"
ICON_IMAGE_FIELD = "icon_image_key"
LOCATION_FIELD = "location"
REGION_ID_FIELD = "region_id"
PROPERTY_CATEGORY_ID_FIELD = "property_category_id"
DROPDOWN_TYPE_FIELD = "drop_down_type"
LISTED_BY_USER_ID_FIELD = "listed_by_user_id"
LISTED_BY_FIELD = "listed_by"
IS_FEATURED_FIELD = "is_featured"
IS_RECOMMENDED_FIELD = "is_recommended"
IS_INVESTMENT_PROPERTY="is_investment_property"
PROJECT_TITLE_FIELD = "project_title"
AD_DESCRIPTION_FIELD = "ad_description"
PRICE_FIELD = "price"
REGION_FIELD = "region"
IMAGES_FIELD = "images"
ADDRESS_FIELD = "address"
VIEW_COUNT_FIELD = "view_count"
TOP_PROPERTIES_FIELD = "top_properties"
FEATURED_PROPERTIES_FIELD = "featured_properties"
RECOMMENDED_PROPERTIES_FIELD = "recommended_properties"
PROPERTY_ID_FIELD = "property_id"
CANDLE_DATA_FIELD = "candle_data"
CANDLE_DATA_ID_FIELD = "candle_data_id"
PROJECT_LOGO_FIELD = "project_logo"
CATEGORY_FIELD = "category"
PROPERTY_DETAILS_ID_FIELD = "property_details_id"
PROPERTY_BROCHURE_FIELD = "property_brochure"
PROPERTY_DOCUMENT_FIELD = "property_document"
DOCUMENT_TITLE_FIELD = "document_title"
BROCHURE_TITLE_FIELD = "brochure_title"
PROPERTY_GAIN_FIELD = "property_gain"
STATUS_FIELD = "status"
SENDER_ID_FIELD = "sender_id"
RECIEVER_ID_FIELD = "reciever_id"
BANKING_NAME="banking_name"
ACCOUNT_NUMBER="account_number"
IFSC_CODE="ifsc_code"
IS_PRIMARY_ACCOUNT="is_primary"
AADHAR_NUMBER="aadhar_number"
PAN_NUMBER="pan_number"


# Messages
EMAIL_ALREADY_USED = "Email already used!"
MOBLIE_NO_ALREADY_USED = "Mobile Number already Used!"
PASSWORD_NOT_MATCH = "Password does not match!"
MOBILE_NO_NOT_EXIST = "Mobile Number does not exist!"
USER_IS_INACTIVE = "User status is Inactive!"
USER_NOT_FOUND = "User Not Found!"
PROFILE_DETAILS_COMPLETED = "Profile Details Completed"
PROFILE_DETAILS_INCOMPLETE = "Profile Details are Incomplete"
MOBILE_OTP_SENT = "OTP Sent on Mobile Number"
EMAIL_OTP_SENT = "OTP Sent on Email ID"
OTP_NOT_GENERATED = "OTP not Found"
OTP_DOES_NOT_MATCH = "OTP is Invalid"
OTP_VERIFIED_SUCCESSFULLY = "OTP Verified Successfully"
OTP_VERIFICATOIN_EMAIL = "OTP Verification via Email!"
EMAIL_OTP_FOR_REGISTRATION = "OTP for Email Verification"
SECURE_PIN_CHANGED = "Secure Pin Changed Successfully!"
SECURE_PIN_UPDATED = "Secure Pin Updated Successfully!"
OTP_EXPIRED_OR_INVALID = "OTP is expired or invalid"
PROFILE_PICTURE_UPLOADED = "Profile Picture Uploaded Successfully!"
PROFILE_PICTURE_FETCHED = "Profile Picture Fetched Successfully!"
INVALID_PROFILE_PICTURE_KEY = "Invalid Profile Picture Key!"
USER_DOES_NOT_EXIST = "User Does Not Exist!"
INVALID_USER_TYPE = "Invalid User Type!"
SECURE_PIN_MATCH = "Secure Pin Matched Successfully!"
SECURE_PIN_NOT_MATCH = "Secure Pin Not Matched!"
CUSTOMERS_NOT_ALLOWED = "Customers are not allowed to login here!"
BANK_ACCOUNT_ALREADY_EXIST = "Bank Account Number already Exist"
PRIMARY_ACCOUNT_EXIST = "Primary Bank Account Already Exist, Please remove it to mark this primary"
DELETE_PRIMARY_ACCOUNT = "You can not delete Primary Account"
RECORD_DOES_NOT_FOUND="Record does not found"
AADHAR_ALREADY_EXIST="Aadhar Number already Exist"
PAN_NUMBER_ALREADY_EXIST="Pan Number Already Exist"
# Response Keys
USER_DETAILS = "user_details"
MESSAGE = "message"
ID = "id"
ACCESS_TOKEN = "access_token"
REFRESH_TOKEN = "refresh_token"
TOKEN_TYPE_KEY = "token_type"
TOKEN_METHOD = "bearer"
AWS_RESPONSE_CONTENT_TYPE_KEY = "ResponseContentType"
AWS_CONTENT_TYPE_KEY = "Content-Type"
ROLES_AND_PERMISSIONS = "roles_and_permissions"