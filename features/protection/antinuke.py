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
    do: Optional[Punishment] = commands.flag(
        default=Punishment.KICK, description="Action to take"
    )


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
            "an"
        ], 
        invoke_without_command=True
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
                (
                    context.guild.id, 
                    modules.value
                ),
            )
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
                flags.do
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
        aliases=[
            "settings"
        ]
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
            (
                context.guild.id,
            ),
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

            display_short = readable_module.replace("changes the vanity URL", "vanity").replace("adds bots", "bot additions")
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

        overview = f"the **{enabled_list}** module{'s are' if len(enabled_names) != 1 else ' is'} **enabled**"

        if disabled_modules:
            disabled_list = (
                ", ".join(disabled_modules[:-1])
                + (" & " if len(disabled_modules) > 1 else "")
                + (disabled_modules[-1] if disabled_modules else "")
            )
            overview += f", and **{disabled_list}** {'are' if len(disabled_modules) != 1 else 'is'} disabled"

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
                f"members who **{selected['display']}** **{selected['threshold']}** or more {times_text} will be **{selected['action']}**\n\n",
                ephemeral=True,
            )

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        return await context.send(overview, view=view)


async def setup(bot: Bot):
    await bot.add_cog(Antinuke(bot))
