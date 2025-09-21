"""Authentication middleware and utilities for socket-agent."""

import hashlib
import time
from typing import Any, Dict, List, Optional, Union

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from .schemas import AuthInfo


class User(BaseModel):
    """User information from token validation."""

    id: int
    username: str
    email: Optional[str] = None
    created_at: str


class TokenValidationResult(BaseModel):
    """Result of token validation."""

    valid: bool
    user: Optional[User] = None
    error: Optional[str] = None


class TokenCache:
    """Simple in-memory token cache."""

    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, token: str) -> Optional[TokenValidationResult]:
        """Get cached validation result."""
        token_hash = self._hash_token(token)
        if token_hash in self._cache:
            entry = self._cache[token_hash]
            if time.time() - entry["timestamp"] < self.ttl:
                return TokenValidationResult(**entry["result"])
            else:
                del self._cache[token_hash]
        return None

    def set(self, token: str, result: TokenValidationResult) -> None:
        """Cache validation result."""
        token_hash = self._hash_token(token)
        self._cache[token_hash] = {
            "result": result.model_dump(),
            "timestamp": time.time()
        }

    def _hash_token(self, token: str) -> str:
        """Hash token for cache key."""
        return hashlib.sha256(token.encode()).hexdigest()


class SocketAgentAuthMiddleware:
    """FastAPI middleware for socket-agent authentication."""

    def __init__(
        self,
        app,
        identity_service_url: str,
        audience: Optional[str] = None,
        cache_ttl: int = 300,
        timeout: float = 5.0
    ):
        """
        Initialize authentication middleware.

        Args:
            app: FastAPI application
            identity_service_url: URL of socketagent.id service
            audience: Token audience for validation
            cache_ttl: Token cache TTL in seconds
            timeout: HTTP timeout for validation requests
        """
        self.app = app
        self.identity_service_url = identity_service_url.rstrip("/")
        self.audience = audience
        self.timeout = timeout
        self.cache = TokenCache(ttl=cache_ttl)
        self.security = HTTPBearer(auto_error=False)

        # Add middleware
        app.middleware("http")(self._middleware)

    async def _middleware(self, request: Request, call_next):
        """Middleware function to handle authentication."""
        # Store auth info in request state for access by endpoints
        request.state.auth = None
        request.state.user = None

        # Get authorization header
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]  # Remove "Bearer " prefix

            # Validate token
            validation_result = await self._validate_token(token)
            if validation_result.valid:
                request.state.auth = {"token": token, "valid": True}
                request.state.user = validation_result.user
            else:
                request.state.auth = {"token": token, "valid": False, "error": validation_result.error}

        response = await call_next(request)
        return response

    async def _validate_token(self, token: str) -> TokenValidationResult:
        """
        Validate token with identity service.

        Args:
            token: Bearer token to validate

        Returns:
            TokenValidationResult with validation status
        """
        # Check cache first
        cached_result = self.cache.get(token)
        if cached_result:
            return cached_result

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.identity_service_url}/v1/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 200:
                    user_data = response.json()
                    user = User(**user_data)
                    result = TokenValidationResult(valid=True, user=user)
                elif response.status_code == 401:
                    result = TokenValidationResult(valid=False, error="Invalid token")
                else:
                    result = TokenValidationResult(valid=False, error=f"Validation failed: {response.status_code}")

        except Exception as e:
            result = TokenValidationResult(valid=False, error=f"Validation error: {str(e)}")

        # Cache result
        self.cache.set(token, result)
        return result


def get_current_user(request: Request) -> User:
    """
    Dependency to get current authenticated user.

    Args:
        request: FastAPI request object

    Returns:
        User object if authenticated

    Raises:
        HTTPException: If not authenticated or token invalid
    """
    if not hasattr(request.state, "auth") or not request.state.auth:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not request.state.auth.get("valid", False):
        error = request.state.auth.get("error", "Invalid token")
        raise HTTPException(status_code=401, detail=error)

    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(status_code=401, detail="User information not available")

    return request.state.user


def auth_required(scopes: Optional[List[str]] = None):
    """
    Decorator to require authentication for an endpoint.

    Args:
        scopes: Required scopes (not implemented yet)

    Returns:
        Decorated function that enforces authentication
    """
    def decorator(func):
        # Store auth requirement metadata
        if not hasattr(func, "_socket_auth"):
            func._socket_auth = {}
        func._socket_auth["required"] = True
        func._socket_auth["scopes"] = scopes or []

        return func

    return decorator