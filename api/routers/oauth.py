from typing import Optional

import aiohttp
import os
import secrets
import time
import logging

from api.middleware.auth import _bearer
from api.middleware.auth import decode_jwt, get_session

from urllib.parse import urlencode

from fastapi import APIRouter as Router, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, JSONResponse

from helpers.database import Database
from api.middleware.auth import (
    create_jwt,
    fetch_user,
    revoke_session,
    store_session,
)

import dotenv

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

router = Router(prefix="/oauth", tags=["OAuth"])
db = Database(dotenv.get_key(dotenv.find_dotenv(), "DATABASE_URL"))

# Config

CLIENT_ID: str = os.environ["DISCORD_CLIENT_ID"]
CLIENT_SECRET: str = os.environ["DISCORD_CLIENT_SECRET"]
REDIRECT_URI: str = os.environ[
    "DISCORD_REDIRECT_URI"
]  # e.g. http://localhost:8000/oauth/callback
DISCORD_TOKEN: str = os.environ["BOT_TOKEN"]  # bot token, for bot <-> api calls

SCOPES = ["identify", "guilds"]  # guilds scope required for permission checks

DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/v10/oauth2/token"
DISCORD_REVOKE_URL = "https://discord.com/api/v10/oauth2/token/revoke"

# In-memory state store, TODO: redis
_state_store: dict[str, float] = {}
_STATE_TTL = 300  # 5 minutes


# Helpers


def _generate_state() -> str:
    state = secrets.token_urlsafe(32)
    _state_store[state] = time.time()
    return state


def _validate_state(state: str) -> None:
    issued_at = _state_store.pop(state, None)
    if issued_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state"
        )
    if time.time() - issued_at > _STATE_TTL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state expired"
        )


async def _exchange_code(code: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            DISCORD_TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            if not resp.ok:
                body = await resp.text()
                logger.error("Discord token exchange failed: %s", body)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to exchange code with Discord",
                )
            return await resp.json()


async def _revoke_discord_token(token: str, token_type: str = "access_token") -> None:
    async with aiohttp.ClientSession() as session:
        await session.post(
            DISCORD_REVOKE_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "token": token,
                "token_type_hint": token_type,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )


# Routes


@router.get(
    "/login",
    summary="Begin Discord OAuth2 flow",
    response_description="Redirects to Discord's authorization page",
    status_code=302,
)
def login() -> RedirectResponse:
    """
    Redirects the user to Discord's OAuth2 consent screen.
    After approval Discord will redirect to ``/oauth/callback``.
    """
    state = _generate_state()
    params = urlencode(
        {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": state,
            "prompt": "none",  # skip consent screen if already authorised
        }
    )
    return RedirectResponse(url=f"{DISCORD_AUTH_URL}?{params}")


@router.get(
    "/callback",
    summary="Discord OAuth2 callback",
    response_description="Returns a JWT access token",
    status_code=200,
)
async def callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
) -> JSONResponse:
    """
    Handles the redirect from Discord after the user authorises the application.

    Returns::

        {
            "access_token": "<jwt>",
            "token_type":   "Bearer",
            "user": {
                "id":            "...",
                "username":      "...",
                "discriminator": "...",
                "avatar":        "..."
            }
        }
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Discord OAuth error: {error}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state parameter",
        )

    _validate_state(state)

    token_data = await _exchange_code(code)

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    expires_in = token_data["expires_in"]

    user = await fetch_user(access_token)
    user_id = int(user["id"])

    await store_session(
        user_id=user_id,
        discord_access_token=access_token,
        discord_refresh_token=refresh_token,
        expires_in=expires_in,
    )

    jwt_token = create_jwt(user_id=user_id, discord_access_token=access_token)

    return JSONResponse(
        {
            "access_token": jwt_token,
            "token_type": "Bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "discriminator": user.get("discriminator", "0"),
                "avatar": user.get("avatar"),
                "global_name": user.get("global_name"),
            },
        }
    )


@router.get(
    "/me",
    summary="Fetch the authenticated user's profile",
    status_code=200,
)
async def me(request: Request) -> JSONResponse:
    """
    Returns the current user's Discord profile pulled from the local session.
    Requires a valid Bearer JWT in the Authorization header.
    """
    # Re-resolve manually (decorators aren't composable here the same way)
    credentials = await _bearer(request)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = decode_jwt(credentials.credentials)
    session = await get_session(int(payload["sub"]))

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found"
        )

    user = await fetch_user(session["discord_access_token"])

    return JSONResponse(
        {
            "id": user["id"],
            "username": user["username"],
            "discriminator": user.get("discriminator", "0"),
            "avatar": user.get("avatar"),
            "global_name": user.get("global_name"),
        }
    )


@router.post(
    "/logout",
    summary="Revoke the current session",
    status_code=200,
)
async def logout(request: Request) -> JSONResponse:
    """
    Revokes the Discord OAuth tokens and deletes the local session.
    Requires a valid Bearer JWT.
    """
    from api.middleware.auth import decode_jwt, get_session, _bearer

    credentials = await _bearer(request)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = decode_jwt(credentials.credentials)
    user_id = int(payload["sub"])

    session = await get_session(user_id)
    if session:
        await _revoke_discord_token(session["discord_access_token"], "access_token")
        await _revoke_discord_token(session["discord_refresh_token"], "refresh_token")

    await revoke_session(user_id)

    return JSONResponse({"message": "Successfully logged out"})
