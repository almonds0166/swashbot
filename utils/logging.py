import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Union, Dict, Any

import discord
import discord.utils

class TaskTracker:
   """Generates labels for tasks, to help with logging

   Todo:
      Potential ``async with`` syntax?
   """
   task: int = 0

   def __init__(self, digits: int=5):
      self.digits = digits
      self.format = f"@{{:0{digits}x}}"

   def __call__(self) -> str:
      self.task += 1
      return self.format.format(self.task)

def build_logging_setup(filename: Union[str, Path],
   file_count: int=7,
   when: str="midnight",
   interval: int=1,
   *,
   stdout: bool=True,
   date_format: str="%Y-%m-%d %H:%M:%S",
   swashbot_log_level: int=logging.DEBUG,
   discord_log_level: int=logging.DEBUG,
   http_log_level: int=logging.INFO,
) -> Optional[Dict[str, Any]]:
   """Customize the logger

   Default is the last week's worth of logs, where each day of the week gets
   its own log file.

   Args:
      filename: log file base name
      file_count: number of log files to rotate through
      when: see `TimedRotatingFileHandler`_ for more details
      interval:  see `TimedRotatingFileHandler`_ for more details

   Keyword args:
      stdout: whether to print the log info to stdout too
      date_format: log entry date format
      discord_log_level: log level for the discord module
      http_log_level: log level for the discord.http module
   
   .. _TimedRotatingFileHandler: https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler
   """
   if not (filename or stdout): return None

   swashbot_logger = logging.getLogger("swashbot")
   discord_logger = logging.getLogger("discord")
   http_logger = logging.getLogger("discord.http")

   swashbot_logger.setLevel(swashbot_log_level)
   discord_logger.setLevel(discord_log_level)
   http_logger.setLevel(http_log_level)

   formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", date_format, style='{')

   null_handler = logging.NullHandler()

   console_handler = None
   if stdout:
      console_handler = logging.StreamHandler()
      if discord.utils.stream_supports_colour(console_handler.stream):
         console_formatter = discord.utils._ColourFormatter()
      else:
         console_formatter = formatter
      console_handler.setFormatter(console_formatter)
      swashbot_logger.addHandler(console_handler)
      discord_logger.addHandler(console_handler)

   file_handler = None
   if filename:
      file_handler = logging.handlers.TimedRotatingFileHandler(
         filename=filename,
         encoding="utf-8",
         backupCount=file_count,
         utc=True,
      )
      file_handler.setFormatter(formatter)
      swashbot_logger.addHandler(file_handler)
      discord_logger.addHandler(file_handler)

   return {
      "handler": file_handler or console_handler or null_handler,
      "formatter": formatter,
      "level": logging.INFO,
      "root": True,
   }