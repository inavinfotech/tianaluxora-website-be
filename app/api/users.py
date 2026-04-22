from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import user_service
from app.api import deps
from typing import Dict, Any

router = APIRouter()

@router.get("/address")
async def get_my_address(current_user: Dict[str, Any] = Depends(deps.get_current_user)):
    try:
        return await user_service.get_address(current_user["user_id"])
    except Exception as e:
        # Return None if address not found, rather than a hard 404 error to the frontend
        if "404" in str(e):
             return None
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/address")
async def save_my_address(
    address_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(deps.get_current_user)
):
    try:
        return await user_service.save_address(current_user["user_id"], address_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
