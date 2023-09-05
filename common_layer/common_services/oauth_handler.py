from fastapi import Form
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime
import jwt
from common_layer import constants
from database import db
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Hash:
    def get_password_hash(password: str):
        return pwd_cxt.hash(password)

    def verify_password(hashed_password, plain_password):
        return pwd_cxt.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    data.update({constants.TOKEN_TYPE_KEY: constants.ACCESS_TOKEN})
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=constants.ACCESS_TOKEN_EXPIRY_TIME
        )
    to_encode.update({constants.TOKEN_EXPIRE_TIME_KEY: expire})
    encoded_jwt = jwt.encode(
        to_encode, constants.SECRET_KEY, algorithm=constants.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict):
    data.update({constants.TOKEN_TYPE_KEY: constants.REFRESH_TOKEN})
    expire = datetime.utcnow() + timedelta(minutes=constants.REFRESH_TOKEN_EXPIRY_TIME)
    data.update({constants.TOKEN_EXPIRE_TIME_KEY: expire})
    refresh_token = jwt.encode(
        data, constants.SECRET_KEY, algorithm=constants.ALGORITHM
    )
    return refresh_token


def authenticate_user_by_username(username: str, password: str):
    user_collection = db[constants.USER_DETAILS_SCHEMA]
    user_details = user_collection.find_one(
        {constants.USERNAME_FIELD: username}
    )
    if user_details:
        password_check = Hash.verify_password(
            user_details.get(constants.PASSWORD_FIELD), password
        )
        user_details[constants.INDEX_ID] = str(user_details[constants.INDEX_ID])
        return password_check and user_details
