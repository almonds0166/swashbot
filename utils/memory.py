from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Set, Union

from pathlib import Path
import sqlite3
from math import inf, isinf
import shutil
from datetime import datetime

@dataclass(frozen=True)
class Settings:
   at_least: float = inf
   at_most: float = inf
   minutes: float = inf

   def __iter__(self):
      yield from (
         self.at_least,
         self.at_most,
         self.minutes,
      )

   def __bool__(self):
      return not (
         self.at_least is inf and
         self.at_most is inf and
         self.minutes is inf
      )

   def replace(self, *,
      at_least: Optional[float]=None,
      at_most: Optional[float]=None,
      minutes: Optional[float]=None,
   ) -> Settings:
      return Settings(
         self.at_least if at_least is None else at_least,
         self.at_most if at_most is None else at_most,
         self.minutes if minutes is None else minutes,
      )

   def __str__(self):
      if isinf(self.at_least) or (isinf(self.at_most) and isinf(self.minutes)):
          return "No action taken."

      status = []
      if self.at_least == 0 and self.at_most == 0:
         status.append("Turbid! Delete all new messages immediately.")
         status.append("Wait, doesn't that mean this message will get deleted in a split second?")
      elif self.at_least == 0:
         if not isinf(self.at_most):
            status.append(f"Immediately delete all messages past count {self.at_most}.")
            status.append(f"Everything else takes {self.minutes} minute{'s' if self.minutes != 1 else ''} to wash away.")
         else:
            status.append(f"Messages take {self.minutes} minute{'s' if self.minutes != 1 else ''} to wash away.")
      elif self.at_least == self.at_most and not isinf(self.at_most):
         status.append(f"Immediately delete all messages past count {self.at_most}.")
      else:
         status.append(f"Always keep the {self.at_least} most recent message{'s' if self.at_least != 1 else ''}.")

         if not isinf(self.at_most):
            status.append(f"Delete all messages past count {self.at_most}.")
            if not isinf(self.minutes):
               status.append(f"Any messages in-between take {self.minutes} minute{'s' if self.minutes != 1 else ''} to wash away.")
         else:
            status.append(f"Any other messages take {self.minutes} minute{'s' if self.minutes != 1 else ''} to wash away.")

      return "\n".join(status)

@dataclass
class LongTermMemory:
   """Represents Swashbot's saved channel settings

   Args:
      file: Path to the SQLite database

   Attributes:
      file: Path to the SQLite database
      conn: sqlite3 connection
      guilds: Maps channel IDs to respective guild IDs
      channels: Maps guild IDs to a set of channel IDs
      settings: Maps channel IDs to respective `Settings` objects
   """
   file: Path
   conn: sqlite3.Connection = field(default_factory=lambda: sqlite3.connect(":memory:"))
   guilds: Dict[int, int] = field(default_factory=dict)
   channels: Dict[int, Set[int]] = field(default_factory=dict)
   settings: Dict[int, Settings] = field(default_factory=dict)

   def __post_init__(self):
      self.conn = sqlite3.connect(self.file)
      cursor = self.conn.cursor()

      cursor.execute("""
         CREATE TABLE IF NOT EXISTS memo (
            channel INTEGER PRIMARY KEY,
            guild INTEGER,
            at_least INTEGER,
            at_most INTEGER,
            minutes INTEGER
         );
      """)

      self.conn.commit()

      cursor.execute("""
         SELECT channel, guild, at_least, at_most, minutes
         FROM memo;
      """)

      rows = cursor.fetchall()
      for channel, guild, *row in rows:
         row = (
            inf if piece is None else piece
            for piece in row
         )
         settings = Settings(*row)
         if settings:
            self.settings[channel] = settings
            self.guilds[channel] = guild
            if not guild in self.channels:
               self.channels[guild] = set()
            self.channels[guild].add(channel)

   def load(self, channel: int) -> Settings:
      cursor = self.conn.cursor()

      cursor.execute("""
         SELECT guild, at_least, at_most, minutes
         FROM memo
         WHERE channel = ?;
      """, (channel,))

      row = cursor.fetchone()
      if row is None: return Settings()
      guild, *row = row

      row = (
         inf if piece is None else piece
         for piece in row
      )
      settings = Settings(*row)
      if settings:
         self.settings[channel] = settings
         self.guilds[channel] = guild
         if not guild in self.channels:
            self.channels[guild] = set()
         self.channels[guild].add(channel)

      return settings

   def save(self, channel: int, guild: int, settings: Settings) -> None:
      cursor = self.conn.cursor()

      if settings:
         # update to SQLite memory
         row = tuple(
            None if isinf(piece) else int(piece)
            for piece in settings
         )
         row = (channel, guild) + row

         cursor.execute("""
            INSERT OR REPLACE INTO memo (channel, guild, at_least, at_most, minutes)
            VALUES (?, ?, ?, ?, ?);
         """, row)

         self.conn.commit()

         # update to working memory
         self.settings[channel] = settings
         self.guilds[channel] = guild
         if not guild in self.channels:
            self.channels[guild] = set()
         self.channels[guild].add(channel)

      elif channel in self.settings:
         # remove from SQLite memory
         self.remove(channel)

   def remove(self, channel: int) -> None:
      """Erase settings for channel
      """
      cursor = self.conn.cursor()

      cursor.execute("""
         SELECT guild
         FROM memo
         WHERE channel = ?;
      """, (channel,))
      result = cursor.fetchone()
      if result is None: return
      guild, = result

      cursor.execute("""
         DELETE FROM memo
         WHERE channel = ?;
      """, (channel,))

      self.conn.commit()

      # remove from working memory
      del self.settings[channel]
      del self.guilds[channel]
      self.channels[guild].discard(channel)
      if not self.channels[guild]: del self.channels[guild]

   def backup(self, tag: Optional[str]=None) -> str:
      """Make a backup in the same directory as the database

      Args:
         tag: The note to append to the backup's filename. Default is a UTC timestamp.
      """
      parent = self.file.parent
      if tag is None: tag = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
      backup_file = f"{self.file.name}.{tag}"
      
      shutil.copy2(self.file, parent / backup_file)
      
      return backup_file