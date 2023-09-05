import requests
import json
from common_layer import constants
from google.oauth2 import service_account
import google.auth
import google.auth.transport.requests
import os


SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]

secret_data = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLINET_X509_CERT_URL"),
    "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN"),
}


def _get_access_token():
    """Retrieve a valid access token that can be used to authorize requests.

    :return: Access token.
    """
    credentials = service_account.Credentials.from_service_account_info(
        secret_data, scopes=SCOPES
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    token = credentials.token
    return token

def push_notification_in_firebase(data: dict):
    token = _get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token,
    }
    firebase_data = {"module": data.get("module"),"title": data["title"], "body": data["description"], "is_scheduled" : "True", "scheduled_time" :str(data.get("scheduled_time")) }
    if data.get("extra") : firebase_data["ticket_id"] =  data.get("extra").get("ticket_id")
    body = {
        "message": {
            "data": firebase_data,
            "notification": {"title": data["title"], "body": data["description"]},
            "token": data["to"],
            "android": {"notification": {"click_action": "NOTIFICATION"}},
            "apns": {"payload": {"aps": {"category": "NOTIFICATION"}}},
        },
    }

    response = requests.post(
        constants.FIREBASE_URL, headers=headers, data=json.dumps(body)
    )
    return response