from dataclasses import dataclass
import json
import os
from urllib import request
from urllib.error import HTTPError, URLError
from typing import Callable

from fastapi import Depends, Header

from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError

from .repositories import AdminRepository, get_admin_repository


@dataclass(frozen=True)
class AuthenticatedActor:
    uid: str
    email: str
    name: str | None = None


_firebase_app_initialized = False


def _ensure_firebase_app(settings: Settings) -> None:
    global _firebase_app_initialized
    if _firebase_app_initialized:
        return
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError as exc:
        raise ErclaveError(
            "firebase_admin_missing",
            "firebase-admin dependency is required when ERCLAVE_AUTH_MODE=firebase.",
            status_code=500,
        ) from exc

    if firebase_admin._apps:
        _firebase_app_initialized = True
        return

    emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST", "").strip()
    if emulator_host and settings.environment != "local":
        raise ErclaveError(
            "firebase_emulator_forbidden",
            "Firebase Auth Emulator is allowed only in the local environment.",
            status_code=500,
        )

    options = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
    if emulator_host:
        firebase_admin.initialize_app(options=options)
    else:
        firebase_admin.initialize_app(credentials.ApplicationDefault(), options)
    _firebase_app_initialized = True


def verify_firebase_bearer_token(authorization: str | None, settings: Settings) -> AuthenticatedActor:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ErclaveError("auth_required", "Authorization Bearer token is required.", status_code=401)

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise ErclaveError("auth_required", "Authorization Bearer token is required.", status_code=401)

    _ensure_firebase_app(settings)
    from firebase_admin import auth as firebase_auth

    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception as exc:
        raise ErclaveError("invalid_token", "Firebase ID token is invalid.", status_code=401) from exc

    email = str(decoded.get("email") or "").lower()
    if not email:
        raise ErclaveError("email_required", "Firebase token must include an email claim.", status_code=401)

    return AuthenticatedActor(
        uid=str(decoded.get("uid") or decoded.get("sub") or ""),
        email=email,
        name=decoded.get("name"),
    )


def ensure_firebase_user(email: str, display_name: str, settings: Settings) -> None:
    if settings.auth_mode != "firebase":
        return
    _ensure_firebase_app(settings)
    from firebase_admin import auth as firebase_auth

    normalized_email = email.lower()
    try:
        user = firebase_auth.get_user_by_email(normalized_email)
    except firebase_auth.UserNotFoundError:
        firebase_auth.create_user(email=normalized_email, display_name=display_name, disabled=False)
        return
    firebase_auth.update_user(user.uid, display_name=display_name, disabled=False)


def create_firebase_password_invitation(email: str, settings: Settings) -> dict:
    if settings.auth_mode != "firebase":
        return {
            "provider": "demo",
            "email": email.lower(),
            "email_sent": False,
            "reset_link": None,
            "delivery": "disabled",
        }

    normalized_email = email.lower()
    if settings.firebase_web_api_key:
        payload = json.dumps(
            {
                "requestType": "PASSWORD_RESET",
                "email": normalized_email,
                "continueUrl": settings.app_public_base_url,
            }
        ).encode("utf-8")
        firebase_request = request.Request(
            f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={settings.firebase_web_api_key}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(firebase_request, timeout=10) as response:
                if response.status < 200 or response.status >= 300:
                    raise ErclaveError(
                        "firebase_invitation_failed",
                        "Firebase password invitation could not be sent.",
                        status_code=502,
                    )
        except HTTPError as exc:
            raise ErclaveError(
                "firebase_invitation_failed",
                "Firebase password invitation could not be sent.",
                status_code=502,
                details={"status": exc.code},
            ) from exc
        except URLError as exc:
            raise ErclaveError(
                "firebase_invitation_unavailable",
                "Firebase password invitation service is unavailable.",
                status_code=502,
            ) from exc

        return {
            "provider": "firebase",
            "email": normalized_email,
            "email_sent": True,
            "reset_link": None,
            "delivery": "firebase_email",
        }

    _ensure_firebase_app(settings)
    from firebase_admin import auth as firebase_auth

    action_code_settings = firebase_auth.ActionCodeSettings(
        url=settings.app_public_base_url,
        handle_code_in_app=False,
    )
    reset_link = firebase_auth.generate_password_reset_link(normalized_email, action_code_settings)
    return {
        "provider": "firebase",
        "email": normalized_email,
        "email_sent": False,
        "reset_link": reset_link,
        "delivery": "generated_link",
    }


def delete_firebase_user_by_email(email: str, settings: Settings) -> None:
    if settings.auth_mode != "firebase":
        return
    _ensure_firebase_app(settings)
    from firebase_admin import auth as firebase_auth

    try:
        user = firebase_auth.get_user_by_email(email.lower())
    except firebase_auth.UserNotFoundError:
        return
    firebase_auth.delete_user(user.uid)


def get_authenticated_actor(
    authorization: str | None = Header(default=None, alias="Authorization"),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedActor | None:
    if settings.auth_mode != "firebase":
        return None
    return verify_firebase_bearer_token(authorization, settings)


def require_backoffice_admin(
    settings: Settings = Depends(get_settings),
    authenticated_actor: AuthenticatedActor | None = Depends(get_authenticated_actor),
) -> AuthenticatedActor | None:
    if settings.auth_mode != "firebase":
        return None
    if authenticated_actor is None:
        raise ErclaveError("auth_required", "Authorization Bearer token is required.", status_code=401)

    allowed_emails = {
        email.strip().lower()
        for email in settings.backoffice_admin_emails.split(",")
        if email.strip()
    }
    if not allowed_emails or authenticated_actor.email.lower() not in allowed_emails:
        raise ErclaveError(
            "backoffice_admin_required",
            "Authenticated actor is not allowed to use ERClave Backoffice.",
            status_code=403,
            details={"email": authenticated_actor.email},
        )
    return authenticated_actor


def require_permission_for_path_tenant(permission: str) -> Callable:
    def dependency(
        tenant_id: str,
        settings: Settings = Depends(get_settings),
        authenticated_actor: AuthenticatedActor | None = Depends(get_authenticated_actor),
        repository: AdminRepository = Depends(get_admin_repository),
    ) -> None:
        _require_permission(
            tenant_id=tenant_id,
            permission=permission,
            settings=settings,
            authenticated_actor=authenticated_actor,
            repository=repository,
        )

    return dependency


def require_permission_for_header_tenant(permission: str | tuple[str, ...]) -> Callable:
    def dependency(
        x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
        settings: Settings = Depends(get_settings),
        authenticated_actor: AuthenticatedActor | None = Depends(get_authenticated_actor),
        repository: AdminRepository = Depends(get_admin_repository),
    ) -> AuthenticatedActor | None:
        if not x_tenant_id:
            raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
        _require_permission(
            tenant_id=x_tenant_id,
            permission=permission,
            settings=settings,
            authenticated_actor=authenticated_actor,
            repository=repository,
        )
        return authenticated_actor

    return dependency


def _require_permission(
    tenant_id: str,
    permission: str | tuple[str, ...],
    settings: Settings,
    authenticated_actor: AuthenticatedActor | None,
    repository: AdminRepository,
) -> None:
    if settings.auth_mode != "firebase":
        return
    if authenticated_actor is None:
        raise ErclaveError("auth_required", "Authorization Bearer token is required.", status_code=401)
    context = repository.get_session_context_by_email(tenant_id, authenticated_actor.email)
    if context is None:
        raise ErclaveError(
            "session_context_not_found",
            "Session context not found for tenant and authenticated email.",
            status_code=404,
            details={"tenant_id": tenant_id, "email": authenticated_actor.email},
        )
    if context.tenant.status != "active":
        raise ErclaveError(
            "tenant_not_active",
            "The tenant must be active.",
            status_code=403,
            details={"tenant_id": tenant_id, "status": context.tenant.status},
        )
    if "admin" not in context.active_modules:
        raise ErclaveError(
            "admin_module_not_active",
            "The Administration module must be active.",
            status_code=403,
            details={"tenant_id": tenant_id},
        )
    required = (permission,) if isinstance(permission, str) else permission
    if not any(item in context.permissions for item in required):
        raise ErclaveError(
            "permission_denied",
            "Authenticated actor does not have the required permission.",
            status_code=403,
            details={"tenant_id": tenant_id, "permissions_any": list(required)},
        )
