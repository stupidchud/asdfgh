from discord.ext import commands

import discord
import config

from bot import Bot
from helpers.context import Context


class Prefix(commands.Cog):
    """
    Prefix management commands
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.db

    @commands.group(name="prefix", aliases=["pre"], invoke_without_command=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def prefix(self, context: Context) -> discord.Message:
        """
        View the current server prefix
        """
        if not context.guild:
            return await context.send(
                f"my default prefix is `{config.Settings.default_prefix}`"
            )

        result = await self.db.fetchone(
            """
            SELECT prefix 
            FROM prefixes 
            WHERE guild_id = ?
            """,
            (context.guild.id,),
        )

        return await context.send(
            f"my current prefix is `{result[0] if result else config.Settings.default_prefix}`"
        )

    @prefix.command(name="set", aliases=["change", "update", "edit"])
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def set(self, context: Context, new_prefix: str) -> discord.Message:
        """
        Set a custom prefix for the server
        """
        result = await self.db.fetchone(
            """
            SELECT prefix 
            FROM prefixes 
            WHERE guild_id = ?
            """,
            (context.guild.id,),
        )

        if result:
            await self.db.execute(
                """
                UPDATE prefixes 
                SET prefix = ?
                WHERE guild_id = ?
                """,
                (new_prefix, context.guild.id),
            )
        else:
            await self.db.execute(
                """
                INSERT INTO prefixes (
                    guild_id, 
                    prefix
                )
                VALUES (?, ?)
                """,
                (context.guild.id, new_prefix),
            )
        return await context.send(
            f"prefix for **{context.guild.name}** has been set to `{new_prefix}`"
        )

    @prefix.command(name="reset", aliases=["default", "remove", "delete"])
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def reset(self, context: Context) -> discord.Message:
        """
        Reset the prefix to the default
        """
        result = await self.db.fetchone(
            """
            SELECT prefix 
            FROM prefixes 
            WHERE guild_id = ?
            """,
            (context.guild.id,),
        )

        if not result:
            return await context.warn(
                message=f"this server is already using the default prefix `{config.Settings.default_prefix}`"
            )

        await self.db.execute(
            """
            DELETE FROM prefixes 
            WHERE guild_id = ?
            """,
            (context.guild.id,),
        )

        return await context.send(
            f"prefix for **{context.guild.name}** has been reset to `{config.Settings.default_prefix}`"
        )


async def setup(bot: Bot) -> None:
    await bot.add_cog(Prefix(bot))
