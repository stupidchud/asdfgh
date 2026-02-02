from typing import Optional
from discord.ext import commands

import discord

from bot import Bot
from helpers.converters.member import Member
from helpers.converters.duration import Duration
from helpers.context import Context


class Punishment(commands.Cog):
    """
    Moderation punishment commands
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.db

    @commands.command(
        name="ban",
        aliases=["banish"],
    )
    @commands.has_guild_permissions(ban_members=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def ban(
        self,
        context: Context,
        member: Member,
        *,
        reason: Optional[str] = "N/A",
    ) -> discord.Message:
        """
        Ban a member from the server
        """
        await context.guild.ban(member, reason=reason)
        return await context.punishment(punishment="ban", member=member)

    @commands.command(
        name="softban",
        aliases=["tempban"],
    )
    @commands.has_guild_permissions(ban_members=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def softban(
        self,
        context: Context,
        member: Member,
        duration: Duration,
        *,
        reason: Optional[str] = "N/A",
    ) -> discord.Message:
        """
        Temporarily ban a member from the server
        """
        await context.guild.ban(member, reason=reason)

        await self.db.execute(
            """
            INSERT INTO unbans (
                guild_id, 
                user_id, 
                unban_time
            )
            VALUES (?, ?, ?)
            """,
            (
                context.guild.id,
                member.id,
                duration.to_datetime().isoformat(),
            ),
        )

        return await context.punishment(
            punishment="tempban", member=member, until=duration
        )

    @commands.command(
        name="unban",
        aliases=["pardon"],
    )
    @commands.has_guild_permissions(ban_members=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def unban(
        self,
        context: Context,
        user: discord.User,
        reason: Optional[str] = "N/A",
    ) -> discord.Message:
        """
        Unban a member from the server
        """
        await context.guild.unban(user, reason=reason)

        is_scheduled = await self.db.fetchone(
            """
            SELECT id
            FROM unbans
            WHERE guild_id = ? 
            AND user_id = ?
            """,
            (
                context.guild.id,
                user.id,
            ),
        )

        if is_scheduled:
            await self.db.execute(
                """
                DELETE FROM unbans
                WHERE guild_id = ? 
                AND user_id = ?
                """,
                (
                    context.guild.id,
                    user.id,
                ),
            )

        return await context.punishment(punishment="unban", member=user)

    @commands.command(
        name="timeout",
        aliases=["mute"],
    )
    @commands.has_guild_permissions(moderate_members=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def timeout(
        self,
        context: Context,
        member: Member,
        *,
        duration: Duration = None,
    ) -> discord.Message:
        """
        Timeout a member from the server
        """
        if not duration:
            return await context.send("Please provide a duration for the timeout")

        await member.timeout(duration.to_datetime())
        return await context.punishment(
            punishment="timeout", member=member, until=duration
        )

    @commands.command(
        name="untimeout",
        aliases=["unmute"],
    )
    @commands.has_guild_permissions(moderate_members=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def untimeout(
        self,
        context: Context,
        member: Member,
        *,
        reason: Optional[str] = "N/A",
    ) -> discord.Message:
        """
        Remove timeout from a member
        """
        await member.timeout(None, reason=reason)
        return await context.punishment(punishment="untimeout", member=member)

    @commands.command(
        name="kick",
        aliases=["boot"],
    )
    @commands.has_guild_permissions(kick_members=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def kick(
        self,
        context: Context,
        member: Member,
        *,
        reason: Optional[str] = "N/A",
    ) -> discord.Message:
        """
        Kick a member from the server
        """
        await context.guild.kick(member, reason=reason)
        return await context.punishment(punishment="kick", member=member)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Punishment(bot))