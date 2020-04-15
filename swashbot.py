
import os
import traceback
import discord
import asyncio
import pickle
from collections import deque
from datetime import datetime, timedelta

BOT_NAME = "Swashbot"

ERROR_WEBHOOK = "" # for debugging purposes

HELP_MESSAGE = \
"""
https://github.com/almonds0166/swashbot

Example uses:
`@{0} help`: This help message
`@{0} here`: Wash away messages in the current channel (toggle)
`@{0} at least 10`: Always have at least 10 messages in the channel
`@{0} at most 50`: Always have no more than 50 messages in the channel
`@{0} time 60`: Messages wash away after 60 minutes
`@{0} tsunami`: Delete the last 100 messages

*Note*: {0} does not wash away pinned messages.
""".strip().format(BOT_NAME)

def STATUS_MESSAGE(**kwargs):
   """Creates a status string for the current settings."""
   s = ""
   if kwargs["atLeast"] == 0 and kwargs["atMost"] == 0:
      s += "Turbid! Delete all messages immediately.\n"
   elif kwargs["atLeast"] == 0:
      s += "Immediately delete all messages past count {atMost}.\n"
      if not kwargs["time"] is "inf":
         s += "Everything else takes {time} minute"
         s += "s" if kwargs["time"] != 1 else ""
         s += " to wash away.\n"
   elif kwargs["atLeast"] == kwargs["atMost"]:
      s += "Immediately delete all messages past count {atMost}.\n"
   else:
      s += "Delete all messages past count {atMost}.\n"
      s += "Keep at least {atLeast} messages.\n"
      if not kwargs["time"] is "inf":
         s += "Everything in-between takes {time} minute"
         s += "s" if kwargs["time"] != 1 else ""
         s += " to wash away.\n"
   return s.strip().format(**kwargs)

MEMORY = f"{BOT_NAME.lower()}.pkl"

def save_pickle():
   """Save database file"""
   pickle.dump(options, open(MEMORY, "wb"))

# load options

global options, queue
if os.path.exists(MEMORY):
   options = pickle.load(open(MEMORY, "rb"))
else:
   # default options
   options = {
      "atMost": 50,
      "atLeast": 0,
      "time": "inf", # minutes
      "channel": None,
      "me": "<@!>" # placeholder
   }
   save_pickle()
queue = deque()

client = discord.Client()

@client.event
async def on_message(message):
   """
   Adds messages to the queue if they came from the set channel.
   Interprets commands.
   """
   global options, queue

   if options["channel"] is None:
      if not message.author.bot \
      and message.content.strip().lower() == options["me"] + " here":
         await message.add_reaction("👀")
         options["channel"] = message.channel.id
         await refresh_queue()

      return

   if message.channel.id != options["channel"]: return

   queue.append(message)
   print(f"Added message to queue.")

   if not message.author.bot \
   and message.content.startswith(options["me"]): # command
      cmd, *args = message.content[len(options["me"]):].strip().lower().split(" ")
      await message.add_reaction("👀")

      if cmd == "tsunami":
         await asyncio.sleep(1)
         async for msg in message.channel.history():
            await decide_to_delete(msg)
         await refresh_queue()

      elif cmd == "help":
         e = discord.Embed()
         e.title = "Current options for this channel"
         e.description = STATUS_MESSAGE(**options)
         await message.channel.send(HELP_MESSAGE, embed=e)

      elif cmd == "at" \
      and len(args) >= 2 \
      and args[1].isdigit():
         count = int(args[1])

         if args[0] == "least":
            if count > options["atMost"]:
               options["atMost"] = count

            options["atLeast"] = count
            save_pickle()
            await refresh_queue()

         elif args[0] == "most":
            if count < options["atLeast"]:
               options["atLeast"] = count

            options["atMost"] = count
            save_pickle()
            await refresh_queue()

      elif (cmd == "time" \
      or cmd == "timeout") \
      and args:
         if args[0].isdigit():
            time = int(args[0])
            if time == 0:
               options["atMost"] = options["atLeast"]
               save_pickle()
               await refresh_queue()
            else:
               options["time"] = time
               save_pickle()
         elif args[0] == "inf":
            options["time"] = args[0]
            save_pickle()

      elif cmd == "here":
         if options["channel"] == message.channel.id:
            options["channel"] = None
         else:
            options["channel"] = message.channel.id
         save_pickle()
         await refresh_queue()

      else:
         # doesn't understand
         pass

@client.event
async def on_error(event, *args, **kwargs):
   error = traceback.format_exc()
   params = {
      "content": "```\n" + error + "\n```",
      "embeds": [{
         "description": f"event: {event}\nargs: {args}\nkwargs: {kwargs}"
      }]
   }
   if not ERROR_WEBHOOK:
      print("___")
      print(params["content"])
      print(params["embeds"][0]["description"])
   else:
      requests.post(ERROR_WEBHOOK, json=params)

async def decide_to_delete(msg, force=False):
   """
   Deletes messages if they are not pinned.
   Suppresses errors (i.e. if a message is already deleted).
   """
   global options, queue

   try:
      if force \
      or not msg.pinned: #or not msg.content.startswith(options["save"])
         await msg.delete()
   except discord.errors.NotFound:
      pass

async def refresh_queue(limit=100):
   """Adds at most 100 or so messages to the queue that Swashbot looks at."""
   queue.clear()
   if options["channel"] is None: return
   async for msg in client.get_channel(options["channel"]).history(limit=limit):
      queue.appendleft(msg)

async def tik():
   """Adds a dot to the screen every 60 seconds or so."""
   while True:
      print(" .")
      await asyncio.sleep(60)

async def ebb_and_flow():
   global options, queue

   await client.wait_until_ready()
   print(f"Received login callback.")

   if len(options["me"]) < 10:
      options["me"] = f"<@!{client.id}>"

   activity = discord.Activity(
      type=discord.ActivityType.listening,
      name="the soft waves"
   )
   await client.change_presence(
      status=discord.Status.online,
      activity=activity
   )

   await refresh_queue()

   while not client.is_closed():

      while len(queue) > options["atMost"]:
         await decide_to_delete(queue.popleft())

      if options["time"] != "inf":
         while len(queue) > options["atLeast"] \
         and (datetime.utcnow() - queue[0].created_at) > timedelta(minutes=options["time"]):
            await decide_to_delete(queue.popleft())
      else:
         pass

      #print(options) # debug
      await asyncio.sleep(5)

   print("Client closed?")

if __name__ == "__main__":
   client.loop.create_task(tik())
   client.loop.create_task(ebb_and_flow())
   client.run(os.environ["SWASHBOT_TOKEN"], bot=True)