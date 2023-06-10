from __future__ import annotations
from typing import Optional, Union

from pathlib import Path
from datetime import datetime, timedelta
from math import isinf
import asyncio
import traceback
import logging

import discord
from discord.ext import commands

from utils.memory import LongTermMemory, Settings
from utils.flotsam import Deck
from utils.logging import TaskTracker
from config import SWASHBOT_PREFIX, SWASHBOT_DATABASE

# TODO: if a message has a thread attached, delete it?

SwashbotMessageable = Union[discord.TextChannel, discord.Thread]

_swashbot_intents = discord.Intents(
   guilds=True,
   guild_messages=True,
   message_content=True,
)
_swashbot_color = discord.Colour.from_rgb(46, 137, 139)
_swashbot_login_activity = discord.Activity(
   type=discord.ActivityType.listening,
   name="the soft waves"
)
_swashbot_throttle_seconds = 0.85

class Swashbot(commands.Bot):
   """Represents our beloved ocean bot

   Attributes:
      color: Bot color theme
      ready: `datetime` of when bot first logged in successfuly
      disconnects: the number of disconnects since ready
      messages_deleted: the number of messages deleted since ready
      errors: errors caught since ready
      busy_level: the number of channels Swashbot is currently performing busywork on
      commands_processed: the number of commands successfully processed
      memo: saved `~utils.memory.Settings` for channels
      decks: records of channels' messages for smart deletion
   """
   color: discord.Colour = _swashbot_color

   # analytics
   ready: Optional[datetime] = None
   disconnects: int = 0
   messages_deleted: int = 0
   errors: int = 0
   busy_level: int = 0
   commands_processed: int = 0

   def __init__(self) -> None:
      commands.Bot.__init__(self, SWASHBOT_PREFIX,
         intents=_swashbot_intents,
         max_messages=None,
         activity=_swashbot_login_activity,
         status=discord.Status.online,
      )
      self.memo = LongTermMemory(Path(SWASHBOT_DATABASE))
      self.decks: dict[int, Deck] = {}
      self.log = logging.getLogger("swashbot")
      self.new_task = TaskTracker()

   async def setup_hook(self) -> None:
      cogs = []
      for file in Path("./cogs").iterdir():
         if file.suffix == ".py":
            cog = f"cogs.{file.stem}"
            await self.load_extension(cog)
            cogs.append(cog)

      self.log.info(f"Loaded {len(cogs)} cog(s): {cogs}.")

   async def on_ready(self) -> None:
      if self.ready:
         self.disconnects += 1
         return
      
      for channel in list(self.memo.settings):
         await self.gather_flotsam(channel)
      
      self.ready = datetime.utcnow()

   async def on_error(self, event_method: str, *args, **kwargs) -> None:
     self.errors += 1
     e = traceback.format_exc()
     summary = f"method: {event_method}\nargs: {args}\nkwargs: {kwargs}"
     details = f"```\n{e}\n```"
     self.log.error(f"Encountered error:\n{summary}\n{details}")

   async def on_command_error(self, ctx: commands.Context, error: commands.errors.CommandError) -> None:
      self.log.error(f"Unexpected command error:\n{error}")
      try:
         await ctx.message.add_reaction("👀")
      except:
         pass
      return await super().on_command_error(ctx, error)

   async def on_message(self, message: discord.Message) -> None:
      if not self.ready: return
      channel = message.channel.id
      if channel in self.memo.settings:
         self.decks[channel].append_new(message)

      await self.process_commands(message)

   async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
      """(Whenever a message deletion is detected)
      """
      channel = payload.channel_id
      if channel not in self.decks: return
      message = payload.message_id

      try:
         self.decks[channel].remove(message)
      except KeyError:
         pass

   async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent) -> None:
      """(Whenever a batch of messages has been detected as deleted)
      """
      channel = payload.channel_id
      if channel not in self.decks: return
      task = self.new_task()
      self.log.info(f"{task}: Handling bulk delete of {len(payload.message_ids)} message(s) in channel {payload.channel_id} (guild {payload.guild_id}).")

      for message in payload.message_ids:
         try:
            self.decks[channel].remove(message)
         except KeyError:
            pass

      self.log.info(f"{task}: Done.")

   async def on_guild_remove(self, guild: discord.Guild) -> None:
      if guild.id not in self.memo.channels: return

      channels = self.memo.channels[guild.id]
      task = self.new_task()
      self.log.info(f"{task}: I was removed from a {guild.name!r} ({guild.id}), so I'll remove its {len(channels)} deck(s) from memory.")

      for channel in channels: self.memo.remove(channel)
      self.log.info(f"{task}: Done.")

   async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
      if channel in self.memo.settings:
         self.log.info(f"The channel {channel.name!r} ({channel.id}) I was watching was deleted, so I'll remove its deck from memory.")
         self.memo.remove(channel.id)

   async def on_raw_thread_delete(self, payload: discord.RawThreadDeleteEvent) -> None:
      if payload.thread_id in self.memo.settings:
         self.log.info(f"The thread {payload.thread_id} I was watching was deleted, so I'll remove its deck from memory.")
         self.memo.remove(payload.thread_id)

   async def on_command_completion(self, ctx: commands.Context) -> None:
      self.commands_processed += 1
      args = ", ".join([repr(arg) for arg in ctx.args][2:])
      means = f"{ctx.message.content!r}" if ctx.message.content else "a slash command"
      summary = (
         f"``{ctx.command}({args})`` invoked by "
         f"{ctx.author} with {means}"
      )
      self.log.debug(f"Completed processing command #{self.commands_processed}: {summary}.")

   @property
   def uptime(self) -> str:
      """Human-readable uptime
      """
      age = timedelta() if self.ready is None else (datetime.utcnow() - self.ready)
      hours, remainder = divmod(int(age.total_seconds()), 3600)
      minutes, seconds = divmod(remainder, 60)
      days, hours = divmod(hours, 24)
      months, days = divmod(days, 30)

      parts = []
      if months: parts.append(f"{months}m")
      if months or days: parts.append(f"{days}d")
      if months or days or hours: parts.append(f"{hours}h")
      if months or days or hours or minutes: parts.append(f"{minutes}m")
      parts.append(f"{seconds}s")

      return " ".join(parts)

   @property
   def deletion_rate(self) -> str:
      """Messages washed away per unit time
      """
      age = timedelta() if self.ready is None else (datetime.utcnow() - self.ready)
      seconds = max(0, age.total_seconds())

      if seconds == 0 or self.messages_deleted == 0:
         return "n/a"

      if self.messages_deleted > seconds:
         return f"{self.messages_deleted / seconds:.2f} msg/s"

      return f"1 message every {seconds / self.messages_deleted:.2f}s"

   async def try_channel(self, channel: int) -> SwashbotMessageable:
      """Return full Discord channel object given channel ID

      Args:
         channel: Channel ID
      """
      task = self.new_task()
      self.log.debug(f"{task}: Trying to fetch channel {channel}...")
      discord_channel = await self.fetch_channel(channel)
      assert isinstance(discord_channel, SwashbotMessageable)
      self.log.debug(f"{task}: Done.")
      return discord_channel

   async def gather_flotsam(self, channel: int) -> int:
      """Keep a record of messages in a channel

      Args:
         channel: Channel ID

      Returns:
         int: Number of messages gathered.
      """
      task = self.new_task()
      self.log.info(f"{task}: Gathering flotsam for channel {channel}...")
      start = datetime.utcnow()

      settings = self.memo.settings[channel]
      if not settings: return 0

      try:
         discord_channel = await self.try_channel(channel)
      except discord.NotFound:
         if channel in self.memo.settings: self.memo.remove(channel)
         return 0
      deck = Deck()

      limit = None if isinf(settings.at_most) else int(settings.at_most + 10)
      async for message in discord_channel.history(limit=limit):
         if message.pinned: continue
         deck.append_old(message)

      self.decks[channel] = deck

      minutes, seconds = (int((datetime.utcnow() - start).total_seconds()), 60)
      if seconds == 60: seconds = 0 # weird divmod bug
      time = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
      self.log.info(f"{task}: Finished gathering flotsam for {discord_channel.name!r} ({channel}) (about {len(deck)} messages(s) after {time}).")
      return len(deck)

   async def try_delete(self, discord_channel: SwashbotMessageable, id: int) -> None:
      """Attempt to delete a single message

      Args:
         discord_channel: Full Discord channel object
         id: Discord message ID
      """
      try:
         message = await discord_channel.fetch_message(id)
      except discord.NotFound:
         self.log.debug(f"Message {id} was not found.")
         return
      if message.pinned: return
      while self.is_ws_ratelimited(): await asyncio.sleep(0)
      try:
         await message.delete()
         self.messages_deleted += 1
      except discord.Forbidden:
         pass
      await asyncio.sleep(_swashbot_throttle_seconds)

   async def delete_messages(self, channel: int, *, limit: int, beside: Optional[int]=None) -> None:
      """Delete a number of a channel's most recent messages

      Args:
         channel: Channel ID

      Keyword Args:
         limit: Integer number of messages to delete
         beside: Message ID of message to avoi deleting
      """
      if beside is not None: limit += 1
      discord_channel = await self.try_channel(channel)
      async for message in discord_channel.history(limit=limit):
         if message.id == beside: continue
         if message.pinned: continue
         try:
            await message.delete()
            self.messages_deleted += 1
         except discord.Forbidden:
            pass
         await asyncio.sleep(_swashbot_throttle_seconds)

   async def check_permissions(self, channel: SwashbotMessageable, required: discord.Permissions, *,
      inform: Optional[discord.Message]=None
   ) -> bool:
      """Check if we have the required permissions to continue

      If we do, returns True, otherwise False. Swashbot will also try to
      communicate what permissions are required.

      Parameters:
         channel: The Discord channel to check if we have permissions for
         required: Permissions required to return True
         inform: The Message to try to contact if we don't have enough permissions
      """
      if self.user is None: return False
      self_member = channel.guild.get_member(self.user.id)

      if self_member is None:
         self.log.warning((
            f"I tried to check my permissions for {channel.name!r} ({channel.id}) in "
            f"{channel.guild.name!r} ({channel.guild.id}), but it seems I'm not in that guild?"
         ))
         return False

      perms = channel.permissions_for(self_member)
      if required <= perms: return True

      missing_perms = \
         set(perm for perm, value in required if value) \
         - set(perm for perm, value in perms if value)
      missing = ", ".join([
         f"**{perm}**"
         for perm in missing_perms
      ])

      if inform:
         inform_channel_perms = inform.channel.permissions_for(self_member)
         msg = f"I need the following permission(s): {missing} 🙏"
         if inform_channel_perms.send_messages:
            async with channel.typing(): await asyncio.sleep(1)
            if inform_channel_perms.read_message_history:
               await inform.reply(msg)
            else:
               await inform.channel.send(msg)
         elif inform_channel_perms.add_reactions:
            await inform.add_reaction("🙏")

      return False