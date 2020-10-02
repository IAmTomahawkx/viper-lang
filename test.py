# run tests to check coverage
import os
import asyncio

import discord as dpy

import viper
from viper.exts import discord

basic_test = os.path.join("tests", "test_script.vp")
discordpy_test = os.path.join("tests", "discordpy_script_test.vp")

loop = asyncio.get_event_loop()

loop.run_until_complete(viper.eval_file(basic_test)) # run the basic script

class MockDpyObject:
    def __init__(self, **kwargs):
        for name, item in kwargs.items():
            setattr(self, name, item)

class MockDpyContext:
    def __init__(self):
        def error(*args, **kwargs):
            raise dpy.HTTPException(MockDpyObject(status=400, reason="No"), "no")
        self.send = error
        self.author = usr = MockDpyObject(
                name="Danny",
                nick=None,
                discriminator="0007",
                id=123456,
                send=error,
                mention="<@!123456>"
            )
        self.me = MockDpyObject(
                name="OAuth2 Sucks",
                nick=None,
                discriminator="3136",
                id=168930860739985410,
                send=error,
                mention="<@!168930860739985410>"
            )
        self.guild = guild = MockDpyObject(
            name="Discord.py",
            member_count=123,
            description="Discord.py Guild",
            id=336642139381301249,
            owner=usr,
            get_member = lambda i: None,
            get_member_name = lambda n: None
        )
        self.author.guild = guild
        self.me.guild = guild
        self.channel = channel = MockDpyObject(
            id=336642776609456130,
            name="General",
            guild=guild,
            is_nsfw=lambda: False,
            is_news=lambda: False,
            mention="<#336642776609456130>",
            topic="Ahhh",
            send=error
        )
        self.guild.text_channels = [channel]
        self.guild.get_channel = lambda i: channel

        self.message = MockDpyObject(
            content="Hi there",
            guild=guild,
            channel=channel,
            clean_content="Hi there",
            flags=None,
            jump_url="discord.com/url",
            author=usr
        )

ns = viper.VPNamespace()
ns['ctx'] = discord.SafeAccessContext(MockDpyContext()) # noqa

loop.run_until_complete(viper.eval_file(discordpy_test, namespace=ns, safe=True)) # run the discord ext script