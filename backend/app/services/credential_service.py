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

        # 1. Persist to Supabase as single source of truth
        client = _get_supabase_client()
        if client:
            # Ensure foreign key user profile exists in public.profiles before insert
            await self._ensure_profile_exists(uid, client=client)

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
                # Only cache in memory once durable persistence succeeds
                _MEMORY_CONNECTIONS[p_clean] = record
            except Exception as e:
                # Remove from memory if persistence failed; never report false success
                _MEMORY_CONNECTIONS.pop(p_clean, None)
                logger.error(f"Could not persist connection to Supabase for '{p_clean}': {e}")
                raise RuntimeError(f"Database persistence failed for '{p_clean}': {e}")
        else:
            # Standalone / mock mode without Supabase client
            _MEMORY_CONNECTIONS[p_clean] = record

        return self.get_safe_connection_item(p_clean, user_id=uid)

    async def _ensure_profile_exists(self, user_id: str, client: Any = None) -> bool:
        """
        Guarantees that a profile row exists in public.profiles for user_id
        before any platform_connections row referencing it is inserted.
        If missing, creates it using auth.users metadata.
        """
        if not user_id:
            return False
        client = client or _get_supabase_client()
        if not client:
            return False
        try:
            p_check = client.table("profiles").select("id").eq("id", user_id).limit(1).execute()
            if p_check.data and len(p_check.data) > 0:
                return True

            logger.warning(f"Profile missing for user '{user_id}'. Attempting automatic recovery from auth.users.")
            try:
                user_obj = client.auth.admin.get_user_by_id(user_id)
                if user_obj and hasattr(user_obj, "user"):
                    u = user_obj.user
                    meta = getattr(u, "user_metadata", {}) or {}
                    email = getattr(u, "email", "") or f"{user_id}@omnipulse.local"
                    full_name = meta.get("full_name") or meta.get("name") or email.split("@")[0]
                    username = meta.get("username") or email.split("@")[0]
                    client.table("profiles").insert({
                        "id": user_id,
                        "email": email,
                        "full_name": full_name,
                        "username": username,
                    }).execute()
                    logger.info(f"Successfully restored missing profile for user '{user_id}'.")
                    return True
            except Exception as auth_err:
                logger.error(f"Could not retrieve auth user to restore profile: {auth_err}")
        except Exception as e:
            logger.debug(f"Profile check notice: {e}")
        return False

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
                uid = user_id or extract_user_id()
                query = client.table("platform_connections").select("*").eq("platform", p_clean)
                if uid:
                    query = query.eq("user_id", uid)
                res = query.limit(1).execute()
                if res.data and len(res.data) > 0:
                    record = res.data[0]
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
                uid = user_id or extract_user_id()
                query = client.table("platform_connections").delete().eq("platform", p_clean)
                if uid:
                    query = query.eq("user_id", uid)
                query.execute()
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
                uid = user_id or extract_user_id()
                update_payload = {
                    "status": status,
                    "last_verified_at": now_str,
                }
                query = client.table("platform_connections").update(update_payload).eq("platform", p_clean)
                if uid:
                    query = query.eq("user_id", uid)
                query.execute()
                return True
            except Exception as e:
                err_str = str(e).lower()
                if "check constraint" in err_str or "violates" in err_str:
                    try:
                        uid = user_id or extract_user_id()
                        fallback_query = client.table("platform_connections").update({
                            "status": "error",
                            "last_verified_at": now_str,
                        }).eq("platform", p_clean)
                        if uid:
                            fallback_query = fallback_query.eq("user_id", uid)
                        fallback_query.execute()
                        logger.warning(f"Fallback connection status 'error' persisted for '{p_clean}' pending migration 005: {e}")
                        return True
                    except Exception:
                        pass
                logger.error(f"Failed to update connection status in Supabase: {e}")
                return False
        return True

    def get_safe_connection_item(self, platform: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns safe public connection status for API responses.
        Prioritizes authoritative Supabase storage over memory cache.
        Contains NO tokens, secrets, or encrypted values.
        """
        p_clean = platform.lower().strip()
        uid = user_id or extract_user_id()
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
                query = client.table("platform_connections").select(
                    "id, platform, handle, status, account_id, account_name, token_expires_at, last_verified_at, encrypted_access_token"
                ).eq("platform", p_clean)
                if uid:
                    query = query.eq("user_id", uid)
                res = query.limit(1).execute()
                if res.data and len(res.data) > 0:
                    record = res.data[0]
                    _MEMORY_CONNECTIONS[p_clean] = record
                else:
                    mem_rec = _MEMORY_CONNECTIONS.get(p_clean)
                    if mem_rec and mem_rec.get("status") == "disconnected":
                        record = mem_rec
                    else:
                        _MEMORY_CONNECTIONS.pop(p_clean, None)
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

    async def list_all_connections(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns connection statuses for all registered platforms.
        """
        platforms = ["bluesky", "linkedin", "facebook", "instagram", "pinterest", "youtube"]
        return [self.get_safe_connection_item(p, user_id=user_id) for p in platforms]

    # -------------------------------------------------------------------------
    # OAuth State Management (CSRF Protection & Nonce Tracking)
    # -------------------------------------------------------------------------

    async def save_oauth_state(
        self,
        state_id: str,
        platform: str,
        redirect_origin: str,
        expires_in_seconds: int = 600,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Persists pending OAuth authorization state with expiration and user binding.
        """
        now = self._now_utc()
        expires_at = now + datetime.timedelta(seconds=expires_in_seconds)
        resolved_uid = user_id or extract_user_id()
        state_data = {
            "state_id": state_id,
            "platform": platform,
            "redirect_origin": redirect_origin,
            "user_id": resolved_uid,
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
                # If user_id column is not yet migrated, fall back to legacy schema
                err_str = str(e).lower()
                if "column" in err_str and "user_id" in err_str:
                    try:
                        legacy_payload = {k: v for k, v in state_data.items() if k != "user_id"}
                        client.table("oauth_states").insert(legacy_payload).execute()
                    except Exception:
                        pass
                else:
                    logger.debug(f"Could not persist oauth state in Supabase: {e}")

    async def verify_and_consume_oauth_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """
        Validates that state exists and is not expired, then atomically deletes it (single-use).
        """
        if not state_id:
            return None

        state_data: Optional[Dict[str, Any]] = None

        # 1. Check in-memory store
        cached_mem = _MEMORY_OAUTH_STATES.pop(state_id, None)
        if cached_mem:
            state_data = cached_mem

        # 2. Check Supabase
        client = _get_supabase_client()
        if client:
            try:
                res = client.table("oauth_states").select("*").eq("state_id", state_id).single().execute()
                if res.data:
                    # Merge with memory data if user_id was stored in memory
                    db_state = res.data
                    if cached_mem and cached_mem.get("user_id"):
                        db_state["user_id"] = cached_mem["user_id"]
                    state_data = db_state
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
