from typing import Optional, Union
from discord.ext import commands

import discord
import config

from bot import Bot
from helpers.context import Context


class Information(commands.Cog):
    """
    Information related commands
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(name="invite", aliases=["inv"], invoke_without_command=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def invite(self, context: Context) -> discord.Message:
        """
        Get the bot's invite link
        """
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=discord.Permissions(permissions=8),
            scopes=("bot", "applications.commands"),
        )

        return await context.send(f"[invite me!]({invite_url})")

    @invite.command(name="info", aliases=["ii"])
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def inviteinfo(
        self, context: Context, invite: discord.Invite
    ) -> discord.Message:
        """
        Get information about an invite
        """
        return await context.send(
            embed=discord.Embed(title=invite.guild.name, color=config.Color.default)
            .add_field(name="Channel", value=invite.channel.name, inline=False)
            .add_field(
                name="Inviter",
                value=str(invite.inviter) if invite.inviter else "Unknown",
                inline=False,
            )
            .add_field(
                name="Members", value=invite.approximate_member_count, inline=False
            )
            .add_field(
                name="Expires At",
                value=str(invite.expires_at) if invite.expires_at else "Never",
                inline=False,
            )
            .set_footer(
                text=f"Requested by {context.author}",
                icon_url=context.author.display_avatar.url,
            )
            .set_thumbnail(url=invite.guild.icon.url if invite.guild.icon else None)
        )

    @commands.command(
        name="userinfo",
        aliases=["ui", "whois", "discord"],
    )
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def userinfo(
        self,
        context: commands.Context,
        user: Optional[Union[discord.User, discord.Member]] = None,
    ) -> discord.Message:
        """
        Display the users information
        """
        user = user or context.author

        if isinstance(user, discord.User) and context.guild:
            member = context.guild.get_member(user.id)
            if member:
                user = member

        author_name = (
            f"{user.global_name} (@{user.name})"
            if user.global_name
            else f"@{user.name}"
        )

        buttons = discord.ui.View()
        buttons.add_item(
            discord.ui.Button(
                label="Avatar URL",
                url=user.display_avatar.url,
                style=discord.ButtonStyle.gray,
            )
        )

        if user.banner:
            buttons.add_item(
                discord.ui.Button(
                    label="Banner URL",
                    url=user.banner.url,
                    style=discord.ButtonStyle.gray,
                )
            )

        return await context.send(
            embed=discord.Embed(
                description="".join(
                    [
                        (
                            " ".join(
                                config.Emoji.Badges.emojis[flag]
                                for flag, value in user.public_flags
                                if value and flag in config.Emoji.Badges.emojis
                            )
                            + "\n\n"
                            if any(
                                value and flag in config.Emoji.Badges.emojis
                                for flag, value in user.public_flags
                            )
                            else ""
                        ),
                        (
                            f"{config.Emoji.spotify} Listening to [{spotify.title}](https://open.spotify.com/track/{spotify.track_id}) by **{spotify.artist}**\n"
                            if (
                                spotify := (
                                    discord.utils.find(
                                        lambda a: isinstance(a, discord.Spotify),
                                        user.activities,
                                    )
                                    if isinstance(user, discord.Member)
                                    else None
                                )
                            )
                            else ""
                        ),
                        (
                            f"🔊 Currently in {user.voice.channel.mention}"
                            + (
                                f" with {len(user.voice.channel.members) - 1} other {'person' if len(user.voice.channel.members) - 1 == 1 else 'people'}"
                                if len(user.voice.channel.members) - 1 > 0
                                else " by themselves"
                            )
                            + "\n"
                            if isinstance(user, discord.Member)
                            and user.voice
                            and user.voice.channel
                            else ""
                        ),
                        (
                            f"⏲️ Is timed out until {discord.utils.format_dt(user.timed_out_until, style='F')}\n"
                            if isinstance(user, discord.Member) and user.timed_out_until
                            else ""
                        ),
                        (
                            "\n"
                            if isinstance(user, discord.Member)
                            and (
                                discord.utils.find(
                                    lambda a: isinstance(a, discord.Spotify),
                                    user.activities,
                                )
                                or (user.voice and user.voice.channel)
                                or user.timed_out_until
                            )
                            else ""
                        ),
                        (
                            "**Dates**\n"
                            if isinstance(user, discord.Member)
                            else "**Dates**\n"
                        ),
                        (
                            f"Created: {discord.utils.format_dt(user.created_at, style='R')}\n"
                            if isinstance(user, discord.Member)
                            else f"Created: {discord.utils.format_dt(user.created_at, style='R')}"
                        ),
                        (
                            f"Joined: {discord.utils.format_dt(user.joined_at, style='R')}"
                            if isinstance(user, discord.Member)
                            else ""
                        ),
                        (
                            f"\nBoosted: {discord.utils.format_dt(user.premium_since, style='F')} ({discord.utils.format_dt(user.premium_since, style='R')})"
                            if isinstance(user, discord.Member) and user.premium_since
                            else ""
                        ),
                        (
                            f"\n\n**Roles ({len(user.roles) - 1})**\n{' '.join(role.mention for role in user.roles[1:])}"
                            if isinstance(user, discord.Member) and len(user.roles) > 1
                            else ""
                        ),
                        (
                            f"\n\n**Key Permissions**\n{', '.join([perm.replace('_', ' ').title() for perm, value in user.guild_permissions if value][:5])}"
                            + (
                                f" ... ({len([perm for perm, value in user.guild_permissions if value]) - 5} more)"
                                if len(
                                    [
                                        perm
                                        for perm, value in user.guild_permissions
                                        if value
                                    ]
                                )
                                > 5
                                else ""
                            )
                            if isinstance(user, discord.Member)
                            and any(value for _, value in user.guild_permissions)
                            else ""
                        ),
                    ]
                ),
                color=config.Color.default,
            )
            .set_author(name=author_name, icon_url=user.display_avatar.url)
            .set_thumbnail(url=user.display_avatar.url),
            view=buttons,
        )

    @commands.command(
        name="avatar",
        aliases=["av"],
    )
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def avatar(
        self,
        context: commands.Context,
        user: Optional[Union[discord.User, discord.Member]],
    ) -> discord.Message:
        """
        Display the users avatar
        """
        user = user or context.author

        return await context.send(
            embed=discord.Embed(
                title=user.display_name, color=config.Color.default
            ).set_image(url=user.display_avatar.url)
        )

    @commands.command(
        name="banner",
        aliases=["bnaner", "bannr"],
    )
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def banner(
        self,
        context: commands.Context,
        user: Optional[Union[discord.User, discord.Member]],
    ) -> discord.Message:
        """
        Display the users banner
        """
        user = user or context.author

        if user.banner:

            return await context.send(
                embed=discord.Embed(
                    title=user.display_name, color=config.Color.default
                ).set_image(url=user.banner.url)
            )

        else:
            return await context.reply(
                f"{user.mention} doesn't have a banner set",
                allowed_mentions=discord.AllowedMentions(users=False),
            )

    @commands.command(name="serverinfo", aliases=["si", "guildinfo", "gi"])
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def serverinfo(self, context: Context) -> discord.Message:
        """
        Display the server's information
        """
        guild = context.guild
        bots = sum(1 for m in guild.members if m.bot)
        humans = guild.member_count - bots

        embed = discord.Embed(color=config.Color.default)
        embed.set_author(
            name=guild.name, icon_url=guild.icon.url if guild.icon else None
        )

        if guild.description:
            embed.description = guild.description

        embed.add_field(
            name="Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=False,
        )
        embed.add_field(name="Server ID", value=f"{guild.id}", inline=False)
        embed.add_field(
            name="Created",
            value=discord.utils.format_dt(guild.created_at, style="R"),
            inline=False,
        )

        embed.add_field(
            name="Members",
            value=f"{guild.member_count:,} total\n{humans:,} humans\n{bots:,} bots",
            inline=False,
        )
        boost_info = (
            f"Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts"
        )
        if guild.premium_subscriber_role:
            boost_info += f"\n{len(guild.premium_subscribers)} boosters"

        embed.add_field(name="Boosts", value=boost_info, inline=False)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.set_footer(
            text=f"Requested by {context.author}",
            icon_url=context.author.display_avatar.url,
        )

        return await context.send(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Information(bot))
