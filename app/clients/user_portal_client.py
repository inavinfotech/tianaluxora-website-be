"""
HTTP client for the User Portal microservice.
Handles user authentication, registration, profile retrieval, and updates
via the User Portal's external API (/api/v1/external/).
"""
from app.clients.base import BaseClient
from app.core.config import settings


class UserPortalClient(BaseClient):
    """Client for communicating with the Central User Portal service."""

    def __init__(self):
        super().__init__(
            base_url=settings.USER_PORTAL_URL,
            api_key=settings.USER_PORTAL_API_KEY,
            api_secret=settings.USER_PORTAL_API_SECRET,
            service_name="UserPortal",
        )

    async def login(self, email: str, password: str) -> dict:
        """Authenticate user via OAuth2 password flow."""
        return await self.post(
            "/api/v1/external/login",
            data={"username": email, "password": password},
            headers=self._form_auth_headers(),
        )

    async def create_user(self, email: str, password: str, full_name: str) -> dict:
        """Register a new user on the portal."""
        return await self.post(
            "/api/v1/external/create-user",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
            },
        )

    async def get_user(self, user_id: str = None, email: str = None) -> dict:
        """Retrieve user information by ID or email."""
        params = {}
        if user_id:
            params["user_id"] = user_id
        if email:
            params["email"] = email
        return await self.get("/api/v1/external/get-user", params=params)

    async def update_user(self, user_id: str, data: dict) -> dict:
        """Update user profile information."""
        return await self.put(
            "/api/v1/external/update-user",
            json=data,
            params={"user_id": user_id},
        )

    async def get_address(self, user_id: str) -> dict:
        """Retrieve user address from central portal."""
        return await self.get(f"/api/v1/addresses/user/{user_id}")

    async def update_address(self, user_id: str, address_data: dict) -> dict:
        """Create or update user address on central portal."""
        return await self.post(f"/api/v1/addresses/user/{user_id}", json=address_data)

    async def list_users(self, skip: int = 0, limit: int = 100, search: str = None) -> list:
        """List all users from central portal."""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        return await self.get("/api/v1/external/list-users", params=params)


user_portal_client = UserPortalClient()
