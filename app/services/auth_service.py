"""
Auth service — orchestrates login/register through the User Portal microservice and issues store tokens.
All user management is delegated to the Central User Portal via its external API.
"""
import logging
from app.core.security import create_access_token
from app.clients.user_portal_client import user_portal_client
from app.clients.base import ServiceError

logger = logging.getLogger("tiana-bff")


class AuthService:
    async def login(self, email: str, password: str) -> dict:
        """
        Authenticate user via User Portal, then issue a store-scoped JWT.
        """
        email_clean = email.strip().lower()

        # Authenticate via User Portal (OAuth2 password flow)
        portal_response = await user_portal_client.login(email_clean, password)
        portal_token = portal_response.get("access_token")

        if not portal_token:
            raise ServiceError(401, "Invalid email or password", "UserPortal")

        # Fetch full user profile from portal
        user_info = await user_portal_client.get_user(email=email_clean)

        user_id = str(user_info.get("user_id", ""))
        user_email = user_info.get("email", email_clean)
        full_name = user_info.get("full_name", "")
        roles = user_info.get("roles", ["consumer"])

        # Issue store-scoped JWT
        store_token = create_access_token(
            data={
                "sub": user_id,
                "email": user_email,
                "name": full_name or user_email,
                "full_name": full_name or "",
                "roles": roles,
            }
        )

        return {
            "access_token": store_token,
            "token_type": "bearer",
            "user": {
                "user_id": user_id,
                "email": user_email,
                "full_name": full_name or "",
                "is_active": user_info.get("is_active", True),
                "roles": roles,
            },
        }

    async def register(self, email: str, password: str, full_name: str) -> dict:
        """
        Register a new user via User Portal, then auto-login and return store JWT.
        """
        email_clean = email.strip().lower()

        # Create user on the portal
        await user_portal_client.create_user(email_clean, password, full_name)

        # Auto-login after registration
        return await self.login(email_clean, password)

    async def get_profile(self, user_id: str) -> dict:
        """
        Fetch user profile from User Portal.
        """
        user_info = await user_portal_client.get_user(user_id=user_id)

        return {
            "user_id": str(user_info.get("user_id", "")),
            "email": user_info.get("email", ""),
            "full_name": user_info.get("full_name", ""),
            "is_active": user_info.get("is_active", True),
            "roles": user_info.get("roles", ["consumer"]),
        }

    async def update_profile(self, user_id: str, data: dict) -> dict:
        """
        Update user profile via User Portal.
        """
        user_info = await user_portal_client.update_user(user_id, data)

        return {
            "user_id": str(user_info.get("user_id", "")),
            "email": user_info.get("email", ""),
            "full_name": user_info.get("full_name", ""),
            "is_active": user_info.get("is_active", True),
            "roles": user_info.get("roles", ["consumer"]),
        }

    async def get_address(self, user_id: str) -> dict:
        """Fetch user address from User Portal."""
        try:
            return await user_portal_client.get_address(user_id)
        except ServiceError as e:
            if e.status_code == 404:
                return {}
            raise e

    async def update_address(self, user_id: str, address_data: dict) -> dict:
        """Create or update user address via User Portal."""
        return await user_portal_client.update_address(user_id, address_data)


auth_service = AuthService()
