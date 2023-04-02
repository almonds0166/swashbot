from typing import Optional, Callable

from math import inf, isinf
import asyncio

import discord
from discord.ext import commands
from discord import app_commands

from main import Swashbot
from utils.memory import Settings

def _requires_manage_channel_and_manage_messages(perms: discord.Permissions, the_channel: str) -> Optional[str]:
   if perms.manage_channels and perms.manage_messages: return None # user can use this command

   if perms.manage_channels and not perms.manage_messages:
      return f"You don't have the **Manage Messages** permission for {the_channel}"
   elif perms.manage_messages and not perms.manage_channels:
      return f"You don't have the **Manage Channel** permission for {the_channel}"

   return f"You need both the **Manage Channel** and **Manage Messages** permissions for {the_channel} to use that command"

def _requires_manage_messages(perms: discord.Permissions, the_channel: str) -> Optional[str]:
   if perms.manage_messages: return None # user can use this command

   return f"You don't have the **Manage Messages** permission for {the_channel}"

def settings_status(settings: Settings) -> str:
   at_least = settings.at_least
   at_most = settings.at_most
   minutes = settings.minutes

   if isinf(at_least) or (isinf(at_most) and isinf(minutes)):
       return "No action taken."

   status = []
   if at_least == 0 and at_most == 0:
      status.append("Turbid! Delete all new messages immediately.")
      #status.append("Wait, doesn't that mean this message will get deleted in a split second?")
   elif at_least == 0:
      if not isinf(at_most):
         status.append(f"Immediately delete all messages past count {at_most}.")
         status.append(f"Everything else takes {minutes} minute{'s' if minutes != 1 else ''} to wash away.")
      else:
         status.append(f"Messages take {minutes} minute{'s' if minutes != 1 else ''} to wash away.")
   elif at_least == at_most and not isinf(at_most):
      status.append(f"Immediately delete all messages past count {at_most}.")
   else:
      status.append(f"Always keep the {at_least} most recent message{'s' if at_least != 1 else ''}.")

      if not isinf(at_most):
         status.append(f"Delete all messages past count {at_most}.")
         if not isinf(minutes):
            status.append(f"Any messages in-between take {minutes} minute{'s' if minutes != 1 else ''} to wash away.")
      else:
         status.append(f"Any other messages take {minutes} minute{'s' if minutes != 1 else ''} to wash away.")

   return "\n".join(status)

class FrontCog(commands.Cog):
   """Cog that handles the user commands
   """
   def __init__(self, client: Swashbot) -> None:
      self.client = client

   async def get_guild_id(self, channel: int) -> int:
      discord_channel = await self.client.try_channel(channel)
      guild = discord_channel.guild.id
      return guild

   async def check_flotsam(self, channel: int) -> None:
      # nothing to do
      if channel not in self.client.memo.channels:
         if channel in self.client.decks:
            del self.client.decks[channel]
         return

      # need to re-gather
      await self.client.gather_flotsam(channel)

   async def check_perms(self,
      ctx: commands.Context,
      channel: Optional[int],
      check: Callable[[discord.Permissions, str], Optional[str]],
   ) -> Optional[int]:
      """
      """
      if not isinstance(ctx.author, discord.Member): return
      the_channel = "this channel" if channel is None else ""

      if channel is None: channel = ctx.channel.id
      discord_channel = await self.client.try_channel(channel)
      guild = discord_channel.guild.id

      if not the_channel: the_channel = discord_channel.mention
      perms = discord_channel.permissions_for(ctx.author)

      error_msg = check(perms, the_channel)
      if error_msg:
         async with ctx.typing(): await asyncio.sleep(1)
         try:
            await ctx.reply(error_msg)
         except discord.NotFound:
            pass
         return None

      return guild

   @commands.hybrid_command(name="atleast", description="always keep the `m` most recent messages in the channel")
   async def slash_atleast(self, ctx: commands.Context, m: Optional[int]=None, channel: Optional[int]=None) -> None:
      guild = await self.check_perms(ctx, channel, _requires_manage_channel_and_manage_messages)
      if guild is None: return

      await ctx.message.add_reaction("⏲️")

      if channel is None: channel = ctx.channel.id
      guild = await self.get_guild_id(channel)
      settings = self.client.memo.load(channel)

      at_least = inf if m is None else max(0, m)
      # at_least parameter can bump up the at_most parameter
      at_most = max(settings.at_most, at_least)
      settings = settings.replace(at_least=at_least, at_most=at_most)

      self.client.memo.save(channel, guild, settings)
      await self.check_flotsam(channel)

      if ctx.message:
         try:
            if self.client.user is not None:
               await ctx.message.remove_reaction("⏲️", self.client.user)
            await ctx.message.add_reaction("👌")
         except discord.NotFound:
            pass

   @commands.hybrid_command(name="atmost", description="deletes the oldest messages in the channel if the channel message count goes over `m`")
   async def slash_atmost(self, ctx: commands.Context, m: Optional[int]=None, channel: Optional[int]=None) -> None:
      guild = await self.check_perms(ctx, channel, _requires_manage_channel_and_manage_messages)
      if guild is None: return

      await ctx.message.add_reaction("⏲️")

      if channel is None: channel = ctx.channel.id
      guild = await self.get_guild_id(channel)
      settings = self.client.memo.load(channel)

      at_most = inf if m is None else max(0, m)
      # at_most parameter can bump down the at_least parameter
      at_least = min(settings.at_least, at_most)
      settings = settings.replace(at_least=at_least, at_most=at_most)

      self.client.memo.save(channel, guild, settings)
      await self.check_flotsam(channel)

      if ctx.message:
         try:
            if self.client.user is not None:
               await ctx.message.remove_reaction("⏲️", self.client.user)
            await ctx.message.add_reaction("👌")
         except discord.NotFound:
            pass

   @commands.hybrid_command(name="minutes", description="set messages to wash away each after `t` seconds")
   async def slash_minutes(self, ctx: commands.Context, t: Optional[int]=None, channel: Optional[int]=None) -> None:
      guild = await self.check_perms(ctx, channel, _requires_manage_channel_and_manage_messages)
      if guild is None: return

      await ctx.message.add_reaction("⏲️")

      if channel is None: channel = ctx.channel.id
      guild = await self.get_guild_id(channel)
      settings = self.client.memo.load(channel)

      minutes = inf if t is None else t
      settings = settings.replace(minutes=minutes)

      self.client.memo.save(channel, guild, settings)
      await self.check_flotsam(channel)

      if ctx.message:
         try:
            if self.client.user is not None:
               await ctx.message.remove_reaction("⏲️", self.client.user)
            await ctx.message.add_reaction("👌")
         except discord.NotFound:
            pass

   @commands.hybrid_command(name="wave", description="wash away `n` of the most recent messages in the channel")
   async def slash_wave(self, ctx: commands.Context, n: int=100, channel: Optional[int]=None):
      if n < 0:
         if ctx.message:
            await ctx.message.add_reaction("🤔")
         return

      if n == 0:
         if ctx.message:
            await ctx.message.add_reaction("👋")
         return

      guild = await self.check_perms(ctx, channel, _requires_manage_messages)
      if guild is None: return

      if channel is None: channel = ctx.channel.id

      if ctx.message:
         await ctx.message.add_reaction("⏲️")
         await ctx.message.add_reaction("🌊")

      await self.client.delete_messages(channel, limit=n, beside=ctx.message.id)

      if ctx.message:
         try:
            if self.client.user is not None:
               await ctx.message.remove_reaction("⏲️", self.client.user)
               await ctx.message.remove_reaction("🌊", self.client.user)
            await ctx.message.add_reaction("👌")
            await ctx.message.delete(delay=1)
         except discord.NotFound:
            pass

   @commands.hybrid_command(name="current", description="get current channel settings")
   async def slash_current(self, ctx: commands.Context, channel: Optional[int]=None):
      guild = await self.check_perms(ctx, channel, _requires_manage_messages)
      if guild is None: return

      if channel is None: channel = ctx.channel.id
      settings = Settings() if not channel in self.client.memo.channels \
         else self.client.memo.channels[channel]

      content = (
         f"```py\n"
         f"{{\n"
         f"   \"at_least\": {settings.at_least},\n"
         f"   \"at_most\": {settings.at_most},\n"
         f"   \"minutes\": {settings.minutes}\n"
         f"}}\n"
         f"```\n"
      ).strip()

      status = settings_status(settings)

      embed = discord.Embed(
         title="Current settings for this channel",
         description=status,
         color=self.client.color
      )

      await ctx.reply(content, embed=embed)

async def setup(client: Swashbot) -> None:
   await client.add_cog(FrontCog(client))