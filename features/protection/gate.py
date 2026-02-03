from typing import Optional

from discord.ext import commands
from datetime import datetime, timedelta, timezone

import discord

from bot import Bot
from helpers.context import Context
from helpers.converters import Duration

from .models import Punishment


class Flags(commands.FlagConverter, prefix="--", delimiter=" "):
    age: Optional[str] = commands.flag(default=None, description="Account age")
    avatar: Optional[bool] = commands.flag(default=False, description="Check for default avatar")
    action: Optional[Punishment] = commands.flag(default=Punishment.KICK, description="Action to take")


class Gate(commands.Cog):
    """
    Join gate
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.db


    @commands.group(
        name="gate", 
        aliases=[
            "jg", 
            "joingate"
        ], 
        invoke_without_command=True
    )
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def gate(
        self,
        context: Context,
    ) -> discord.Message:
        """
        Manage the join gate
        """
        return await context.send_help()


    @gate.command(
        name="on", 
        aliases=["enable"]
    )
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def gate_on(self, context: Context, *, flags: Flags) -> discord.Message:
        """
        Enable the join gate
        """
        await self.db.execute(
            """
            INSERT INTO join_gate (guild_id, age, avatar, action)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (guild_id) 
            DO UPDATE SET 
                age = excluded.age,
                avatar = excluded.avatar,
                action = excluded.action
            """,
            (
                context.guild.id,
                flags.age,
                int(flags.avatar),
                flags.action.value if flags.action else None,
            )
        )

        return await context.confirm(
            f"join gate has been enabled"
            + (f" with age requirement: **{flags.age}**" if flags.age else "")
            + (f" and action: **{flags.action.value}**" if flags.action else "")
            + (
                f" and default avatar check: **enabled**"
                if flags.avatar
                else ""
            )
        )


    @gate.command(name="edit")
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def gate_edit(self, context: Context, *, flags: Flags) -> discord.Message:
        """
        Edit the join gate settings
        """
        existing = await self.db.fetchone(
            """
            SELECT *
            FROM join_gate 
            WHERE guild_id = ?
            """, 
            (context.guild.id,)
        )

        if not existing:
            return await context.error("join gate is not enabled")

        await self.db.execute(
            """
            UPDATE join_gate
            SET age = COALESCE(?, age),
                avatar = COALESCE(?, avatar),
                action = COALESCE(?, action)
            WHERE guild_id = ?
            """,
            (
                flags.age,
                int(flags.avatar) if flags.avatar is not None else None,
                flags.action.value if flags.action else None,
                context.guild.id,
            )
        )

        return await context.confirm(
            f"join gate has been enabled with age requirement: **{flags.age}**"
            + (f" and action: **{flags.action.value}**" if flags.action else "")
            + (
                f" and default avatar check: **{flags.avatar}**"
                if flags.avatar is not None
                else ""
            )
        )


    @gate.command(
        name="off", 
        aliases=["disable"]
    )
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def gate_off(self, context: Context) -> discord.Message:
        """
        Disable the join gate
        """
        await self.db.execute(
            """
            DELETE FROM join_gate 
            WHERE guild_id = ?
            """,
            (context.guild.id,)
        )

        return await context.confirm("join gate has been disabled")


    @gate.command(
        name="config",
        aliases=["settings"]
    )
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def gate_config(self, context: Context) -> discord.Message:
        """
        View the join gate settings
        """
        settings = await self.db.fetchone(
            """
            SELECT age, avatar, action
            FROM join_gate 
            WHERE guild_id = ?
            """,
            (context.guild.id,)
        )

        if not settings:
            return await context.error("join gate is not enabled")

        age_requirement, avatar_check, action = settings
        try:
            action = Punishment(action) if action else Punishment.KICK
        except (ValueError, KeyError):
            action = Punishment.KICK

        conditions = []
        if age_requirement:
            conditions.append(f"account age below **{age_requirement}**")
        if avatar_check:
            conditions.append("**no avatar**")

        action_text = {
            Punishment.BAN: "banned",
            Punishment.KICK: "kicked",
            Punishment.MUTE: "muted",
            Punishment.TIMEOUT: "timed out"
        }.get(action, "kicked")

        return await context.send(
            f"users with {' or '.join(conditions)} will be **{action_text}**"
            if conditions
            else "No restrictions configured"
        )


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        settings = await self.db.fetchone(
            """
            SELECT age, avatar, action
            FROM join_gate 
            WHERE guild_id = ?
            """,
            (member.guild.id,)
        )

        if not settings:
            return

        age_requirement, avatar_check, action = settings
        action = Punishment(action) if action else Punishment.KICK

        reason = None

        if age_requirement:
            try:                
                duration = Duration.parse_to_timedelta(age_requirement)
                min_account_age = datetime.now(timezone.utc) - duration
                
                if member.created_at > min_account_age:
                    reason = f"join gate: Account must be older than {age_requirement}"
            except Exception:
                pass

        if not reason and avatar_check and member.avatar is None:
            reason = "join gate: Default avatar not allowed"

        if reason:
            actions = {
                Punishment.BAN: lambda: member.ban(reason=reason),
                Punishment.MUTE: lambda: member.timeout(timedelta(days=28), reason=reason),
                Punishment.TIMEOUT: lambda: member.timeout(timedelta(days=28), reason=reason),
                Punishment.KICK: lambda: member.kick(reason=reason),
            }
            action_func = actions.get(action, actions[Punishment.KICK])
            await action_func()


async def setup(bot: Bot) -> None:
    await bot.add_cog(Gate(bot))
