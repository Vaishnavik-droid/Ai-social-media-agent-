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
        enc_refresh_token = encryption_service.encrypt(refresh_token) if refresh_token else None
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
                    "connected_user": account_id or handle,
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

        # Remove from in-memory cache
        _MEMORY_CONNECTIONS[p_clean] = {
            "status": "disconnected",
            "encrypted_access_token": None,
            "encrypted_refresh_token": None,
            "handle": "Not Connected",
            "connected_user": None,
            "account_id": None,
            "account_name": None,
        }

        client = _get_supabase_client()
        if client:
            try:
                client.table("platform_connections").delete().eq("platform", p_clean).execute()
                logger.info(f"Deleted credentials for platform '{p_clean}' in Supabase.")
            except Exception as e:
                logger.warning(f"Could not delete connection from Supabase: {e}")

        return True

    def get_safe_connection_item(self, platform: str) -> Dict[str, Any]:
        """
        Returns safe public connection status for API responses.
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

        # 1. Check database or memory record
        record = _MEMORY_CONNECTIONS.get(p_clean)
        client = _get_supabase_client()
        if not record and client:
            try:
                res = client.table("platform_connections").select("id, platform, handle, connected_user, status, account_id, account_name, last_verified_at").eq("platform", p_clean).single().execute()
                if res.data:
                    record = res.data
                    _MEMORY_CONNECTIONS[p_clean] = record
            except Exception:
                pass

        if record and record.get("status") == "connected":
            acc_id = record.get("account_id")
            acc_name = record.get("account_name")
            user = record.get("connected_user") or record.get("handle")
            last_v = record.get("last_verified_at")
            return {
                "id": p_clean,
                "name": display_name,
                "handle": record.get("handle") or "Connected Account",
                "status": "connected",
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

        if record and record.get("status") == "disconnected":
            return {
                "id": p_clean,
                "name": display_name,
                "handle": "Not Connected",
                "status": "disconnected",
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

        return {
            "id": p_clean,
            "name": display_name,
            "handle": default_handle if env_configured else "Not Connected",
            "status": "connected" if env_configured else "disconnected",
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
