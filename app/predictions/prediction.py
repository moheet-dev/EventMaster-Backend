from fastapi import APIRouter, Depends
from ..dependency.dependency import getCurrentUser
from ..models.models import User
import numpy as np
import joblib
from ..schemas.schema import TicketSaleFeature

model = joblib.load("sale_predictor.pkl")

router = APIRouter()

@router.post("/ticket_sale")
def predictTicketSale(modelFeatures: TicketSaleFeature, user: User = Depends(getCurrentUser)):
    input_array = np.array([
        [
            modelFeatures.days_since_live,
            modelFeatures.capacity
        ]
    ])

    result = model.predict(input_array)

    return {
        "data": {
            "prediction": round(result[0])
        },
        "message": "ticket sale prediction successful",
        "status": 200
    }