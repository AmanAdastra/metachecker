from fastapi import APIRouter, Depends
from core_layer.signzy_kyc import kyc_schema, kyc_service
from logging_module import logger
from common_layer.common_services.oauth_handler import oauth2_scheme

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
    tags=["CUSTOMER KYC MANAGEMENT"],
)
@router.post("/kyc/digilocker-verification")
def digilocker_verification(request: kyc_schema.DigilockerVerificationRequest,token: str = Depends(oauth2_scheme) ):
    logger.debug("Inside Digilocker Verification Route")
    response = kyc_service.digilocker_verification(request,token)
    logger.debug("Returning from Digilocker Verification Route")
    return response

@router.get("/kyc/digilocker-access")
def digilocker_access(token: str = Depends(oauth2_scheme) ):
    logger.debug("Inside Digilocker Access Route")
    response = kyc_service.digilocker()
    logger.debug("Returning from Digilocker Access Route")
    return response