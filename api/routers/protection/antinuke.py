"""
api/routers/protection/antinuke.py
"""

from fastapi import APIRouter as Router, Depends

from helpers.database import Database
from features.protection.antinuke import Modules, Punishment
from api.middleware.auth import authentication, get_current_user

import dotenv

dotenv.load_dotenv()

router = Router(prefix="/protection/antinuke", tags=["Protection"])
db = Database(dotenv.get_key(dotenv.find_dotenv(), "DATABASE_URL"))


@router.get("/", summary="Check if AntiNuke is active", status_code=200)
def read_antinuke():
    return {"message": "active"}


@router.get("/{guild}", summary="Get antinuke settings for a guild", status_code=200)
@authentication.require_permission(manage_guild=True)
async def get_antinuke(guild: int, user: dict = Depends(get_current_user)):
    result = await db.fetchall(
        """
        SELECT module, punishment, threshold, enabled
        FROM antinuke
        WHERE guild_id = ?
        """,
        (guild,),
    )

    if not result:
        return {"message": f"No antinuke settings found for guild {guild}"}

    return {
        "guild_id": guild,
        "modules": [
            {
                "module":     row["module"],
                "punishment": row["punishment"],
                "threshold":  row["threshold"],
                "enabled":    row["enabled"],
            }
            for row in result
        ],
    }


@router.post("/{guild}", summary="Activate a module for a guild", status_code=200)
@authentication.require_permission(manage_guild=True)
async def activate_antinuke(
    guild: int,
    module: Modules,
    punishment: Punishment,
    threshold: str = "3",
    user: dict = Depends(get_current_user),
):
    await db.execute(
        """
        INSERT INTO antinuke (guild_id, module, punishment, threshold, enabled)
        VALUES (?, ?, ?, ?, 1)
        ON CONFLICT (guild_id, module) DO UPDATE SET
            punishment  = excluded.punishment,
            threshold   = excluded.threshold,
            enabled     = 1,
            updated_at  = CURRENT_TIMESTAMP
        """,
        (guild, module.value, punishment.value, threshold),
    )

    return {
        "message": (
            f"Antinuke activated for guild {guild}, module {module.value}, "
            f"punishment {punishment.value}, threshold {threshold}"
        )
    }


@router.put("/{guild}", summary="Update punishment/threshold for a module", status_code=200)
@authentication.require_permission(manage_guild=True)
async def update_antinuke(
    guild: int,
    module: Modules,
    punishment: Punishment,
    threshold: str = "3",
    user: dict = Depends(get_current_user),
):
    await db.execute(
        """
        UPDATE antinuke
        SET punishment = ?, threshold = ?, updated_at = CURRENT_TIMESTAMP
        WHERE guild_id = ? AND module = ?
        """,
        (punishment.value, threshold, guild, module.value),
    )

    return {
        "message": (
            f"Antinuke updated for guild {guild}, module {module.value}, "
            f"punishment {punishment.value}, threshold {threshold}"
        )
    }


@router.delete("/{guild}", summary="Deactivate a module for a guild", status_code=200)
@authentication.is_server_owner()
async def deactivate_antinuke(
    guild: int,
    module: Modules,
    user: dict = Depends(get_current_user),
):
    """Deactivating a module is owner-only — more destructive than toggling settings."""
    await db.execute(
        """
        UPDATE antinuke
        SET enabled = 0, updated_at = CURRENT_TIMESTAMP
        WHERE guild_id = ? AND module = ?
        """,
        (guild, module.value),
    )

    return {"message": f"Antinuke deactivated for guild {guild}, module {module.value}"}