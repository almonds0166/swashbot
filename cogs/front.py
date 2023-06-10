from typing import Optional, Callable

from math import inf, isinf
import asyncio

import discord
from discord.ext import commands

from main import Swashbot, SwashbotMessageable
from utils.memory import Settings

# TODO: there's lots of repeated code in here, hard to navigate
# Especially the cumbersome emoji reaction logic

_permissions_to_message = discord.Permissions(
   send_messages=True,
   send_messages_in_threads=True,
)
_permission_to_delete = discord.Permissions(
   manage_messages=True,
   view_channel=True,
   read_message_history=True,
)
_permissions_for_settings_commands = _permissions_to_message | _permission_to_delete

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

class FrontCog(commands.Cog):
   """Cog that handles the user commands
   """
   def __init__(self, client: Swashbot) -> None:
      self.client = client

   async def get_guild_id(self, channel: int) -> int:
      discord_channel = await self.client.try_channel(channel)
      guild = discord_channel.guild.id
      return guild

   async def check_flotsam(self, channel: int) -> int:
      # nothing to do
      if channel not in self.client.memo.settings:
         if channel in self.client.decks:
            del self.client.decks[channel]
         return 0

      # need to re-gather
      return await self.client.gather_flotsam(channel)

   async def check_user_permissions(self,
      ctx: commands.Context,
      channel: Optional[int],
      check: Callable[[discord.Permissions, str], Optional[str]],
   ) -> Optional[int]:
      """Checks if the user who invoked the command is allowed to do so

      Parameters:
         ctx: Command context
         channel: Channel ID from command arg, if provided
         check: See check functions above in this file (front.py)

      Returns:
         int: Guild ID, if user has the permissions
         None: None, if user has insufficient permissions
      """
      if not isinstance(ctx.author, discord.Member): return
      if not isinstance(ctx.channel, SwashbotMessageable): return

      the_channel = "this channel" if channel is None else ""

      if channel is None:
         channel = ctx.channel.id
         discord_channel = ctx.channel
      else:
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

   @commands.hybrid_command(name="sink", description="re-sync messages for the channel")
   async def slash_sink(self, ctx: commands.Context, channel: Optional[int]=None) -> None:
      if not isinstance(ctx.channel, SwashbotMessageable): return
      guild = await self.check_user_permissions(ctx, channel, _requires_manage_channel_and_manage_messages)
      if guild is None: return
      if channel is None: channel = ctx.channel.id

      if ctx.message:
         try:
            await ctx.message.add_reaction("⏲️")
         except (discord.Forbidden, discord.NotFound):
            pass

      count = await self.check_flotsam(channel)

      if ctx.message:
         try:
            if self.client.user is not None:
               await ctx.message.remove_reaction("⏲️", self.client.user)
            await ctx.message.add_reaction("👌")
         except (discord.Forbidden, discord.NotFound):
            pass

      if ctx.interaction:
         await ctx.reply(f"Found {count} message" + ("s!" if count != 1 else "!"))

   @commands.hybrid_command(name="atleast", description="always keep the `m` most recent messages in the channel")
   async def slash_atleast(self, ctx: commands.Context, m: str, channel: Optional[int]=None) -> None:
      if not isinstance(ctx.channel, SwashbotMessageable): return
      guild = await self.check_user_permissions(ctx, channel, _requires_manage_channel_and_manage_messages)
      if guild is None: return

      try:
         await ctx.message.add_reaction("👀")
      except (discord.NotFound, discord.Forbidden):
         pass

      if channel is None: channel = ctx.channel.id
      settings = self.client.memo.load(channel)

      if m.lower() in ("inf", "infinity"):
         at_least = inf
      elif m.isdigit():
         at_least = int(m)
      else:
         return
      # at_least parameter can bump up the at_most parameter
      at_most = max(settings.at_most, at_least)
      settings = settings.replace(at_least=at_least, at_most=at_most)

      if settings:
         if not await self.client.check_permissions(ctx.channel, _permissions_for_settings_commands, inform=ctx.message):
            return

      self.client.memo.save(channel, guild, settings)
      await self.check_flotsam(channel)

      if ctx.message:
         try:
            if self.client.user is not None:
               await ctx.message.remove_reaction("👀", self.client.user)
            await ctx.message.add_reaction("👌")
         except discord.NotFound:
            pass

      if ctx.interaction:
         await ctx.reply(f"Done! `at_least = {settings.at_least}`")

   @commands.hybrid_command(name="atmost", description="deletes the oldest messages in the channel if the channel message count goes over `m`")
   async def slash_atmost(self, ctx: commands.Context, m: str, channel: Optional[int]=None) -> None:
      if not isinstance(ctx.channel, SwashbotMessageable): return
      guild = await self.check_user_permissions(ctx, channel, _requires_manage_channel_and_manage_messages)
      if guild is None: return

      try:
         await ctx.message.add_reaction("👀")
      except (discord.NotFound, discord.Forbidden):
         pass

      if channel is None: channel = ctx.channel.id
      settings = self.client.memo.load(channel)

      if m.lower() in ("inf", "infinity"):
         at_most = inf
      elif m.isdigit():
         at_most = int(m)
      else:
         return
      # at_most parameter can bump down the at_least parameter
      at_least = min(settings.at_least, at_most)
      settings = settings.replace(at_least=at_least, at_most=at_most)

      if settings:
         if not await self.client.check_permissions(ctx.channel, _permissions_for_settings_commands, inform=ctx.message):
            return

      self.client.memo.save(channel, guild, settings)
      await self.check_flotsam(channel)

      if ctx.message:
         try:
            if self.client.user is not None:
               await ctx.message.remove_reaction("👀", self.client.user)
            await ctx.message.add_reaction("👌")
         except discord.NotFound:
            pass

      if ctx.interaction:
         await ctx.reply(f"Done! `at_most = {settings.at_most}`")

   @commands.hybrid_command(name="minutes", description="set messages to wash away each after `t` seconds")
   async def slash_minutes(self, ctx: commands.Context, t: str, channel: Optional[int]=None) -> None:
      if not isinstance(ctx.channel, SwashbotMessageable): return
      guild = await self.check_user_permissions(ctx, channel, _requires_manage_channel_and_manage_messages)
      if guild is None: return

      try:
         await ctx.message.add_reaction("👀")
      except (discord.NotFound, discord.Forbidden):
         pass

      if channel is None: channel = ctx.channel.id
      settings = self.client.memo.load(channel)

      if t.lower() in ("inf", "infinity"):
         minutes = inf
      elif t.isdigit():
         minutes = int(t)
      else:
         return
      settings = settings.replace(minutes=minutes)

      if settings:
         if not await self.client.check_permissions(ctx.channel, _permissions_for_settings_commands, inform=ctx.message):
            return

      self.client.memo.save(channel, guild, settings)
      await self.check_flotsam(channel)

      if ctx.message:
         try:
            if self.client.user is not None:
               await ctx.message.remove_reaction("👀", self.client.user)
            await ctx.message.add_reaction("👌")
         except (discord.NotFound, discord.Forbidden):
            pass

      if ctx.interaction:
         await ctx.reply(f"Done! `minutes = {settings.minutes}`")

   @commands.hybrid_command(name="wave", description="wash away `n` of the most recent messages in the channel")
   async def slash_wave(self, ctx: commands.Context, n: int=100, channel: Optional[int]=None):

      if n < 0:
         if ctx.message:
            try:
               await ctx.message.add_reaction("🤔")
            except (discord.Forbidden, discord.NotFound):
               pass
         return

      if n == 0:
         if ctx.message:
            try:
               await ctx.message.add_reaction("👋")
            except (discord.Forbidden, discord.NotFound):
               pass
         return

      if not isinstance(ctx.channel, SwashbotMessageable): return
      guild = await self.check_user_permissions(ctx, channel, _requires_manage_messages)
      if guild is None: return

      if channel is None:
         channel = ctx.channel.id
         discord_channel = ctx.channel
      else:
         discord_channel = await self.client.try_channel(channel)

      if not await self.client.check_permissions(discord_channel, _permission_to_delete, inform=ctx.message):
         return

      if ctx.message:
         try:
            await ctx.message.add_reaction("⏲️")
            await ctx.message.add_reaction("🌊")
         except (discord.Forbidden, discord.NotFound):
            pass

      await self.client.delete_messages(channel, limit=n, beside=ctx.message.id)

      if ctx.message:
         try:
            if self.client.user is not None:
               await ctx.message.remove_reaction("⏲️", self.client.user)
               await ctx.message.remove_reaction("🌊", self.client.user)
            await ctx.message.add_reaction("👌")
            await ctx.message.delete(delay=1)
         except (discord.Forbidden, discord.NotFound):
            pass

      if ctx.interaction:
         await ctx.reply(f"Done!")

   @commands.hybrid_command(name="current", description="get current channel settings")
   async def slash_current(self, ctx: commands.Context, channel: Optional[int]=None):
      if not isinstance(ctx.channel, SwashbotMessageable): return
      guild = await self.check_user_permissions(ctx, channel, _requires_manage_messages)
      if guild is None: return

      if channel is None: channel = ctx.channel.id
      settings = Settings() if not channel in self.client.memo.settings \
         else self.client.memo.settings[channel]

      if not await self.client.check_permissions(ctx.channel, _permissions_to_message, inform=ctx.message):
         return

      content = (
         f"```py\n"
         f"{{\n"
         f"   \"at_least\": {settings.at_least},\n"
         f"   \"at_most\": {settings.at_most},\n"
         f"   \"minutes\": {settings.minutes}\n"
         f"}}\n"
         f"```\n"
      ).strip()

      status = str(settings)

      embed = discord.Embed(
         title="Current settings for this channel",
         description=status,
         color=self.client.color
      )

      await ctx.reply(content, embed=embed)

async def setup(client: Swashbot) -> None:
   await client.add_cog(FrontCog(client))