from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from pathlib import Path
from datetime import datetime, timedelta
from math import isinf
import traceback

import discord
from discord.ext import commands

from utils.memory import LongTermMemory
from utils.flotsam import Deck
from config import SWASHBOT_PREFIX, SWASHBOT_DATABASE

# TODO: if a message has a thread attached, delete it?

_swashbot_intents = discord.Intents(
   guilds=True,
   guild_messages=True,
   message_content=True,
)
_swashbot_color = discord.Colour.from_rgb(46, 137, 139)

class Swashbot(commands.Bot):
   """Represents our beloved ocean bot

   Attributes:
      color: Bot color theme
      ready: `datetime` of when bot first logged in successfuly
      disconnects: the number of disconnects since ready
      messages_deleted: the number of messages deleted since ready
      errors: errors caught since ready
      busy_level: the number of channels Swashbot is currently performing busywork on
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

   def __init__(self) -> None:
      commands.Bot.__init__(self, SWASHBOT_PREFIX, intents=_swashbot_intents)
      self.memo = LongTermMemory(Path(SWASHBOT_DATABASE))
      self.decks: dict[int, Deck] = {}

   async def setup_hook(self) -> None:
      for file in Path("./cogs").iterdir():
         if file.suffix == ".py":
            cog = f"cogs.{file.stem}"
            await self.load_extension(cog)

   async def on_ready(self) -> None:
      if self.ready:
         self.disconnects += 1
         return
      
      for channel in self.memo.channels:
         await self.gather_flotsam(channel)
      
      await self.change_presence(status=discord.Status.online)
      self.ready = datetime.utcnow()

   async def on_error(self, event_method: str, *args, **kwargs) -> None:
     self.errors += 1
     e = traceback.format_exc()
     summary = f"method: {event_method}\nargs: {args}\nkwargs: {kwargs}"
     details = f"```\n{e}\n```"

   async def on_command_error(self, ctx: commands.Context, error: commands.errors.CommandError) -> None:
      try:
         await ctx.message.add_reaction("👀")
      except:
         pass
      return await super().on_command_error(ctx, error)

   async def on_message(self, message: discord.Message) -> None:
      if not self.ready: return
      channel = message.channel.id
      if channel in self.memo.channels:
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

   async def try_channel(self, channel: int) -> discord.TextChannel:
      """Return full Discord channel object given channel ID

      Args:
         channel: Channel ID
      """
      discord_channel = await self.fetch_channel(channel)
      assert isinstance(discord_channel, discord.TextChannel)
      return discord_channel

   async def gather_flotsam(self, channel: int) -> None:
      """Keep a record of messages in a channel

      Args:
         channel: Channel ID
      """
      settings = self.memo.channels[channel]
      if not settings: return

      discord_channel = await self.try_channel(channel)
      deck = Deck()

      # ⚠️ TODO: not sure if this limit is correct
      limit = None if isinf(settings.at_most) else int()
      async for message in discord_channel.history(limit=limit):
         if message.pinned: continue
         deck.append_old(message)

      self.decks[channel] = deck

   async def try_delete(self, discord_channel: discord.TextChannel, id: int) -> None:
      """Attempt to delete a single message

      Args:
         discord_channel: Full Discord channel object
         id: Discord message ID
      """
      try:
         message = await discord_channel.fetch_message(id)
      except discord.NotFound:
         return
      if message.pinned: return
      await message.delete()
      self.messages_deleted += 1

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
         await message.delete()
         self.messages_deleted += 1
