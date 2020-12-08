
async def command(client, param, ctx):
   """
   Syntax:
      ~debug

   Description:
      Just tells me how many servers and channels swashbot
      is swashing about in, and gives me the current channel settings
   """
   if param.isdigit():
      param = max(0, int(param))
   elif param in ("inf", "infty", "infinity"):
      param = 10
   else: # param == ""
      param = 5 # default value
   param = min(param, 10)

   cid = ctx.channel.id

   if cid in client.memo:
      s = (
         f"```python\n"
         f"memo = {{\n"
         f"   \"at_least\": {client.memo[cid].at_least},\n"
         f"   \"at_most\": {client.memo[cid].at_most},\n"
         f"   \"time\": {client.memo[cid].time},\n"
         f"}}\n"
         f"```\n"
      )
   else:
      s = "No settings saved for this channel yet.\n"

   s += (
      f"`n` = `{len(client.all_guilds)}`\n"
      f"`c` = `{len(client.all_channels)}`\n"
   )

   s += f"Tail ({param}) of `debug.log`:\n```\n"

   with open("./debug.log") as f: # fragile!?
      for line in f.readlines()[-param:]:
         s += line # already has \n

   s += "```"

   await ctx.channel.send(s)