from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.services.user_service import user_service
from typing import Dict, Any

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)

async def get_current_user(token: str = Depends(reusable_oauth2)) -> Dict[str, Any]:
    try:
        validation_data = await user_service.validate_token(token)
        if not validation_data.get("is_valid"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        
        user_id = validation_data.get("user_id")
        user = await user_service.get_user_by_id(user_id)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
