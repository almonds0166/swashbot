
import logging
import traceback
import os
import random

import discord
import asyncio
import aiohttp

from swashbot.config import DEBUG_LOG, WEBHOOK

logging.basicConfig(
   handlers=[logging.FileHandler(DEBUG_LOG, "w", "utf-8")], # can be updated in 3.9
   level=logging.DEBUG,
   format="[ %(asctime)s | %(levelname)s ] %(message)s",
   datefmt="%Y-%m-%d %H:%M:%S"
)
loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
for logger in loggers:
   #print(logger)
   logger.setLevel(logging.ERROR)

async def post_to_webhook(content, embed=None):
   """
   Returns response code
   """
   if not WEBHOOK: return -1

   params = {"content": content}
   if embed is not None:
      params["embeds"] = [{"description": embed}]

   async with aiohttp.ClientSession() as session:
      async with session.post(WEBHOOK, json=params) as resp:
         return resp.status

async def debug(msg, webhook=False):
   """
   Detailed information, helpful for keeping track of bugs
   """
   print(f"{msg}", flush=True)
   logging.debug(f"{msg}")
   if webhook:
      content = f"**Debug info**: [{msg}]"
      response_code = await post_to_webhook(content)
      tmp = f"Received {response_code} when posting debug info to webhook."
      if response_code == 200:
         logging.info(tmp)
      else:
         logging.error(tmp)

async def info(msg, webhook=False):
   """
   Things are working as expected
   """
   print(f"{msg}", flush=True)
   logging.info(f"{msg}")
   if webhook:
      content = f"**Info**: [{msg}]"
      response_code = await post_to_webhook(content)
      tmp = f"Received {response_code} when posting info to webhook."
      if response_code == 200:
         logging.info(tmp)
      else:
         logging.error(tmp)

async def warn(msg, webhook=True):
   """
   Something unexpected happened
   """
   print(f"{msg}", flush=True)
   logging.warning(f"{msg}")
   if webhook:
      content = f"**Warning**: [{msg}]"
      response_code = await post_to_webhook(content)
      tmp = f"Received {response_code} when posting warning to webhook."
      if response_code == 200:
         logging.info(tmp)
      else:
         logging.error(tmp)

async def error(msg, webhook=True):
   """
   The program was not able to perform its operation(s) as expected
   """
   print(f"{msg}", flush=True)
   logging.error(f"{msg}")
   if webhook:
      content = f"**Error**: [{msg}]"
      response_code = await post_to_webhook(content)
      tmp = f"Received {response_code} when posting error to webhook."
      if response_code == 200:
         logging.info(tmp)
      else:
         logging.error(tmp)