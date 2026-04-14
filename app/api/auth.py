from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.services.user_service import user_service

router = APIRouter()

class UserSignup(BaseModel):
    email: str
    password: str
    full_name: str

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        return await user_service.login(form_data.username, form_data.password)
    except Exception as e:
        # In a real app, you'd want better error handling based on response status
        raise HTTPException(status_code=401, detail="Login failed")

@router.post("/signup")
async def signup(user: UserSignup):
    try:
        return await user_service.signup(user.email, user.password, user.full_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Signup failed")

@router.get("/me")
async def get_me(email: str):
    try:
        return await user_service.get_me(email)
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")
