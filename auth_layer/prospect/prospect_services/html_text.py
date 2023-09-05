from common_layer import constants
import os

from common_layer.common_services import html_compiler


path = os.getcwd()
STATIC_URL = constants.PROJECT_STATIC_CONTENT_URL

def generate_otp(otp):
    text = html_compiler.dynamic_html(file_path=r"./templates/email_verification_otp.html",OTP=otp,STATIC_URL=STATIC_URL)
    return text