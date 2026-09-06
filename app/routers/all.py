from fastapi import APIRouter, Depends
from app.models.models import User
from app.dependency.dependency import getCurrentUser
from app.helpers.helper import createUploadSignature
router = APIRouter()

@router.get("/upload-signature")
def getUploadSignature(user: User = Depends(getCurrentUser)):
    return {
        "data": createUploadSignature(),
        "message": "signature generation successful",
        "status": 200
    }