from typing import Optional

from discord.ext import commands
from datetime import datetime, timedelta, timezone

import discord

from bot import Bot
from helpers.context import Context
from helpers.converters import Duration
from helpers.converters import Modules

from .models import Punishment


ACTIONS = {
    Punishment.KICK: "kicked",
    Punishment.BAN: "banned",
    Punishment.TIMEOUT: "timed out",
    Punishment.STRIP: "stripped of roles",
    Punishment.STRIPSTAFF: "stripped of staff roles",
}

MODULES = {
    Modules.BAN: "bans",
    Modules.KICK: "kicks",
    Modules.VANITY: "changes the vanity URL",
    Modules.BOTADD: "adds bots",
    Modules.ROLES: "creates or deletes roles",
    Modules.CHANNELS: "creates or deletes channels",
    Modules.EMOJIS: "deletes emojis",
    Modules.WEBHOOKS: "creates webhooks",
}


class Flags(commands.FlagConverter, prefix="--", delimiter=" "):
    threshold: Optional[str] = commands.flag(default="3")
    do: Optional[Punishment] = commands.flag(default=Punishment.KICK, description="Action to take")


class Antinuke(commands.Cog):
    """
    Nuke protection
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.db


    @commands.group(
        name="antinuke", 
        aliases=["an"], 
        invoke_without_command=True
    )
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def antinuke(
        self,
        context: Context,
        modules: Optional[Modules] = None,
        *,
        flags: Optional[Flags] = None
    ) -> discord.Message:
        """
        Manage the nuke protection
        """
        if not modules:
            return await context.send_help()

        await self.db.execute(
            """
            INSERT INTO antinuke (
                guild_id,
                module,
                threshold,
                punishment
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, module) DO UPDATE SET
                threshold=excluded.threshold,
                punishment=excluded.punishment
            """, (
                context.guild.id,
                modules.value,
                flags.threshold,
                flags.do
            )
        )
        
        action = ACTIONS.get(flags.do, flags.do.value)
        module_action = MODULES.get(modules, modules.value)
        threshold_int = int(flags.threshold)
        
        return await context.send(
            "anyone who **" + module_action + "** " + 
            (str(threshold_int) + " or more " if threshold_int > 1 else "") +
            ("times" if modules not in [Modules.VANITY, Modules.BOTADD] and threshold_int > 1 else "") +
            (" " if modules not in [Modules.VANITY, Modules.BOTADD] and threshold_int > 1 else "") +
            "will be **" + action + "**"
        )


async def setup(bot: Bot):
    await bot.add_cog(Antinuke(bot))