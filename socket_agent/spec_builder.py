"""Build socket-agent descriptor from FastAPI app."""

import inspect
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.routing import APIRoute

from .schemas import AuthInfo, EndpointInfo, SocketDescriptor


def build_descriptor(
    app: FastAPI,
    *,
    name: str,
    description: str,
    base_url: str,
) -> SocketDescriptor:
    """
    Build a socket-agent descriptor from a FastAPI app.

    Args:
        app: FastAPI application instance
        name: API name
        description: API description
        base_url: Base URL of the API

    Returns:
        SocketDescriptor instance
    """
    endpoints = []
    schemas = {}
    all_examples = []

    # Iterate through all routes
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        # Skip internal routes
        if route.path.startswith("/.well-known"):
            continue

        # Get the endpoint function
        endpoint_func = route.endpoint

        # Check if it has socket metadata
        if hasattr(endpoint_func, "_socket_meta"):
            meta = endpoint_func._socket_meta

            # Check for auth requirements
            auth_info = getattr(endpoint_func, "_socket_auth", {})
            auth_required = auth_info.get("required", False)
            scopes = auth_info.get("scopes", [])

            # Add endpoint info
            for method in route.methods:
                endpoints.append(
                    EndpointInfo(
                        path=route.path,
                        method=method,
                        summary=meta.get("summary", ""),
                        auth_required=auth_required,
                        scopes=scopes if scopes else None,
                    )
                )

            # Add schemas if provided
            if meta.get("request_schema") or meta.get("response_schema"):
                schema_key = route.path
                schemas[schema_key] = {}

                if meta.get("request_schema"):
                    schemas[schema_key]["request"] = meta["request_schema"]

                if meta.get("response_schema"):
                    schemas[schema_key]["response"] = meta["response_schema"]

            # Collect examples
            if meta.get("examples"):
                all_examples.extend(meta["examples"])

    # Check if any endpoints require auth
    auth_required_endpoints = [ep for ep in endpoints if ep.auth_required]
    has_auth = len(auth_required_endpoints) > 0

    # Create auth info
    auth = AuthInfo(type="none")
    if has_auth:
        # Get auth config from app state if available
        auth_config = getattr(app.state, "socket_agent_auth", {})
        server_id = auth_config.get("server_id")
        identity_service_url = auth_config.get("identity_service_url", "https://socketagent.io")

        auth = AuthInfo(
            type="bearer",
            description="JWT tokens from socketagent.id",
            identity_service_url=identity_service_url,
            server_id=server_id,
            audience="api",
            optional=False
        )

    # Create descriptor
    descriptor = SocketDescriptor(
        name=name,
        description=description,
        base_url=base_url,
        endpoints=endpoints,
        schemas=schemas,
        auth=auth,
        examples=all_examples,
    )

    # Check size constraints
    size_kb = descriptor.size_kb()
    if size_kb > 8:
        raise ValueError(
            f"Descriptor size ({size_kb:.2f}KB) exceeds 8KB limit. "
            "Reduce the number of endpoints or simplify schemas."
        )
    elif size_kb > 3:
        import warnings

        warnings.warn(
            f"Descriptor size ({size_kb:.2f}KB) exceeds recommended 3KB limit.",
            UserWarning,
        )

    return descriptor
