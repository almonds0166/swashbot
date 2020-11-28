
import sqlite3
import random

import discord

INF = None

async def command(client, param, ctx):
   """
   Syntax:
      ~at least m

   Description:
      Swashbot will always keep the m most recent messages in the channel
      Saves settings in swashbot's LTM
   """
   if param.isdigit():
      param = max(0, int(param))
   elif param in ("inf", "infty", "infinity"):
      param = INF
   else:
      await ctx.msg.add_reaction("👀")
      return

   cid = ctx.channel.id

   if cid not in client.memo:
      client.memo[cid] = client.DEFAULT_SETTINGS.copy()

   if param is INF:
      # short circuit to default settings
      client.memo[cid] = client.DEFAULT_SETTINGS.copy()
   else:
      client.memo[cid].at_least = param
      if client.memo[cid].at_most is not None:
         client.memo[cid].at_most = max(param, client.memo[cid].at_most)

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