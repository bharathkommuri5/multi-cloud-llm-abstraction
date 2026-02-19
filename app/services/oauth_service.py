"""
OAuth service for handling different identity providers (Google, Microsoft, GitHub, etc.)
Provides verification and user extraction logic for multiple OAuth providers.
"""

from typing import Dict, Any, Optional, Literal
from app.utils.logger import auth_logger as logger
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as grequests
from app.core.config import settings

# Type for supported providers
OAuthProviderType = Literal["google", "microsoft", "github"]


class OAuthProvider:
    """Base class for OAuth providers."""
    
    name: str
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify token and return user payload with standard fields: email, name, sub."""
        raise NotImplementedError


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider."""
    
    def __init__(self):
        self.name = "google"
        if not settings.GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID not configured")
        self.client_id = settings.GOOGLE_CLIENT_ID
    
    def verify_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Google ID token and extract user info."""
        try:
            payload = google_id_token.verify_oauth2_token(
                id_token, grequests.Request(), self.client_id
            )
            logger.info("Google ID token verified")
            
            # Normalize to standard fields (email, name, sub)
            return {
                "email": payload.get("email"),
                "name": payload.get("name", ""),
                "sub": payload.get("sub"),  # Google user ID
                "provider": self.name,
                "raw_payload": payload,
            }
        except Exception as e:
            logger.warning(f"Google token verification failed: {str(e)}")
            raise ValueError(f"Invalid Google ID token: {str(e)}")


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft OAuth provider (Azure AD)."""
    
    def __init__(self):
        self.name = "microsoft"
        if not settings.MICROSOFT_CLIENT_ID:
            raise ValueError("MICROSOFT_CLIENT_ID not configured")
        self.client_id = settings.MICROSOFT_CLIENT_ID
    
    def verify_token(self, access_token: str) -> Dict[str, Any]:
        """Verify Microsoft token by calling Microsoft Graph API."""
        import requests
        
        try:
            # Get user info from Microsoft Graph API
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info("Microsoft token verified via Graph API")
            
            return {
                "email": data.get("userPrincipalName") or data.get("mail"),
                "name": data.get("displayName", ""),
                "sub": data.get("id"),  # Microsoft user ID
                "provider": self.name,
                "raw_payload": data,
            }
        except Exception as e:
            logger.warning(f"Microsoft token verification failed: {str(e)}")
            raise ValueError(f"Invalid Microsoft token: {str(e)}")


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth provider."""
    
    def __init__(self):
        self.name = "github"
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
            raise ValueError("GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET not configured")
        self.client_id = settings.GITHUB_CLIENT_ID
        self.client_secret = settings.GITHUB_CLIENT_SECRET
    
    def verify_token(self, access_token: str) -> Dict[str, Any]:
        """Verify GitHub token by calling GitHub API."""
        import requests
        
        try:
            # Get user info from GitHub API
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = requests.get("https://api.github.com/user", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info("GitHub token verified via GitHub API")
            
            # GitHub doesn't always provide email via /user endpoint
            email = data.get("email")
            if not email:
                # Fallback to fetch email from user email endpoint
                email_response = requests.get("https://api.github.com/user/emails", headers=headers)
                if email_response.status_code == 200:
                    emails = email_response.json()
                    email = next((e["email"] for e in emails if e["primary"]), None)
            
            return {
                "email": email,
                "name": data.get("name", data.get("login", "")),
                "sub": str(data.get("id")),  # GitHub user ID
                "provider": self.name,
                "raw_payload": data,
            }
        except Exception as e:
            logger.warning(f"GitHub token verification failed: {str(e)}")
            raise ValueError(f"Invalid GitHub token: {str(e)}")


class OAuthProviderFactory:
    """Factory for creating OAuth provider instances."""
    
    _providers = {
        "google": GoogleOAuthProvider,
        "microsoft": MicrosoftOAuthProvider,
        "github": GitHubOAuthProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_name: str) -> OAuthProvider:
        """Get OAuth provider by name."""
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unsupported provider: {provider_name}. Supported: {list(cls._providers.keys())}")
        
        try:
            return provider_class()
        except ValueError as e:
            logger.warning(f"Failed to initialize {provider_name} provider: {str(e)}")
            raise
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported provider names."""
        return list(cls._providers.keys())
