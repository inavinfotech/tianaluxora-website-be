from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import httpx
from app.core.config import settings

router = APIRouter()

class UserSignup(BaseModel):
    email: str
    password: str
    full_name: str

def get_headers():
    return {
        "X-API-KEY": settings.USER_PORTAL_API_KEY,
        "X-API-SECRET": settings.USER_PORTAL_API_SECRET
    }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.USER_PORTAL_API_URL}/external/login",
            headers={"X-API-KEY": settings.USER_PORTAL_API_KEY},
            data={"username": form_data.username, "password": form_data.password}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Login failed"))
        return response.json()

@router.post("/signup")
async def signup(user: UserSignup):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.USER_PORTAL_API_URL}/external/create-user",
            headers=get_headers(),
            json={"email": user.email, "password": user.password, "full_name": user.full_name, "is_active": True}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Signup failed"))
        return response.json()

@router.get("/me")
async def get_me(email: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.USER_PORTAL_API_URL}/external/get-user",
            headers=get_headers(),
            params={"email": email}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Failed to fetch user"))
        return response.json()
