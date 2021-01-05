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

import viper
from viper.objects import wraps_as_native

__all__ = [
    "SafeAccessTextChannel",
    "SafeAccessContext",
    "SafeAccessUser",
    "SafeAccessGuild",
    "SafeAccessMember",
    "SafeAccessMessage"
]


@wraps_as_native("A command context object")
class SafeAccessContext:
    def __init__(self, runner, ctx: commands.Context):
        self._runner = runner
        self._ctx = ctx  # can't access underscored attrs, makes this safe
        self.message = SafeAccessMessage(runner, ctx.message)
        self.author = SafeAccessMember(runner, ctx.author) if ctx.guild else SafeAccessUser(runner, ctx.author)
        self.channel = SafeAccessTextChannel(runner, ctx.channel)
        self.guild = SafeAccessGuild(runner, ctx.guild) if ctx.guild else runner.null
        self.bot = SafeAccessMember(runner, ctx.me) if ctx.guild else SafeAccessUser(runner, ctx.me)
        self.content = viper.String(ctx.message.content, -1, runner)

    def _cast(self, typ):
        if typ is viper.String:
            return viper.String("<Context message={0}>".format(self.message), -1, self._runner)
        return self._runner.null

    async def send(self, lineno, runner, message: viper.String) -> Optional["SafeAccessMessage"]:
        try:
            msg = await self._ctx.send(message._value)
            return SafeAccessMessage(self._runner, msg)
        except discord.HTTPException:
            return self._runner.null

@wraps_as_native("A Message")
class SafeAccessMessage:
    def __init__(self, runner, message: discord.Message):
        self._runner = runner
        self._msg = message
        self.channel = SafeAccessTextChannel(runner, message.channel)
        self.guild = SafeAccessGuild(runner, message.guild) if message.guild else runner.null
        self.author = SafeAccessMember(runner, message.author) if isinstance(message.author,
                                                                     discord.Member) else SafeAccessUser(runner, message.author)
        self.content = viper.String(message.content, -1, runner)
        self.clean_content = viper.String(message.clean_content, -1, runner)
        self.flags = message.flags
        self.jump_url = viper.String(message.jump_url, -1, runner)

    def _cast(self, typ, lineno):
        if typ is viper.String:
            return viper.String("<Message channel={0} guild={1} author={2}>".format(self.channel, self.guild, self.author), lineno, self._runner)

@wraps_as_native("A Channel")
class SafeAccessTextChannel:
    def __init__(self, runner, channel: discord.TextChannel):
        self._chn = channel
        self._runner = runner
        self.guild = SafeAccessGuild(runner, channel.guild) if channel.guild else runner.null
        self.id = viper.Integer(channel.id, -1, runner)
        self.nsfw = viper.Boolean(channel.is_nsfw(), -1, runner)
        self.news = viper.Boolean(channel.is_news(), -1, runner)
        self.topic = viper.String(channel.topic, -1, runner)
        self.mention = viper.String(channel.mention, -1, runner)

    def _cast(self, typ, lineno):
        if typ is viper.String:
            return viper.String("<Channel id={0} nsfw={1} guild={2}>".format(self.id._value, self.nsfw._value, self.guild), lineno, self._runner)
        return self._runner.null

    async def send(self, lineno, runner, message: viper.String) -> Optional[type(SafeAccessMessage)]:
        try:
            msg = await self._chn.send(message._value)
            return SafeAccessMessage(runner, msg)
        except discord.HTTPException:
            return runner.null

@wraps_as_native("A Member")
class SafeAccessMember:
    def __init__(self, runner, member: discord.Member, guild=None):
        self._mem = member
        self._runner = runner
        self.name = viper.String(member.name, -1, runner)
        self.id = viper.Integer(member.id, -1, runner)
        self.discriminator = viper.String(member.discriminator, -1, runner)
        self.mention = member.mention
        self.guild = guild or SafeAccessGuild(runner, member.guild)
        self.nick = viper.String(member.nick, -1, runner) if member.nick else runner.null

    def _cast(self, typ, lineno):
        if typ is viper.String:
            return viper.String("<Member name={0} id={1} guild={2}>".format(self.name._value, self.id._value, self.guild), lineno, self._runner)
        return self._runner.null

    async def ban(self, lineno, runner, reason: viper.String=None):
        await self._mem.ban(reason=reason._value if reason else None)
        return runner.null

    async def unban(self, lineno, runner, reason: viper.String=None):
        await self._mem.unban(reason=reason._value if reason else None)
        return runner.null

    async def send_dm(self, lineno, runner, message: viper.String) -> Optional[type(SafeAccessMessage)]:
        try:
            msg = await self._mem.send(message._value)
            return SafeAccessMessage(runner, msg)
        except discord.HTTPException:
            return runner.null

@wraps_as_native("A User")
class SafeAccessUser:
    def __init__(self, runner, user: discord.User):
        self._runner = runner
        self._usr = user
        self.name = viper.String(user.name, -1, runner)
        self.id = viper.Integer(user.id, -1, runner)
        self.discriminator = viper.String(user.discriminator, -1, runner)
        self.mention = viper.String(user.mention, -1, runner)

    def _cast(self, typ, lineno):
        if typ is viper.String:
            return viper.String("<User name={0} id={1}>".format(self.name, self.id), lineno, self._runner)
        return self._runner.null

    async def send_dm(self, lineno, runner, message) -> Optional[type(SafeAccessMessage)]:
        try:
            msg = await self._mem.send(message._value)
            return SafeAccessMessage(runner, msg)
        except discord.HTTPException:
            return runner.null

@wraps_as_native("A Guild")
class SafeAccessGuild:
    def __init__(self, runner, guild: discord.Guild):
        self._guild = guild
        self._runner = runner
        self.member_count = viper.Integer(guild.member_count, -1, runner)
        self.owner = SafeAccessMember(runner, guild.owner, self) if guild.owner else runner.null
        self.description = viper.String(guild.description, -1, runner)
        self.name = viper.String(guild.name, -1, runner)
        self.id = viper.Integer(guild.id, -1, runner)

    def _cast(self, typ, lineno):
        if typ is viper.String:
            return viper.String("<Guild name={0} id={1} owner={2}>".format(self.name, self.id, self.owner), lineno, self._runner)
        return self._runner.null

    def get_member(self, lineno, runner, id_or_name: Union[viper.String, viper.Integer]) -> Optional[type(SafeAccessMember)]:
        if isinstance(id_or_name, viper.Integer):
            member = self._guild.get_member(id_or_name._value)
            if member:
                return SafeAccessMember(self._runner, member)

            return self._runner.null

        elif isinstance(id_or_name, str):
            member = self._guild.get_member_named(id_or_name)
            if member:
                return SafeAccessMember(self._runner, member)

            return self._runner.null

        raise viper.ViperExecutionError(runner, lineno, "get_member expected a string or an integer, not {0!r}".format(id_or_name))

    def get_channel(self, lineno, runner, id_or_name: Union[viper.String, viper.Integer]) -> Optional[type(SafeAccessTextChannel)]:
        if isinstance(id_or_name, viper.Integer):
            channel = self._guild.get_channel(id_or_name._value)
            if channel:
                return SafeAccessTextChannel(runner, channel)

            return runner.null

        elif isinstance(id_or_name, viper.String):
            channel = utils.get(self._guild.text_channels, name=id_or_name._value)
            if channel:
                return SafeAccessTextChannel(runner, channel)

            return runner.null

        raise viper.ViperExecutionError(runner, lineno, "get_channel expected a string or an integer, not {0!r}".format(id_or_name))
