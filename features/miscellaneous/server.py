from typing import Optional
from discord.ext import commands

import discord

from bot import Bot
from helpers.context import Context
from helpers.converters import Member
from helpers.converters.role import Role


class RoleFlags(commands.FlagConverter, prefix="--", delimiter=" "):
    name: str = commands.flag(description="Role name")
    color: Optional[discord.Color] = commands.flag(default=None, description="Role color")
    hoist: Optional[bool] = commands.flag(default=False, description="Display role separately")
    mentionable: Optional[bool] = commands.flag(default=False, description="Allow role to be mentioned")
    icon: Optional[str] = commands.flag(default=None, description="Role icon emoji or URL")
    permissions: Optional[int] = commands.flag(default=0, description="Role permissions value")


class Server(commands.Cog):
    """
    Server management commands
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot


    @commands.command(
        name="pic", 
        aliases=["picperms"]
    )
    @commands.cooldown(1, 4, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def pic(
        self, 
        context: Context, 
        member: Optional[Member] = None
    ) -> discord.Message:
        """
        Give or remove pic perms from a user
        """
        member = member or context.author

        first_channel = (
            context.guild.text_channels[0] if context.guild.text_channels else None
        )

        perms = first_channel.overwrites_for(member)
        currently_denied = perms.attach_files is False

        for channel in context.guild.text_channels:
            if currently_denied:
                await channel.set_permissions(
                    member,
                    attach_files=None,
                    embed_links=None,
                    reason=f"granted picture permissions by {context.author}",
                )
            else:
                await channel.set_permissions(
                    member,
                    attach_files=False,
                    embed_links=False,
                    reason=f"removed picture permissions by {context.author}",
                )

        if currently_denied:
            return await context.confirm(
                f"granted picture permissions to {member.mention} globally"
            )
        else:
            return await context.confirm(
                f"removed picture permissions from {member.mention} globally"
            )


    @commands.command(
        name="screenshare",
        aliases=["ss"]
    )
    @commands.cooldown(1, 4, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def screenshare(
        self, 
        context: Context, 
        member: Optional[Member] = None
    ) -> discord.Message:
        """
        Give or remove screenshare perms from a user
        """
        member = member or context.author

        first_channel = (
            context.guild.voice_channels[0] if context.guild.voice_channels else None
        )

        perms = first_channel.overwrites_for(member)
        currently_denied = perms.stream is False

        for channel in context.guild.voice_channels:
            if currently_denied:
                await channel.set_permissions(
                    member,
                    stream=None,
                    reason=f"granted screenshare permissions by {context.author}",
                )
            else:
                await channel.set_permissions(
                    member,
                    stream=False,
                    reason=f"removed screenshare permissions by {context.author}",
                )

        if currently_denied:
            return await context.confirm(
                f"granted screenshare permissions to {member.mention} globally"
            )
        else:
            return await context.confirm(
                f"removed screenshare permissions from {member.mention} globally"
            )


    @commands.group(
        name="role",
        invoke_without_command=True
    )
    @commands.has_permissions(manage_roles=True)
    async def role(
        self,
        context: Context,
    ) -> discord.Message:
        """
        Manage server roles
        """
        return await context.send_help()


    @role.command(
        name="create",
        aliases=["new"]
    )
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def role_create(
        self,
        context: Context,
        *,
        flags: RoleFlags,
    ) -> discord.Message:
        """
        Create a new role with customization options
        """
        role_kwargs = {
            "name": flags.name,
            "color": flags.color,
            "hoist": flags.hoist,
            "mentionable": flags.mentionable,
            "reason": f"Role created by {context.author}",
        }
        
        if flags.permissions:
            role_kwargs["permissions"] = discord.Permissions(flags.permissions)
        
        if flags.icon:
            role_kwargs["icon"] = flags.icon
        
        new_role = await context.guild.create_role(**role_kwargs)
        
        details = [f"name: **{new_role.name}**"]
        for attr, label in [("color", "color"), ("hoist", "hoisted"), ("mentionable", "mentionable")]:
            if getattr(flags, attr):
                details.append(f"{label}: **{getattr(flags, attr)}**")
        
        return await context.confirm(
            f"created new role with {', '.join(details)}"
        )


    @role.command(
        name="add",
        aliases=["assign", "give"]
    )
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def role_add(
        self,
        context: Context,
        member: Member,
        *, 
        role: Role
    ) -> discord.Message:
        """
        Assign a role to a member
        """
        await member.add_roles(
            role,
            reason=f"role assigned by {context.author}"
        )

        return await context.confirm(
            f"assigned role **{role.name}** to {member.mention}"
        )


    @role.command(
        name="remove",
        aliases=["take"]
    )
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def role_remove(
        self,
        context: Context,
        member: Member,
        *, 
        role: Role
    ) -> discord.Message:
        """
        Remove a role from a member
        """
        await member.remove_roles(
            role,
            reason=f"role removed by {context.author}"
        )

        return await context.confirm(
            f"removed role **{role.name}** from {member.mention}"
        )


    @role.command(
        name="delete",
        aliases=["del"]
    )
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def role_delete(
        self,
        context: Context,
        *, 
        role: Role
    ) -> discord.Message:
        """
        Delete a role from the server
        """
        await role.delete(
            reason=f"role deleted by {context.author}"
        )

        return await context.confirm(
            f"deleted role **{role.name}**"
        )


async def setup(bot: Bot) -> None:
    await bot.add_cog(Server(bot))
