
import discord
import aiohttp

async def command(client, param, ctx):
   """
   Syntax:
      ~info

   Description:
      Shares information about Swashbot
   """
   tmp = "https://api.github.com/repos/almonds0166/swashbot/git/refs/heads/master"
   
   async with aiohttp.ClientSession() as session:
      async with session.get(tmp) as resp:
         r = await resp.json() # note for future: check if 200

   latest_commit_sha = r["object"]["sha"][:7]
   latest_commit_url = "https://github.com/almonds0166/swashbot/commits/" + r["object"]["sha"]
   # yeah, technically, Swashbot isn't guaranteed to have the most up-to-date commit
   # as of today, at least

   f = (
      "Hello! I'm Swashbot (:\n"
      "I wash Discord messages away over time [like gentle beach waves]"
      "(https://youtu.be/b44ruhi5ji4), inspired by ephemeral messaging platforms like Signal."
   )

   e = discord.Embed(
      title="About",
      description=f,
      color=client.color
   )

   e.add_field(
      name="Name",
      value="[Swashbot](https://api.github.com/repos/almonds0166/swashbot)"
   )

   e.add_field(
      name="Latest commit",
      value=f"[{latest_commit_sha}]({latest_commit_url})"
   )

   e.add_field(
      name="Framework",
      value="[discord.py](https://github.com/Rapptz/discord.py)"
   )

   await ctx.channel.send(embed=e)