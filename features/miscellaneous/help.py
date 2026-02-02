from typing import Optional
from discord.ext import commands

import discord
import config

from bot import Bot
from helpers.context import Context


class Help(commands.Cog):
    """
    Help commands
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="help")
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def help_command(self, context: Context, command_name: Optional[str] = None) -> discord.Message:
        """
        Display the help menu
        """
        prefix = config.Settings.default_prefix
        if context.guild:
            prefix = await self.bot.db.fetchone(
                """
                SELECT prefix 
                FROM prefixes 
                WHERE guild_id = ?
                """,
                (
                    context.guild.id,
                ),
            )
            if prefix:
                prefix = prefix[0]

        if not command_name:
            return await context.send(f"command/category is a required argument\n-# for more information, visit {config.Settings.help}")

        command = self.bot.get_command(command_name)
        return await context.send_help(prefix, command)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Help(bot))