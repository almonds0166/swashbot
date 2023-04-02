from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Set

from pathlib import Path
import sqlite3
from math import inf, isinf

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

@dataclass
class LongTermMemory:
   """Represents Swashbot's saved channel settings

   Args:
      file: Path to the SQLite database

   Attributes:
      file: Path to the SQLite database
      conn: sqlite3 connection
      guilds: Maps guild IDs to a set of channel IDs with saved settings
      channels: Maps channel IDs to its settings
   """
   file: Path
   conn: sqlite3.Connection = field(default_factory=lambda: sqlite3.connect(":memory:"))
   guilds: Dict[int, Set[int]] = field(default_factory=dict)
   channels: Dict[int, Settings] = field(default_factory=dict)

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
            self.channels[channel] = settings
            if guild not in self.guilds: self.guilds[guild] = set()
            self.guilds[guild].add(channel)

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
         self.channels[channel] = settings
         if guild not in self.guilds: self.guilds[guild] = set()
         self.guilds[guild].add(channel)

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
         self.channels[channel] = settings
         if guild not in self.guilds: self.guilds[guild] = set()
         self.guilds[guild].add(channel)

      elif channel in self.channels:
         # remove from SQLite memory
         cursor.execute("""
            DELETE FROM memo
            WHERE channel = ?;
         """, (channel,))

         self.conn.commit()

         # remove from working memory
         del self.channels[channel]
         if guild in self.guilds:
            self.guilds[guild].discard(channel)
            if not self.guilds[guild]:
               del self.guilds[guild]