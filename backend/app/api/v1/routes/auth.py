"""
OmniPulse Authentication Route — Single-User & Multi-Method Authentication.
Resolves usernames (e.g., 'vaishnavi') to registered Supabase Auth email addresses,
authenticates using the official Supabase Gotrue password flow (public anon key),
and returns legitimate sessions to the frontend.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["auth"])


class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Account password")


class UserSessionProfile(BaseModel):
    id: str
    email: str
    full_name: str
    username: str
    brand_name: str
    avatar_char: str


class LoginResponse(BaseModel):
    success: bool
    resolved_email: str
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    user: UserSessionProfile


def _get_supabase_admin():
    """Service-role client used exclusively for read-only username-to-email resolution."""
    url = settings.SUPABASE_URL.strip() if settings.SUPABASE_URL else ""
    key = settings.SUPABASE_SERVICE_ROLE_KEY.strip() if settings.SUPABASE_SERVICE_ROLE_KEY else ""
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning(f"Could not initialize Supabase admin client: {e}")
        return None


def resolve_identifier_to_email(identifier: str) -> str:
    """
    Resolves a supplied username or email to the authoritative registered email.
    Recognizes 'vaishnavi' and maps it to the existing confirmed Supabase account:
    vaishnavikolekar2023@gmail.com (Auth UID: 88782b79-1b78-4e79-b3ab-294e179b3274).
    """
    clean_id = identifier.strip()

    # 1. If it is already an email address, NEVER rewrite it — return as-is immediately!
    if "@" in clean_id:
        return clean_id

    clean_lower = clean_id.lower()

    # 2. Database resolution via public.profiles table
    admin = _get_supabase_admin()
    if admin:
        try:
            # Check username column
            res = admin.table("profiles").select("email").ilike("username", clean_id).limit(1).execute()
            if res.data and res.data[0].get("email"):
                return res.data[0]["email"]

            # Check full_name column
            res2 = admin.table("profiles").select("email").ilike("full_name", f"%{clean_id}%").limit(1).execute()
            if res2.data and res2.data[0].get("email"):
                return res2.data[0]["email"]
        except Exception as e:
            logger.warning(f"Database username resolution error for '{clean_id}': {e}")

    # 3. Authoritative aliases for single-user accounts
    if clean_lower in ("vaishnavi", "vaishnavik"):
        return "vaishnavikolekar2023@gmail.com"
    if clean_lower in ("vaishnavi_pk", "vaishnavi pandurang kolekar"):
        return "kolekarvaishnavi77@gmail.com"

    # Fallback to identifier
    return clean_id


@router.get("/auth/resolve-username")
async def resolve_username_endpoint(username: str = Query(..., description="Username to resolve")):
    """Resolves a username to its registered email address."""
    clean_user = username.strip()
    if not clean_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username parameter cannot be empty."
        )

    resolved = resolve_identifier_to_email(clean_user)
    return {
        "success": True,
        "username": clean_user,
        "resolved_email": resolved,
        "is_mapped": resolved != clean_user,
    }


@router.post("/auth/login", response_model=LoginResponse)
async def login_endpoint(payload: LoginRequest):
    """
    Authenticates a user by username or email.
    1. Resolves username (e.g. 'vaishnavi') to the registered email.
    2. Calls legitimate Supabase Gotrue password authentication with public anon credentials.
    3. Returns the authenticated session to the client.
    """
    clean_id = payload.identifier.strip()
    clean_pwd = payload.password

    if not clean_id or not clean_pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide both your username/email and password."
        )

    # 1. Resolve username to registered email
    target_email = resolve_identifier_to_email(clean_id)

    # 2. Perform official Supabase password authentication using public client
    url = settings.SUPABASE_URL.strip() if settings.SUPABASE_URL else ""
    anon_key = (settings.SUPABASE_ANON_KEY or settings.SUPABASE_KEY or "").strip()

    if not url or not anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase credentials are not configured on the backend."
        )

    from supabase import create_client
    try:
        anon_client = create_client(url, anon_key)
        auth_res = anon_client.auth.sign_in_with_password({
            "email": target_email,
            "password": clean_pwd,
        })
    except Exception as e:
        err_msg = str(e)
        logger.warning(f"Supabase login failed for identifier '{clean_id}' (resolved: '{target_email}'): {err_msg}")

        # Check for invalid credentials
        if "Invalid login credentials" in err_msg or "invalid_credentials" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials. Please check your username/email and password."
            )
        if "Email not confirmed" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email confirmation is required. Please confirm your email in Supabase before signing in."
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )

    if not auth_res or not getattr(auth_res, "session", None) or not getattr(auth_res, "user", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not establish authenticated session with Supabase."
        )

    session = auth_res.session
    user = auth_res.user
    user_meta = getattr(user, "user_metadata", {}) or {}

    full_name = user_meta.get("full_name") or "vaishnavi"
    username_val = user_meta.get("username") or clean_id if not "@" in clean_id else "vaishnavi"
    brand_name = user_meta.get("brand_name") or "OmniPulse Media"
    avatar_char = full_name[0].upper() if full_name else "V"

    return LoginResponse(
        success=True,
        resolved_email=target_email,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in,
        token_type=session.token_type or "bearer",
        user=UserSessionProfile(
            id=str(user.id),
            email=user.email or target_email,
            full_name=full_name,
            username=username_val,
            brand_name=brand_name,
            avatar_char=avatar_char,
        )
    )

