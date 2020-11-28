
import sqlite3
import random

import discord

INF = None

async def command(client, param, ctx):
   """
   Syntax:
      ~time t

   Description:
      Change how long it takes for messages in the swash zone to erase.
      t is in minutes.
   """
   if param.isdigit():
      param = max(0, int(param))
   elif param in ("inf", "infty", "infinity"):
      param = INF
   else:
      await ctx.msg.add_reaction("👀")
      return

   cid = ctx.channel.id
   previous_settings = client.memo.get(cid, client.DEFAULT_SETTINGS.copy())
   was_swashing = previous_settings.at_most is not INF or previous_settings.time is not INF

   if cid not in client.memo: client.memo[cid] = previous_settings
   client.memo[cid].time = param

   if not was_swashing and param is not INF:
      client.loop.create_task(client.swash(cid, ctx))

   # update ltm
   gid = None if ctx.guild is None else ctx.guild.id

   conn = sqlite3.connect(client.MEMORY)
   c = conn.cursor()

   if client.memo[cid].at_least == 0 \
   and client.memo[cid].at_most is INF \
   and client.memo[cid].time is INF:

      c.execute(
         """
         DELETE FROM memo
         WHERE channel = ?;
         """,
         (cid,)
      )

   else:

      c.execute(
         """
         INSERT OR REPLACE INTO memo (channel, guild, at_least, at_most, time_)
         VALUES (?, ?, ?, ?, ?);
         """,
         (cid, gid, client.memo[cid].at_least, client.memo[cid].at_most, client.memo[cid].time)
      )

   conn.commit()

   try:
      await ctx.msg.add_reaction("👌")
   except discord.NotFound:
      pass

   return