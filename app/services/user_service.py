import httpx
from app.core.config import settings
from typing import Dict, Any, Optional

class UserService:
    def __init__(self):
        self.base_url = settings.USER_PORTAL_API_URL
        self.headers = {
            "X-API-KEY": settings.USER_PORTAL_API_KEY,
            "X-API-SECRET": settings.USER_PORTAL_API_SECRET
        }

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/external/login",
                headers={"X-API-KEY": settings.USER_PORTAL_API_KEY},
                data={"username": username, "password": password}
            )
            response.raise_for_status()
            return response.json()

    async def signup(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/external/create-user",
                headers=self.headers,
                json={
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "is_active": True
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_me(self, email: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/external/get-user",
                headers=self.headers,
                params={"email": email}
            )
            response.raise_for_status()
            return response.json()

user_service = UserService()
