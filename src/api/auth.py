"""
Authentication middleware for AWS Cognito integration
"""

import os
import jwt
from typing import Optional
from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from functools import lru_cache

from src.utils.exceptions import AuthenticationException, InvalidTokenException
from src.utils.logger import get_structured_logger

logger = get_structured_logger(__name__)
security = HTTPBearer()


class CognitoAuth:
    """AWS Cognito authentication handler"""

    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_CLIENT_ID')
        self.jwks_url = None

        if self.user_pool_id:
            self.jwks_url = (
                f"https://cognito-idp.{self.region}.amazonaws.com/"
                f"{self.user_pool_id}/.well-known/jwks.json"
            )

    @lru_cache(maxsize=1)
    def get_jwks(self) -> dict:
        """
        Fetch JSON Web Key Set from Cognito.
        Cached to avoid repeated requests.
        """
        if not self.jwks_url:
            raise AuthenticationException("Cognito not configured")

        try:
            response = requests.get(self.jwks_url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Failed to fetch JWKS", error=e)
            raise AuthenticationException(f"Failed to fetch JWKS: {str(e)}")

    def get_public_key(self, token: str) -> str:
        """
        Extract public key from JWKS for token verification.

        Args:
            token: JWT token

        Returns:
            Public key for verification
        """
        try:
            # Decode header without verification to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')

            if not kid:
                raise InvalidTokenException("Token missing key ID")

            # Find matching key in JWKS
            jwks = self.get_jwks()
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    # Convert JWK to PEM format
                    return jwt.algorithms.RSAAlgorithm.from_jwk(key)

            raise InvalidTokenException("Public key not found in JWKS")

        except jwt.InvalidTokenError as e:
            logger.error("Invalid token", error=e)
            raise InvalidTokenException(str(e))

    def verify_token(self, token: str) -> dict:
        """
        Verify JWT token and return claims.

        Args:
            token: JWT token from Authorization header

        Returns:
            dict: Token claims including user_id

        Raises:
            InvalidTokenException: If token is invalid
        """
        try:
            # Get public key
            public_key = self.get_public_key(token)

            # Verify and decode token
            claims = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=self.client_id,
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_aud': True
                }
            )

            logger.info(
                "Token verified successfully",
                user_id=claims.get('sub'),
                token_use=claims.get('token_use')
            )

            return claims

        except jwt.ExpiredSignatureError:
            raise InvalidTokenException("Token has expired")
        except jwt.InvalidAudienceError:
            raise InvalidTokenException("Invalid token audience")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenException(f"Invalid token: {str(e)}")


# Global auth instance
_cognito_auth = CognitoAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency to extract and validate user from JWT token.

    Args:
        credentials: Authorization credentials from header

    Returns:
        str: User ID (Cognito sub)

    Raises:
        HTTPException: If authentication fails
    """
    # Check if in development mode
    app_env = os.getenv('APP_ENV', 'production')

    if app_env == 'development':
        # Allow bypass in development
        logger.warning("Using development mode - authentication bypassed")
        return os.getenv('DEV_USER_ID', 'dev-user-123')

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Verify token
        claims = _cognito_auth.verify_token(credentials.credentials)

        # Extract user ID (sub claim)
        user_id = claims.get('sub')
        if not user_id:
            raise InvalidTokenException("Token missing user ID")

        return user_id

    except InvalidTokenException as e:
        logger.error("Authentication failed", error=e)
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error("Unexpected authentication error", error=e)
        raise HTTPException(
            status_code=500,
            detail="Authentication service error"
        )


async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Optional authentication - returns user ID if authenticated, None otherwise.

    Args:
        authorization: Optional Authorization header

    Returns:
        Optional[str]: User ID if authenticated, None otherwise
    """
    if not authorization:
        return None

    try:
        # Extract token from "Bearer <token>"
        if not authorization.startswith('Bearer '):
            return None

        token = authorization[7:]  # Remove "Bearer " prefix

        # Verify token
        claims = _cognito_auth.verify_token(token)
        return claims.get('sub')

    except Exception as e:
        logger.warning("Optional auth failed", error=e)
        return None


def require_roles(*required_roles: str):
    """
    Decorator factory for role-based access control.

    Usage:
        @app.get("/admin")
        @require_roles("admin", "superuser")
        async def admin_endpoint(user_id: str = Depends(get_current_user)):
            ...
    """
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> str:
        """Check if user has required roles"""
        try:
            claims = _cognito_auth.verify_token(credentials.credentials)
            user_id = claims.get('sub')

            # Extract roles from token (custom claim)
            user_roles = claims.get('cognito:groups', [])

            # Check if user has any of the required roles
            if not any(role in user_roles for role in required_roles):
                logger.warning(
                    "Access denied - insufficient permissions",
                    user_id=user_id,
                    required_roles=required_roles,
                    user_roles=user_roles
                )
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )

            return user_id

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Role check failed", error=e)
            raise HTTPException(
                status_code=500,
                detail="Authorization service error"
            )

    return Depends(role_checker)


class APIKeyAuth:
    """Simple API key authentication for service-to-service communication"""

    def __init__(self):
        self.api_keys = set(
            os.getenv('API_KEYS', '').split(',')
        ) if os.getenv('API_KEYS') else set()

    def verify_api_key(self, api_key: str) -> bool:
        """Verify if API key is valid"""
        return api_key in self.api_keys


_api_key_auth = APIKeyAuth()


async def verify_api_key(
    x_api_key: Optional[str] = Header(None)
) -> str:
    """
    FastAPI dependency for API key authentication.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        str: Service identifier

    Raises:
        HTTPException: If API key is invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )

    if not _api_key_auth.verify_api_key(x_api_key):
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return "service-account"
