
import sqlite3

import discord

INF = None

async def command(client, param, ctx):
   """
   Syntax:
      ~prefix p

   Description:
      Changes the server prefix to p, which is a string that may be up to 32 characters.
      At the time of writing this, I can imagine quite a few critical bugs that may result if
      users forget their prefix. Hmm. I guess in that case, contact me, and I can take a look.
   """
   p = param.strip()[:32]

   client.prefixes[ctx.guild.id] = p

   # update ltm
   conn = sqlite3.connect(client.MEMORY)
   c = conn.cursor()

   if p == "~":

      c.execute(
         """
         DELETE FROM prefixes
         WHERE guild = ?;
         """,
         (ctx.guild.id,)
      )

   else:

      c.execute(
         """
         INSERT OR REPLACE INTO prefixes (guild, prefix)
         VALUES (?, ?);
         """,
         (ctx.guild.id, p)
      )

   conn.commit()

   try:
      await ctx.msg.add_reaction("👌")
   except discord.NotFound:
      pass

   return