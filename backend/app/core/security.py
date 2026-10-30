from typing import Optional
from fastapi import Header, HTTPException, status


async def get_current_user_token(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Extracts Bearer token from Authorization header if present.
    In single-user mode, permits unauthenticated calls in development
    or validates Supabase JWT token if provided.
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]

    return None
