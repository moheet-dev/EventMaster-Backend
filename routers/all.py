from fastapi import APIRouter, Depends
from models.models import User
from dependency.dependency import getCurrentUser
from helpers.helper import createUploadSignature
router = APIRouter()

@router.get("/upload-signature")
def getUploadSignature(user: User = Depends(getCurrentUser)):
    return {
        "data": createUploadSignature(),
        "message": "signature generation successful",
        "status": 200
    }