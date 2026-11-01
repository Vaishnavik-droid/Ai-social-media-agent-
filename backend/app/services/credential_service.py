import datetime
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.core.config import settings
from app.core.encryption import encryption_service
from app.api.v1.routes.posts import _get_supabase_client, extract_user_id, to_uuid

logger = logging.getLogger("omnipulse.services.credentials")

# In-memory stores for fallback when Supabase is disconnected or for testing
_MEMORY_CONNECTIONS: Dict[str, Dict[str, Any]] = {}
_MEMORY_OAUTH_STATES: Dict[str, Dict[str, Any]] = {}


class CredentialService:
    """
    Centralized credential and connection persistence service.
    Stores access tokens and secrets encrypted at rest in Supabase.
    """

    def __init__(self):
        pass

    def _now_utc(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    def _iso_now(self) -> str:
        return self._now_utc().isoformat()

    # -------------------------------------------------------------------------
    # Platform Connection Management
    # -------------------------------------------------------------------------

    async def save_connection(
        self,
        platform: str,
        handle: str,
        access_token: str,
        account_id: Optional[str] = None,
        account_name: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime.datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scopes: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Encrypts tokens and durably persists connection in Supabase.
        """
        p_clean = platform.lower().strip()
        uid = user_id or extract_user_id()
        now_str = self._iso_now()

        enc_access_token = encryption_service.encrypt(access_token) if access_token else ""
        if refresh_token:
            enc_refresh_token = encryption_service.encrypt(refresh_token)
        else:
            # Preserve existing refresh token if already stored
            existing_cred = await self.get_credentials(p_clean, user_id=uid)
            if existing_cred and existing_cred.get("refresh_token"):
                enc_refresh_token = encryption_service.encrypt(existing_cred["refresh_token"])
            else:
                enc_refresh_token = None
        expires_str = token_expires_at.isoformat() if token_expires_at else None

        record = {
            "platform": p_clean,
            "user_id": uid,
            "handle": handle,
            "connected_user": account_id or handle,
            "account_id": account_id,
            "account_name": account_name or handle,
            "encrypted_access_token": enc_access_token,
            "encrypted_refresh_token": enc_refresh_token,
            "token_expires_at": expires_str,
            "scopes": scopes or "",
            "metadata": metadata or {},
            "status": "connected",
            "last_verified_at": now_str,
            "updated_at": now_str,
        }

        # 1. Update in-memory cache
        _MEMORY_CONNECTIONS[p_clean] = record

        # 2. Persist to Supabase
        client = _get_supabase_client()
        if client:
            try:
                # Upsert by (user_id, platform)
                db_id = to_uuid(f"conn-{uid}-{p_clean}")
                payload = {
                    "id": db_id,
                    "user_id": uid,
                    "platform": p_clean,
                    "handle": handle,
                    "status": "connected",
                    "account_id": account_id,
                    "account_name": account_name or handle,
                    "encrypted_access_token": enc_access_token,
                    "encrypted_refresh_token": enc_refresh_token,
                    "token_expires_at": expires_str,
                    "scopes": scopes or "",
                    "metadata": metadata or {},
                    "last_verified_at": now_str,
                    "updated_at": now_str,
                }
                client.table("platform_connections").upsert(payload).execute()
                logger.info(f"Persisted encrypted connection for '{p_clean}' ({handle}) in Supabase.")
            except Exception as e:
                logger.warning(f"Could not persist connection to Supabase ({e}). In-memory fallback retained.")

        return self.get_safe_connection_item(p_clean)

    async def get_credentials(self, platform: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Internal method for platform publishing adapters.
        Retrieves and decrypts stored tokens. Never expose to client!
        """
        p_clean = platform.lower().strip()

        # Prioritize Sandbox token for Pinterest Sandbox integration
        if p_clean == "pinterest":
            import os
            sandbox_token = getattr(settings, "PINTEREST_SANDBOX_TOKEN", "") or os.environ.get("PINTEREST_SANDBOX_TOKEN", "")
            if sandbox_token:
                return {
                    "platform": "pinterest",
                    "access_token": sandbox_token.strip(),
                    "refresh_token": None,
                    "account_id": "pinterest_sandbox_user",
                    "account_name": "Pinterest Sandbox",
                    "handle": "Pinterest Sandbox",
                    "metadata": {"mode": "sandbox"},
                    "token_expires_at": None,
                }

        record: Optional[Dict[str, Any]] = None

        client = _get_supabase_client()
        if client:
            try:
                res = client.table("platform_connections").select("*").eq("platform", p_clean).single().execute()
                if res.data:
                    record = res.data
            except Exception:
                pass

        if not record:
            record = _MEMORY_CONNECTIONS.get(p_clean)

        if not record or record.get("status") != "connected":
            return None

        enc_token = record.get("encrypted_access_token")
        if not enc_token:
            return None

        decrypted_token = encryption_service.decrypt(enc_token)
        if not decrypted_token:
            return None

        decrypted_refresh = encryption_service.decrypt(record.get("encrypted_refresh_token")) if record.get("encrypted_refresh_token") else None

        return {
            "platform": p_clean,
            "access_token": decrypted_token,
            "refresh_token": decrypted_refresh,
            "account_id": record.get("account_id"),
            "account_name": record.get("account_name"),
            "handle": record.get("handle"),
            "metadata": record.get("metadata") or {},
            "token_expires_at": record.get("token_expires_at"),
        }

    async def delete_connection(self, platform: str, user_id: Optional[str] = None) -> bool:
        """
        Removes credentials and resets connection state to disconnected.
        """
        p_clean = platform.lower().strip()

        # Record explicit disconnected state in memory to override any environment variable fallback
        _MEMORY_CONNECTIONS[p_clean] = {
            "platform": p_clean,
            "status": "disconnected",
            "is_configured": False,
            "encrypted_access_token": None,
            "encrypted_refresh_token": None,
            "handle": None,
        }

        client = _get_supabase_client()
        if client:
            try:
                client.table("platform_connections").delete().eq("platform", p_clean).execute()
                logger.info(f"Deleted credentials for platform '{p_clean}' in Supabase.")
            except Exception as e:
                logger.warning(f"Could not delete connection from Supabase: {e}")

        return True

    async def update_connection_status(
        self,
        platform: str,
        status: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Updates status and verification timestamp of an existing platform connection record.
        Preserves encrypted credentials even during transient errors.
        """
        p_clean = platform.lower().strip()
        now_str = self._iso_now()

        if p_clean in _MEMORY_CONNECTIONS:
            _MEMORY_CONNECTIONS[p_clean]["status"] = status
            _MEMORY_CONNECTIONS[p_clean]["last_verified_at"] = now_str
            if reason:
                _MEMORY_CONNECTIONS[p_clean]["status_reason"] = reason

        client = _get_supabase_client()
        if client:
            try:
                update_payload = {
                    "status": status,
                    "last_verified_at": now_str,
                }
                client.table("platform_connections").update(update_payload).eq("platform", p_clean).execute()
                return True
            except Exception as e:
                err_str = str(e).lower()
                if "check constraint" in err_str or "violates" in err_str:
                    try:
                        client.table("platform_connections").update({
                            "status": "error",
                            "last_verified_at": now_str,
                        }).eq("platform", p_clean).execute()
                        logger.warning(f"Fallback connection status 'error' persisted for '{p_clean}' pending migration 005: {e}")
                        return True
                    except Exception:
                        pass
                logger.error(f"Failed to update connection status in Supabase: {e}")
                return False
        return True

    def get_safe_connection_item(self, platform: str) -> Dict[str, Any]:
        """
        Returns safe public connection status for API responses.
        Prioritizes authoritative Supabase storage over memory cache.
        Contains NO tokens, secrets, or encrypted values.
        """
        p_clean = platform.lower().strip()
        names = {
            "bluesky": "Bluesky",
            "linkedin": "LinkedIn",
            "facebook": "Facebook",
            "instagram": "Instagram",
            "pinterest": "Pinterest",
            "youtube": "YouTube",
        }
        display_name = names.get(p_clean, p_clean.capitalize())

        # 1. Query Supabase directly as authoritative single source of truth
        record: Optional[Dict[str, Any]] = None
        client = _get_supabase_client()
        if client:
            try:
                res = client.table("platform_connections").select(
                    "id, platform, handle, status, account_id, account_name, token_expires_at, last_verified_at, encrypted_access_token"
                ).eq("platform", p_clean).single().execute()
                if res.data:
                    record = res.data
                    _MEMORY_CONNECTIONS[p_clean] = record
            except Exception as e:
                logger.debug(f"Supabase connection lookup notice for '{p_clean}': {e}")

        # Fallback to memory store if Supabase returned nothing
        if not record:
            record = _MEMORY_CONNECTIONS.get(p_clean)

        if record:
            raw_status = record.get("status") or "disconnected"

            # Check expiration if token_expires_at is present
            exp_str = record.get("token_expires_at")
            is_expired = False
            if exp_str:
                try:
                    exp_dt = datetime.datetime.fromisoformat(str(exp_str).replace("Z", "+00:00"))
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=datetime.timezone.utc)
                    if exp_dt < self._now_utc():
                        is_expired = True
                except Exception:
                    pass

            acc_id = record.get("account_id")
            acc_name = record.get("account_name")
            user = record.get("account_name") or record.get("handle") or record.get("account_id") or record.get("connected_user")
            last_v = record.get("last_verified_at")

            # Determine granular status and status reason
            if raw_status == "connected":
                final_status = "expired" if is_expired else "connected"
                reason = "Access token has expired. Please reconnect." if is_expired else None
            elif raw_status in ("expired", "reauth_required", "temp_unavailable", "error"):
                final_status = raw_status
                reason = (
                    "Reauthorization required."
                    if raw_status == "reauth_required"
                    else ("Verification temporarily unavailable." if raw_status == "temp_unavailable" else "Connection error.")
                )
            else:
                final_status = "disconnected"
                reason = None

            if final_status != "disconnected":
                return {
                    "id": p_clean,
                    "name": display_name,
                    "handle": record.get("handle") or ("Connected Account" if final_status == "connected" else "Connection Needed"),
                    "status": final_status,
                    "status_reason": reason,
                    "connected_user": user,
                    "connectedUser": user,
                    "account_id": acc_id,
                    "accountId": acc_id,
                    "account_name": acc_name,
                    "accountName": acc_name,
                    "last_verified_at": last_v,
                    "lastVerifiedAt": last_v,
                    "is_configured": True,
                    "isConfigured": True,
                }
            else:
                return {
                    "id": p_clean,
                    "name": display_name,
                    "handle": "Not Connected",
                    "status": "disconnected",
                    "status_reason": None,
                    "connected_user": None,
                    "connectedUser": None,
                    "account_id": None,
                    "accountId": None,
                    "account_name": None,
                    "accountName": None,
                    "last_verified_at": None,
                    "lastVerifiedAt": None,
                    "is_configured": False,
                    "isConfigured": False,
                }

        # 2. Check environment variable fallback
        env_configured = False
        default_handle = "Not Connected"
        default_user = None

        if p_clean == "bluesky" and settings.BLUESKY_HANDLE and settings.BLUESKY_APP_PASSWORD:
            env_configured = True
            default_handle = settings.BLUESKY_HANDLE
            default_user = settings.BLUESKY_HANDLE
        elif p_clean == "linkedin" and settings.LINKEDIN_ACCESS_TOKEN:
            env_configured = True
            default_handle = settings.LINKEDIN_AUTHOR_URN or "LinkedIn Account"
            default_user = settings.LINKEDIN_AUTHOR_URN
        elif p_clean == "pinterest":
            import os
            if getattr(settings, "PINTEREST_SANDBOX_TOKEN", "") or os.environ.get("PINTEREST_SANDBOX_TOKEN", ""):
                env_configured = True
                default_handle = "Pinterest Sandbox"
                default_user = "Pinterest Sandbox"

        return {
            "id": p_clean,
            "name": display_name,
            "handle": default_handle if env_configured else "Not Connected",
            "status": "connected" if env_configured else "disconnected",
            "status_reason": None,
            "connected_user": default_user,
            "connectedUser": default_user,
            "account_id": None,
            "accountId": None,
            "account_name": None,
            "accountName": None,
            "last_verified_at": None,
            "lastVerifiedAt": None,
            "is_configured": env_configured,
            "isConfigured": env_configured,
        }

    async def list_all_connections(self) -> List[Dict[str, Any]]:
        """
        Returns connection statuses for all registered platforms.
        """
        platforms = ["bluesky", "linkedin", "facebook", "instagram", "pinterest", "youtube"]
        return [self.get_safe_connection_item(p) for p in platforms]

    # -------------------------------------------------------------------------
    # OAuth State Management (CSRF Protection & Nonce Tracking)
    # -------------------------------------------------------------------------

    async def save_oauth_state(
        self,
        state_id: str,
        platform: str,
        redirect_origin: str,
        expires_in_seconds: int = 600,
    ) -> None:
        """
        Persists pending OAuth authorization state with expiration.
        """
        now = self._now_utc()
        expires_at = now + datetime.timedelta(seconds=expires_in_seconds)
        state_data = {
            "state_id": state_id,
            "platform": platform,
            "redirect_origin": redirect_origin,
            "expires_at": expires_at.isoformat(),
            "created_at": now.isoformat(),
        }

        # 1. In-memory cache
        _MEMORY_OAUTH_STATES[state_id] = state_data

        # 2. Persist to Supabase if available
        client = _get_supabase_client()
        if client:
            try:
                client.table("oauth_states").insert(state_data).execute()
            except Exception as e:
                logger.debug(f"Could not persist oauth state in Supabase: {e}")

    async def verify_and_consume_oauth_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """
        Validates that state exists and is not expired, then atomically deletes it (single-use).
        """
        if not state_id:
            return None

        state_data: Optional[Dict[str, Any]] = None

        # 1. Check in-memory store
        if state_id in _MEMORY_OAUTH_STATES:
            state_data = _MEMORY_OAUTH_STATES.pop(state_id)

        # 2. Check Supabase
        client = _get_supabase_client()
        if client:
            try:
                res = client.table("oauth_states").select("*").eq("state_id", state_id).single().execute()
                if res.data:
                    state_data = res.data
                    # Invalidate state immediately
                    client.table("oauth_states").delete().eq("state_id", state_id).execute()
            except Exception as e:
                logger.debug(f"Supabase oauth state check: {e}")

        if not state_data:
            return None

        # Verify expiration
        exp_str = state_data.get("expires_at")
        if exp_str:
            try:
                exp_dt = datetime.datetime.fromisoformat(exp_str.replace("Z", "+00:00"))
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=datetime.timezone.utc)
                if exp_dt < self._now_utc():
                    logger.warning(f"OAuth state {state_id} has expired.")
                    return None
            except Exception as e:
                logger.warning(f"Error parsing state expiration: {e}")
                return None

        return state_data


credential_service = CredentialService()
