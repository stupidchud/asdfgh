from __future__ import annotations
from typing import Optional, Callable

import os
import time
import logging

from functools import wraps

import aiohttp
import jwt

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from helpers.database import Database

import dotenv

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

#  Constants

DISCORD_API = "https://discord.com/api/v10"
JWT_SECRET: str = os.environ["JWT_SECRET"]  # openssl rand -hex 32
JWT_ALGORITHM: str = "HS256"
JWT_TTL: int = 60 * 60 * 24 * 7  # 7 days

_db = Database(dotenv.get_key(dotenv.find_dotenv(), "DATABASE_URL"))
_bearer = HTTPBearer(auto_error=False)

#  Discord permission bit flags (subset)

PERMISSION_FLAGS: dict[str, int] = {
    "administrator": 0x0000000000000008,
    "manage_guild": 0x0000000000000020,
    "manage_roles": 0x0000000000000010,
    "manage_channels": 0x0000000000000010,
    "manage_messages": 0x0000000000002000,
    "kick_members": 0x0000000000000002,
    "ban_members": 0x0000000000000004,
    "moderate_members": 0x0000000400000000,
    "manage_webhooks": 0x0000000020000000,
    "manage_nicknames": 0x0000000008000000,
    "view_audit_log": 0x0000000000000080,
}

#  Token helpers


def create_jwt(user_id: int, discord_access_token: str) -> str:
    payload = {
        "sub": str(user_id),
        "dat": discord_access_token,  # used to hit Discord API on behalf of user
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_TTL,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


#  Session persistence


async def store_session(
    user_id: int,
    discord_access_token: str,
    discord_refresh_token: str,
    expires_in: int,
) -> None:
    await _db.execute(
        """
        INSERT INTO sessions (
            user_id,
            discord_access_token,
            discord_refresh_token,
            discord_token_expires_at
        ) VALUES (?, ?, ?, ?)
        ON CONFLICT (user_id) DO UPDATE SET
            discord_access_token = excluded.discord_access_token,
            discord_refresh_token = excluded.discord_refresh_token,
            discord_token_expires_at = excluded.discord_token_expires_at,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            discord_access_token,
            discord_refresh_token,
            int(time.time()) + expires_in,
        ),
    )


async def get_session(user_id: int) -> Optional[dict]:
    row = await _db.fetchone(
        "SELECT * FROM sessions WHERE user_id = ?",
        (user_id,),
    )
    return dict(row) if row else None


async def revoke_session(user_id: int) -> None:
    await _db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))


#  Discord API helpers


async def _discord_get(endpoint: str, access_token: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{DISCORD_API}{endpoint}",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as resp:
            if resp.status == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Discord token is invalid or expired",
                )
            if not resp.ok:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Discord API error: {resp.status}",
                )
            return await resp.json()


async def fetch_user(access_token: str) -> dict:
    return await _discord_get("/users/@me", access_token)


async def fetch_user_guilds(access_token: str) -> list[dict]:
    return await _discord_get("/users/@me/guilds", access_token)


#  Request-level user resolution


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """
    Resolves the authenticated user from the Bearer JWT.
    Returns a dict with ``user_id`` and ``discord_access_token``.
    Raises 401 if missing or invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_jwt(credentials.credentials)
    user_id = int(payload["sub"])

    session = await get_session(user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found — please re-authenticate",
        )

    # Transparently check if Discord token needs refreshing
    if int(time.time()) >= session["discord_token_expires_at"] - 300:
        session = await _refresh_discord_token(session)

    return {
        "user_id": user_id,
        "discord_access_token": session["discord_access_token"],
    }


async def _refresh_discord_token(session: dict) -> dict:
    """Exchange a refresh token for a new Discord access token."""
    async with aiohttp.ClientSession() as http:
        async with http.post(
            "https://discord.com/api/v10/oauth2/token",
            data={
                "client_id": os.environ["DISCORD_CLIENT_ID"],
                "client_secret": os.environ["DISCORD_CLIENT_SECRET"],
                "grant_type": "refresh_token",
                "refresh_token": session["discord_refresh_token"],
            },
        ) as resp:
            if not resp.ok:
                await revoke_session(session["user_id"])
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not refresh Discord token — please re-authenticate",
                )
            data = await resp.json()

    await store_session(
        user_id=session["user_id"],
        discord_access_token=data["access_token"],
        discord_refresh_token=data["refresh_token"],
        expires_in=data["expires_in"],
    )
    return {**session, "discord_access_token": data["access_token"]}


#  Authentication class (decorator API)


class Authentication:
    """
    Discord-style permission decorators for FastAPI route handlers.

    Usage::

        authentication = Authentication()

        @router.get("/settings")
        @authentication.require_permission(manage_guild=True)
        async def get_settings(guild: int, user=Depends(get_current_user)):
            ...

        @router.delete("/nuke")
        @authentication.is_server_owner()
        async def nuke(guild: int, user=Depends(get_current_user)):
            ...

    Both decorators expect the route to have:
      - A ``guild`` query/path parameter (int guild ID)
      - A ``user`` dependency resolved by ``get_current_user``
    """

    #  internal helpers

    @staticmethod
    async def _get_guild_member_permissions(
        guild_id: int,
        access_token: str,
    ) -> tuple[bool, int]:
        """
        Returns ``(is_owner, permission_bits)`` for the authenticated user in *guild_id*.
        Hits ``/users/@me/guilds`` which the ``guilds`` OAuth scope provides.
        """
        guilds: list[dict] = await fetch_user_guilds(access_token)

        for g in guilds:
            if int(g["id"]) == guild_id:
                return g.get("owner", False), int(g.get("permissions", 0))

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of that guild",
        )

    @staticmethod
    def _has_permissions(permission_bits: int, **required: bool) -> bool:
        """
        Returns True if *permission_bits* satisfies all *required* flags.
        ``administrator`` always passes.
        """
        if permission_bits & PERMISSION_FLAGS["administrator"]:
            return True

        for flag, needed in required.items():
            if not needed:
                continue
            bit = PERMISSION_FLAGS.get(flag)
            if bit is None:
                raise ValueError(f"Unknown permission flag: {flag!r}")
            if not (permission_bits & bit):
                return False
        return True

    #  public decorators

    def is_server_owner(self) -> Callable:
        """
        Requires the authenticated user to be the owner of the target guild.

        The decorated route **must** accept ``guild: int`` and
        ``user: dict = Depends(get_current_user)``.
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                guild_id: Optional[int] = kwargs.get("guild")
                user: Optional[dict] = kwargs.get("user")

                if guild_id is None or user is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Route is missing `guild` or `user` parameter",
                    )

                is_owner, _ = await self._get_guild_member_permissions(
                    guild_id,
                    user["discord_access_token"],
                )

                if not is_owner:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You must be the server owner to perform this action",
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def require_permission(self, **permissions: bool) -> Callable:
        """
        Requires the authenticated user to hold the specified Discord permission(s).

        Supported flags (pass as keyword args set to True):
            administrator, manage_guild, manage_roles, manage_channels,
            manage_messages, kick_members, ban_members, moderate_members,
            manage_webhooks, manage_nicknames, view_audit_log

        Example::

            @authentication.require_permission(manage_guild=True, ban_members=True)
            async def some_route(guild: int, user=Depends(get_current_user)): ...
        """
        unknown = set(permissions) - set(PERMISSION_FLAGS)
        if unknown:
            raise ValueError(f"Unknown permission flags: {unknown}")

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                guild_id: Optional[int] = kwargs.get("guild")
                user: Optional[dict] = kwargs.get("user")

                if guild_id is None or user is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Route is missing `guild` or `user` parameter",
                    )

                is_owner, bits = await self._get_guild_member_permissions(
                    guild_id,
                    user["discord_access_token"],
                )

                # owners bypass all permission checks
                if not is_owner and not self._has_permissions(bits, **permissions):
                    missing = [
                        flag
                        for flag, needed in permissions.items()
                        if needed
                        and not (bits & PERMISSION_FLAGS[flag])
                        and not (bits & PERMISSION_FLAGS["administrator"])
                    ]
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing permission(s): {', '.join(missing)}",
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def bot_only(self) -> Callable:
        """
        Restricts a route to requests authenticated with the bot's internal API key.
        Set BOT_API_KEY in your .env — used for bot <-> API communication.
        """
        _bot_key = os.environ.get("BOT_API_KEY", "")

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request: Optional[Request] = kwargs.get("request")
                key = (request.headers.get("X-Bot-Key") if request else None) or ""
                if not _bot_key or key != _bot_key:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Bot-only endpoint",
                    )
                return await func(*args, **kwargs)

            return wrapper

        return decorator


#  module-level singleton

authentication = Authentication()
