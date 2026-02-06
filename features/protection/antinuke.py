from typing import Optional

from discord.ext import commands
from datetime import datetime, timedelta, timezone

import discord

from bot import Bot
from helpers.context import Context
from helpers.converters import Duration
from helpers.converters import Modules

from .models import Punishment


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
        aliases=[
            "an",
        ], 
        invoke_without_command=True
    )
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def antinuke(
        self,
        context: Context,
        modules: Modules,
        *,
        flags: Optional[Flags]
    ) -> discord.Message:
        """
        Manage the nuke protection
        """
        return await context.send_help()


async def setup(bot: Bot):
    await bot.add_cog(Antinuke(bot))