from typing import Optional

from collections import defaultdict
from datetime import timedelta
from time import monotonic

import discord

from discord.ext import commands, tasks

from bot import Bot
from helpers.context import Context
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
    do: Optional[Punishment] = commands.flag(
        default=Punishment.KICK, description="Action to take"
    )


class InfractionTracker:
    """
    Rolling-window infraction tracker using monotonic time.

    Each (guild_id, module) key maps to a list of monotonic timestamps.
    Entries older than the configured window are pruned on every read.
    """

    __slots__ = ("_window", "_store")

    def __init__(self, window: timedelta = timedelta(minutes=10)):
        self._window: float = window.total_seconds()
        self._store: dict[tuple[int, str], list[float]] = defaultdict(list)

    def _prune(self, key: tuple[int, str]) -> list[float]:
        cutoff = monotonic() - self._window
        entries = self._store[key]
        entries[:] = [ts for ts in entries if ts > cutoff]
        return entries

    def record(self, guild_id: int, module: str) -> int:
        """
        Record an infraction and return the current count
        within the rolling window.
        """
        key = (guild_id, module)
        entries = self._prune(key)
        entries.append(monotonic())
        return len(entries)

    def reset(self, guild_id: int, module: str) -> None:
        """
        Clear all infractions for a key after a punishment fires.
        """
        self._store.pop((guild_id, module), None)

    def purge_stale(self) -> int:
        """
        Remove all keys whose entries have fully expired.
        Returns the number of keys removed.
        """
        stale = [key for key in list(self._store) if not self._prune(key)]
        for key in stale:
            del self._store[key]
        return len(stale)

    def clear(self) -> None:
        self._store.clear()


class Antinuke(commands.Cog):
    """
    Nuke protection
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.db
        self.tracker = InfractionTracker(window=timedelta(minutes=10))
        self.purge_loop.start()

    def cog_unload(self):
        self.purge_loop.cancel()
        self.tracker.clear()

    @tasks.loop(minutes=5)
    async def purge_loop(self):
        self.tracker.purge_stale()

    @purge_loop.before_loop
    async def before_purge_loop(self):
        await self.bot.wait_until_ready()

    #
    # Commands
    #

    @commands.group(
        name="antinuke",
        aliases=["an"],
        invoke_without_command=True,
    )
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def antinuke(
        self,
        context: Context,
        modules: Optional[Modules] = None,
        enabled: Optional[str] = "on",
        *,
        flags: Optional[Flags] = None,
    ) -> discord.Message:
        """
        Manage the nuke protection
        """
        if not modules:
            return await context.send_help()

        if enabled == "off":
            await self.db.execute(
                """
                DELETE FROM antinuke
                WHERE guild_id = ?
                AND module = ?
                """,
                (context.guild.id, modules.value),
            )
            self.tracker.reset(context.guild.id, modules.value)
            return await context.send(
                "turned off protection for **"
                + MODULES.get(modules, modules.value)
                + "**"
            )

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
            """,
            (
                context.guild.id,
                modules.value,
                flags.threshold,
                flags.do,
            ),
        )

        action = ACTIONS.get(flags.do, flags.do.value)
        module_action = MODULES.get(modules, modules.value)
        threshold_int = int(flags.threshold)

        return await context.send(
            "anyone who **"
            + module_action
            + "** "
            + (str(threshold_int) + " or more " if threshold_int > 1 else "")
            + (
                "times"
                if modules not in [Modules.VANITY, Modules.BOTADD] and threshold_int > 1
                else ""
            )
            + (
                " "
                if modules not in [Modules.VANITY, Modules.BOTADD] and threshold_int > 1
                else ""
            )
            + "will be **"
            + action
            + "**"
        )

    @antinuke.command(
        name="config",
        aliases=["settings"],
    )
    @commands.has_guild_permissions(administrator=True)
    async def antinuke_config(self, context: Context) -> discord.Message:
        """
        View current antinuke configuration
        """
        rows = await self.db.fetchall(
            """
            SELECT module, threshold, punishment
            FROM antinuke
            WHERE guild_id = ?
            """,
            (context.guild.id,),
        )

        if not rows:
            return await context.send("you don't have any antinuke modules enabled yet")

        active_modules = []
        enabled_names = []
        for row in rows:
            module_name = row[0]
            threshold = row[1]
            punishment = row[2]

            readable_module = next(
                (v for k, v in MODULES.items() if k.value == module_name), module_name
            )
            readable_action = next(
                (v for k, v in ACTIONS.items() if k.value == punishment), punishment
            )

            display_short = readable_module.replace(
                "changes the vanity URL", "vanity"
            ).replace("adds bots", "bot additions")
            enabled_names.append(display_short)

            active_modules.append(
                {
                    "name": module_name,
                    "display": readable_module,
                    "display_short": display_short,
                    "threshold": threshold,
                    "action": readable_action,
                }
            )

        enabled_values = [row[0] for row in rows]
        disabled_modules = []

        for module_enum in Modules:
            if module_enum.value not in enabled_values:
                readable = MODULES.get(module_enum, module_enum.value)
                short = readable.replace("changes the vanity URL", "vanity").replace(
                    "adds bots", "bot additions"
                )
                disabled_modules.append(short)

        enabled_list = (
            ", ".join(enabled_names[:-1])
            + (" & " if len(enabled_names) > 1 else "")
            + (enabled_names[-1] if enabled_names else "")
        )

        overview = (
            f"the **{enabled_list}** module"
            f"{'s are' if len(enabled_names) != 1 else ' is'} **enabled**"
        )

        if disabled_modules:
            disabled_list = (
                ", ".join(disabled_modules[:-1])
                + (" & " if len(disabled_modules) > 1 else "")
                + (disabled_modules[-1] if disabled_modules else "")
            )
            overview += (
                f", and **{disabled_list}** "
                f"{'are' if len(disabled_modules) != 1 else 'is'} disabled"
            )

        select = discord.ui.Select(
            placeholder="select a module to view details",
            options=[
                discord.SelectOption(
                    label=mod["display_short"][:100],
                    value=mod["name"],
                    description=f"threshold: {mod['threshold']} → {mod['action']}"[
                        :100
                    ],
                )
                for mod in active_modules[:25]
            ],
        )

        async def select_callback(interaction: discord.Interaction):
            if interaction.user.id != context.author.id:
                return await interaction.response.send_message(
                    "this isn't for you", ephemeral=True
                )

            selected = next(
                (m for m in active_modules if m["name"] == select.values[0]), None
            )
            if not selected:
                return await interaction.response.send_message(
                    "module not found", ephemeral=True
                )

            times_text = "times" if int(selected["threshold"]) > 1 else "time"
            await interaction.response.send_message(
                f"members who **{selected['display']}** "
                f"**{selected['threshold']}** or more {times_text} "
                f"will be **{selected['action']}**\n\n",
                ephemeral=True,
            )

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        return await context.send(overview, view=view)

    #
    # Listeners
    #

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.handle_infraction(channel.guild.id, Modules.CHANNELS)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self.handle_infraction(channel.guild.id, Modules.CHANNELS)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self.handle_infraction(role.guild.id, Modules.ROLES)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        await self.handle_infraction(role.guild.id, Modules.ROLES)

    #
    # Infraction handler
    #

    async def handle_infraction(self, guild_id: int, module: Modules):
        row = await self.db.fetchone(
            """
            SELECT threshold, punishment
            FROM antinuke
            WHERE guild_id = ? AND module = ?
            """,
            (guild_id, module.value),
        )

        if not row:
            return

        threshold = int(row[0])
        punishment = row[1]

        count = self.tracker.record(guild_id, module.value)

        if count < threshold:
            return

        self.tracker.reset(guild_id, module.value)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        async for entry in guild.audit_logs(limit=1):
            if entry.action not in (
                discord.AuditLogAction.channel_create,
                discord.AuditLogAction.channel_delete,
                discord.AuditLogAction.role_create,
                discord.AuditLogAction.role_delete,
            ):
                break

            perpetrator = entry.user
            if perpetrator == self.bot.user or perpetrator == guild.owner:
                return

            try:
                await self.punish(guild, perpetrator, punishment, module)
            except (discord.Forbidden, discord.HTTPException):
                # print(f"failed to punish {perpetrator} for {module.value} infraction in guild {guild_id}")
                pass
            break

    async def punish(
        self,
        guild: discord.Guild,
        member: discord.Member,
        punishment: str,
        module: Modules,
    ) -> None:
        reason = f"antinuke: exceeded {module.value} threshold"

        if punishment == Punishment.KICK.value:
            await guild.kick(member, reason=reason)

        elif punishment == Punishment.BAN.value:
            await guild.ban(member, reason=reason)

        elif punishment == Punishment.TIMEOUT.value:
            await member.timeout(timedelta(hours=1), reason=reason)

        elif punishment == Punishment.STRIP.value:
            roles = [r for r in member.roles if r != guild.default_role]
            if roles:
                await member.remove_roles(*roles, reason=reason)

        elif punishment == Punishment.STRIPSTAFF.value:
            staff = [
                r
                for r in member.roles
                if r.permissions.administrator or r.permissions.manage_guild
            ]
            if staff:
                await member.remove_roles(*staff, reason=reason)


async def setup(bot: Bot):
    await bot.add_cog(Antinuke(bot))
