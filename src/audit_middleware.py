"""
Middleware for capturing request context for audit logging
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import contextvars
import time

# Context variables to store request info across the request lifecycle
request_context = contextvars.ContextVar('request_context', default=None)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to capture request context for audit logging"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and capture context information

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/endpoint in the chain

        Returns:
            The HTTP response
        """
        # Capture request start time
        start_time = time.time()

        # Extract request context
        context = {
            'ip_address': get_client_ip(request),
            'user_agent': request.headers.get('user-agent', ''),
            'endpoint': request.url.path,
            'http_method': request.method,
            'user_id': None,  # Will be extracted from request body/headers
            'user_role': None,
        }

        # Try to extract user_id from headers (if frontend sends it)
        user_id = request.headers.get('X-User-ID') or request.headers.get('X-Officer-ID')
        if user_id:
            context['user_id'] = user_id

        # Try to extract user role from headers
        user_role = request.headers.get('X-User-Role')
        if user_role:
            context['user_role'] = user_role

        # Store context for use in endpoints
        request_context.set(context)

        # Also attach to request state for easy access
        request.state.audit_context = context

        # Process the request
        try:
            response = await call_next(request)
            context['status_code'] = response.status_code
            context['success'] = response.status_code < 400
            return response
        except Exception as e:
            context['status_code'] = 500
            context['success'] = False
            context['error'] = str(e)
            raise
        finally:
            # Calculate request duration
            duration = time.time() - start_time
            context['duration_ms'] = int(duration * 1000)


def get_client_ip(request: Request) -> str:
    """
    Extract the client's IP address from the request

    Checks for X-Forwarded-For header (for proxied requests) first,
    then falls back to the direct client IP.

    Args:
        request: The FastAPI request object

    Returns:
        The client's IP address as a string
    """
    # Check for proxied IP in X-Forwarded-For header
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(',')[0].strip()

    # Check for X-Real-IP header (used by some proxies)
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return 'unknown'


def get_current_context():
    """
    Get the current request context

    Returns:
        Dictionary with request context (ip_address, user_agent, etc.)
        or None if not in request context
    """
    return request_context.get()


def update_context(**kwargs):
    """
    Update the current request context with additional information

    Useful for adding user_id after extracting it from request body

    Args:
        **kwargs: Key-value pairs to update in the context
    """
    context = request_context.get()
    if context:
        context.update(kwargs)
        request_context.set(context)
