"""
A helper file to aid with discord.py scripting. Using this requires you to have discord.py installed.
These Classes will not allow users to preform any major actions on your guilds, the most major being banning members.
Use these instead of passing raw discord.py models to your users, as these could be used to obtain sensitive materials,
such as your token, or to shut down your bot.
"""
from typing import Union, Optional

import discord
from discord import utils
from discord.ext import commands

from viper import VP_NONE, VP_ArgumentError, PyVP_Model

__all__ = [
    "SafeAccessTextChannel",
    "SafeAccessContext",
    "SafeAccessUser",
    "SafeAccessGuild",
    "SafeAccessMember",
    "SafeAccessMessage"
]


class SafeAccessContext(PyVP_Model):
    def __init__(self, ctx: commands.Context):
        self._ctx = ctx  # can't access underscored attrs, makes this safe
        self.message = SafeAccessMessage(ctx.message)
        self.author = SafeAccessMember(ctx.author) if ctx.guild else SafeAccessUser(ctx.author)
        self.channel = SafeAccessTextChannel(ctx.channel)
        self.guild = SafeAccessGuild(ctx.guild) if ctx.guild else VP_NONE
        self.bot = SafeAccessMember(ctx.me) if ctx.guild else SafeAccessUser(ctx.me)
        self.content = ctx.message.content

    def __repr__(self):
        return "<Context message={0}>".format(self.message)

    async def send(self, message: str, embed: discord.Embed = None) -> Optional["SafeAccessMessage"]:
        try:
            msg = await self._ctx.send(message, embed=embed)
            return SafeAccessMessage(msg)
        except discord.HTTPException:
            return VP_NONE


class SafeAccessMessage(PyVP_Model):
    def __init__(self, message: discord.Message):
        self._msg = message
        self.channel = SafeAccessTextChannel(message.channel)
        self.guild = SafeAccessGuild(message.guild) if message.guild else VP_NONE
        self.author = SafeAccessMember(message.author) if isinstance(message.author,
                                                                     discord.Member) else SafeAccessUser(message.author)
        self.content = message.content
        self.clean_content = message.clean_content
        self.flags = message.flags
        self.jump_url = message.jump_url

    def __repr__(self):
        return "<Message channel={0} guild={1} author={2}>".format(self.channel, self.guild, self.author)


class SafeAccessTextChannel(PyVP_Model):
    def __init__(self, channel: discord.TextChannel):
        self._chn = channel
        self.guild = SafeAccessGuild(channel.guild) if channel.guild else VP_NONE
        self.id = channel.id
        self.nsfw = channel.is_nsfw()
        self.news = channel.is_news()
        self.topic = channel.topic
        self.mention = channel.mention

    def __repr__(self):
        return "<Channel id={0} nsfw={1} guild={2}>".format(self.id, self.nsfw, self.guild)

    async def send(self, message: str, embed: discord.Embed = None) -> Optional[SafeAccessMessage]:
        try:
            msg = await self._chn.send(message, embed=embed)
            return SafeAccessMessage(msg)
        except discord.HTTPException:
            return VP_NONE


class SafeAccessMember(PyVP_Model):
    def __init__(self, member: discord.Member):
        self._mem = member
        self.name = member.name
        self.id = member.id
        self.discriminator = member.discriminator
        self.mention = member.mention
        self.guild = SafeAccessGuild(member.guild)
        self.nick = member.nick or VP_NONE

    def __repr__(self):
        return "<Member name={0} id={1} guild={2}>".format(self.name, self.id, self.guild)

    async def ban(self, reason=None):
        await self._mem.ban(reason=reason)
        return VP_NONE

    async def unban(self, reason=None):
        await self._mem.unban(reason=reason)
        return VP_NONE

    async def send_dm(self, message, embed: discord.Embed = None) -> Optional[SafeAccessMessage]:
        try:
            msg = await self._mem.send(message, embed=embed)
            return SafeAccessMessage(msg)
        except discord.HTTPException:
            return VP_NONE


class SafeAccessUser(PyVP_Model):
    def __init__(self, user: discord.User):
        self._usr = user
        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self.mention = user.mention

    def __repr__(self):
        return "<User name={0} id={1}>".format(self.name, self.id)

    async def send_dm(self, message, embed: discord.Embed = None) -> Optional[SafeAccessMessage]:
        try:
            msg = await self._usr.send(message, embed=embed)
            return SafeAccessMessage(msg)
        except discord.HTTPException:
            return VP_NONE

class SafeAccessGuild(PyVP_Model):
    def __init__(self, guild: discord.Guild):
        self._guild = guild
        self.member_count = guild.member_count
        self.owner = SafeAccessUser(guild.owner) # this needs to be a user to avoid recursion
        self.description = guild.description
        self.name = guild.name
        self.id = guild.id

    def __repr__(self):
        return "<Guild name={0} id={1} owner={2}>".format(self.name, self.id, self.owner)

    def get_member(self, id_or_name: Union[str, int]) -> Optional[SafeAccessMember]:
        if isinstance(id_or_name, int):
            member = self._guild.get_member(id_or_name)
            if member:
                return SafeAccessMember(member)

            return VP_NONE

        elif isinstance(id_or_name, str):
            member = self._guild.get_member_named(id_or_name)
            if member:
                return SafeAccessMember(member)

            return VP_NONE

        raise VP_ArgumentError("get_member expected a string or an integer, not {0!r}".format(id_or_name))

    def get_channel(self, id_or_name: Union[str, int]) -> Optional[SafeAccessTextChannel]:
        if isinstance(id_or_name, int):
            channel = self._guild.get_channel(id_or_name)
            if channel:
                return SafeAccessTextChannel(channel)

            return VP_NONE

        elif isinstance(id_or_name, str):
            channel = utils.get(self._guild.text_channels, name=id_or_name)
            if channel:
                return SafeAccessTextChannel(channel)

            return VP_NONE

        raise VP_ArgumentError("get_channel expected a string or an integer, not {0!r}".format(id_or_name))
