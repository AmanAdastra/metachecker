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
def digilocker_verification(
    request: kyc_schema.DigilockerVerificationRequest,
    token: str = Depends(oauth2_scheme),
):
    logger.debug("Inside Digilocker Verification Route")
    response = kyc_service.digilocker_verification_endpoint(request, token)
    logger.debug("Returning from Digilocker Verification Route")
    return response


@router.get("/kyc/digilocker-access")
def digilocker_access(token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Digilocker Access Route")
    response = kyc_service.digilocker()
    logger.debug("Returning from Digilocker Access Route")
    return response


@router.post("/kyc/add-bank-details")
def add_bank_details(
    request: kyc_schema.BankDetails, token: str = Depends(oauth2_scheme)
):
    logger.debug("Inside add_bank_details route")
    response = kyc_service.add_bank_account(request, token)
    logger.debug("Returning from add_bank_details route")
    return response


@router.put("/kyc/update-bank-details")
def update_bank_details(
    request: kyc_schema.UpdateBankDetailsSchema, token: str = Depends(oauth2_scheme)
):
    logger.debug("Inside Update Bank Details route")
    response = kyc_service.update_bank_account(request, token)
    logger.debug("Returning from Update Bank Details route")
    return response


@router.get("/kyc/get-bank-details")
def get_bank_details(token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Get Bank Details route")
    response = kyc_service.get_bank_account_details(token)
    logger.debug("Returning from Get Bank Details route")
    return response


@router.delete("/kyc/delete-bank-details")
def delete_bank_details(record_id: str, token: str = Depends(oauth2_scheme)):
    logger.debug("Inside Delete Bank Details route")
    response = kyc_service.delete_bank_account_details(record_id, token)
    logger.debug("Returning from Delete Bank Details route")
    return response


@router.post("/kyc/add-kyc-details")
def add_kyc_details(
    request: kyc_schema.KycDetailsSchema, token: str = Depends(oauth2_scheme)
):
    logger.debug("Inside Add KYC Details route")
    response = kyc_service.add_kyc_details(request, token)
    logger.debug("Returning from Add KYC Details route")
    return response


@router.put("/kyc/update-kyc-details")
def update_kyc_details(
    request: kyc_schema.UpdateKycDetailsSchema, token: str = Depends(oauth2_scheme)
):
    logger.debug("Inside Add KYC Details route")
    response = kyc_service.update_kyc_details(request, token)
    logger.debug("Returning from Add KYC Details route")
    return response

@router.get("/kyc/get-kyc-details")
def get_kyc_details(
    token: str = Depends(oauth2_scheme)
):
    logger.debug("Inside Get KYC Details route")
    response = kyc_service.get_kyc_details( token)
    logger.debug("Returning from Get KYC Details route")
    return response