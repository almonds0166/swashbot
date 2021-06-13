
import os
from pathlib import Path
import sys
from datetime import datetime, timedelta

import discord
import asyncio
import aiohttp

from swashbot.config import *
from swashbot.debug import *
from swashbot.utils import *

INF = None

class Swashbot(discord.Client):
   def __init__(self, token, **kwargs):
      super().__init__(**kwargs)
      
      self.loop.create_task(self.toc())
      self.token = token

      # important constants
      self.DEFAULT_SETTINGS = Settings()
      self.MEMORY = MEMORY

      # initialize memory
      self.flotsam = {}
      self.prefixes = {}
      self.ready = False
      self.memo = {}
      self.t0 = None

      # analytics
      self.all_guilds = set()
      self.all_channels = set()

      # sugar
      self.color = discord.Colour.from_rgb(*COLOUR)
      self.emojis_ = {
         "wait": {"⏲️": 1},
         "wash": {"🌊": 1},
         "wave": {"<a:awave:780163655568064513>": 1},
         "done": {"👌": 1},
         "eyes": {"👀": 1}
      } # emojis randomly chosen with custom weights (not yet implemented)

      # load commands
      current_dir = Path(os.path.dirname(os.path.realpath(__file__)))
      self.cmds = {}
      for item in os.listdir(current_dir / "cmds"):
         full_path = Path(current_dir / "cmds" / item)
         cmd = full_path.stem.replace("_", " ")
         if not full_path.is_file() or full_path.suffix != ".py": continue
         module_name = f"swashbot.cmds.{full_path.stem}"
         self.cmds[cmd] = __import__(module_name, fromlist=[None]).command

   async def toc(self):
      """
      Routine that adds a dot to the screen every 60 seconds or so.
      Refreshes activity status as well.
      """
      await self.wait_until_ready() # doesn't seem quite to work?
      activity = discord.Activity(
         type=discord.ActivityType.listening,
         name="the soft waves"
      )
      while True:
         await self.change_presence(
            status=discord.Status.online,
            activity=activity
         )
         await asyncio.sleep(10)
         print(" .")

   def run(self):
      super().run(self.token, bot=True)

   async def on_ready(self):
      # load long-term memory
      load_memory(self, MEMORY)

      if not self.ready:
         # keep track of uptime
         self.t0 = datetime.now()
         now = \
            self.t0.strftime("%a %d %b %Y at %H:%M:%S") + \
            self.t0.strftime("%p").lower()
         await info(
            f"Successfully connected to and prepared data from Discord. "
            f"Where I currently seem to be at, the time is {now}."
         )
         self.ready = True
      else:
         await debug("Reconnected after failed resume request.")
      pass

   async def on_error(self, event, *args, **kwargs):
      e = traceback.format_exc()
      await error(
         "Encountered exception, see here for details:\n" + e,
         webhook=False
      )
      await post_to_webhook(
         content="```\n" + e + "\n```",
         embed=f"event: {event}\nargs: {args}\nkwargs: {kwargs}"
      )

   async def try_to_fetch_channel(self, cid):
      """
      Handles any errors that may occur when fetching channels
      """
      try:
         channel = await self.fetch_channel(cid)
      except discord.InvalidData:
         await warn("I received an unknown channel from Discord. New Discord feature?")
      except discord.HTTPException:
         await warn("I encountered an HTTPException. Is my internet down? Is Discord down? https://discordstatus.com/")
      except discord.NotFound:
         await warn("Discord tells me it can't find the channel. Does it not exist anymore?")
      except discord.Forbidden:
         await warn("Discord tells me I don't have the proper permissions to access the channel.")
      else:
         return channel

      return None

   async def try_to_fetch_message(self, channel, mid):
      """
      Handles any errors that may occur when fetching messages
      """
      try:
         msg = await channel.fetch_message(mid)
      except discord.HTTPException:
         await warn("I encountered an HTTPException. Is Discord down? https://discordstatus.com/ Is my internet down?")
      except discord.NotFound:
         await warn("Discord tells me it can't find the message. So I guess consider the message aready deleted?")
      except discord.Forbidden:
         await warn("Discord tells me I don't have the proper permissions to access the message.")
      else:
         return msg

      return None

   async def delete_single_message(self, cid, mid):
      """
      Given channel and message ID, fetch the message and erase it
      """
      channel = await self.try_to_fetch_channel(cid)
      if channel is None: return

      msg = await self.try_to_fetch_message(channel, mid)
      if msg is None: return

      if not msg.pinned: await msg.delete()

   async def delete_multiple_messages(self, channel, t, limit=None):
      """
      Given channel and snowflake time t, delete at most limit messages before t
      """
      await info(f"Tasked with bulk deleting messages (limit = {limit}, before = {t}).")

      delete_count = 0
      async for msg in channel.history(limit=limit, before=t):
         if not msg.pinned: await msg.delete()
         delete_count += 1

   async def on_raw_message_delete(self, payload):
      """
      Remove messages from deque if need be
      """
      if not self.ready: return
      # check settings
      # if settings say that this channel is being watched, add msg to deck
      cid = payload.channel_id
      mid = payload.message_id
      if cid in self.memo:
         memo = self.memo[cid]
         if memo.at_most is not INF or memo.time is not INF:
            if cid not in self.flotsam: self.flotsam[cid] = Flotsam() # unclear how necessary this line is
            try:
               self.flotsam[cid].remove(mid)
            except KeyError: # not in there
               #await debug("Key was not found in self.decks. Did Swashbot delete this message?")
               pass

   async def on_raw_bulk_message_delete(self, payload):
      pass
      # not yet implemented

   async def on_guild_remove(self, guild):
      pass
      # not yet implemented

   async def on_message(self, msg):
      """
      Adds messages to deque if need be
      Respond to commands
      Detect new pins
      """
      if not self.ready: return

      # sadly, Swashbot can't hang out in group DMs
      if msg.channel.type == discord.ChannelType.group \
      or msg.channel.type == discord.ChannelType.private:
         return

      # construct context
      ctx = Context(msg=msg, channel=msg.channel, guild=msg.guild)
      cid = msg.channel.id
      gid = msg.guild.id

      # if a new pin was added, make sure to remove the newly pinned
      # message from deck, if it's there
      if msg.type == discord.MessageType.pins_add:
         await debug(f"Message with ID {msg.reference.message_id} was pinned in a channel.")
         if cid in self.flotsam:
            try:
               self.flotsam[cid].remove(msg.reference.message_id)
            except KeyError: # not in there
               #await debug("Key was not found in self.decks. Did Swashbot delete this message?")
               pass

      # check settings
      # if settings say that this channel is being watched, add msg to flotsam
      # note that brand new messages should never be pinned
      if cid in self.memo:
         memo = self.memo[cid]
         if memo.at_most is not INF or memo.time is not INF:
            if cid not in self.flotsam: self.flotsam[cid] = Flotsam() # necessary?
            self.flotsam[cid].append_new(msg)

      # at this point, make sure message isn't a system message
      if msg.is_system(): return

      # and make sure message wasn't sent by self
      if msg.author.id == self.user.id: return

      # otherwise, start processing command
      p = self.prefixes.get(gid, "~")
      if not msg.clean_content.startswith(p):
         # not a command
         return
      else:
         # could be a command
         content = msg.clean_content[len(p):].lower()

         cmd = None
         for potential_cmd in self.cmds.keys():
            if content.startswith(f"{potential_cmd} "):
               param = content[len(potential_cmd)+1:]
               cmd = potential_cmd
               break
            elif content == potential_cmd:
               param = ""
               cmd = potential_cmd
               break

         if cmd is None:
            try:
               await msg.add_reaction("👀")
            except discord.NotFound:
               pass
            return

      # cmd is indeed recognized as a command at this point

      # Swashbot only listens to members with the Manage Channels permission
      # hmm, users may be able to get around this by using bot/webhook proxies
      if not msg.author.bot \
      and not msg.author.permissions_in(msg.channel).manage_channels:
         await msg.channel.send("You don't have the `Manage Channels` permission :eyes:")
         return
      # additionally, Swashbot needs Manage Messages permission to operate
      if not msg.guild.me.permissions_in(msg.channel).manage_messages:
         await msg.channel.send("I need the `Manage Messages` permission before I can respond to commands :eyes:")
         return

      # now actually process the command
      await self.cmds[cmd](self, param, ctx)

      return

   async def gather_flotsam(self, cid):
      """
      Count the messages
      """
      self.flotsam[cid] = Flotsam()

      channel = await self.try_to_fetch_channel(cid)
      if channel is None: return False

      async for msg in channel.history(limit=self.memo[cid].at_most):
         if not msg.pinned:
            self.flotsam[cid].append_old(msg)

      try:
         await self.delete_multiple_messages(channel, self.flotsam[cid].oldest.t)
      except AttributeError:
         # this occurs if there are no messages in a channel or if (at_least == 0
         # and at_most == inf)
         pass

      return True

   async def swash(self, cid, ctx):
      """
      Probably most important part of this script
      Deletes messages if the Flotsam is detected to be too large in size
      And deletes messages in the swash zone that are considered too old
      """
      await info("Began new swash task.")
      try:
         await ctx.msg.add_reaction("⏲️")
      except AttributeError:
         pass
      except discord.NotFound:
         pass

      if not (await self.gather_flotsam(cid)):
         return # rip

      try:
         await ctx.msg.remove_reaction("⏲️", self.user)
         await ctx.msg.add_reaction("👌")
      except AttributeError:
         pass
      except discord.NotFound:
         pass

      memo = self.memo.get(cid, self.DEFAULT_SETTINGS).copy()
      while memo.at_most is not INF or memo.time is not INF:

         while self.flotsam[cid].size > (memo.at_most if memo.at_most is not None else float("inf")):
            mid = self.flotsam[cid].pop_oldest()
            await self.delete_single_message(cid, mid)

         delta_t = timedelta(minutes=memo.time if memo.time is not None else 5834160)
         while (self.flotsam[cid].size > (memo.at_least if memo.at_least is not None else float("inf"))) \
         and (self.flotsam[cid].oldest.t + delta_t < datetime.utcnow()):
            mid = self.flotsam[cid].pop_oldest()
            await self.delete_single_message(cid, mid)

         await asyncio.sleep(THROTTLE)

         memo = self.memo.get(cid, self.DEFAULT_SETTINGS).copy()

      await info("Shutting down ebb and flow process.")

      # clear the deck!
      del self.flotsam[cid]
      del self.memo[cid]

      return