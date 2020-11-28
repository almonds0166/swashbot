
import sqlite3

def load_memory(client, file):
   conn = sqlite3.connect(file)
   c = conn.cursor()

   c.execute(
      """
      CREATE TABLE IF NOT EXISTS prefixes (
         guild INTEGER PRIMARY KEY,
         prefix TEXT
      );
      """
   )

   c.execute(
      """
      SELECT * FROM prefixes;
      """
   )
   for gid, prefix in c.fetchall():
      client.prefixes[gid] = prefix

   c.execute(
      """
      CREATE TABLE IF NOT EXISTS memo (
         channel INTEGER PRIMARY KEY,
         guild INTEGER,
         at_least INTEGER,
         at_most INTEGER,
         time_ INTEGER
      );
      """
   )

   c.execute(
      """
      SELECT * FROM memo;
      """
   )
   for cid, gid, at_least, at_most, time in c.fetchall():
      client.all_channels.add(cid)
      client.all_guilds.add(gid)
      client.memo[cid] = Settings(at_least, at_most, time)

   conn.commit()

   for cid in client.memo:
      client.loop.create_task(client.swash(cid, Context()))

# channel settings
class Settings:
   def __init__(self, at_least=0, at_most=None, time=None):
      self.at_least = at_least
      self.at_most  = at_most
      self.time     = time

   def __copy__(self):
      return Settings(self.at_least, self.at_most, self.time)

   def copy(self):
      return self.__copy__() # not sure why the above method isn't working

# Discord context
class Context:
   def __init__(self, **kwargs):
      self.msg     = kwargs.get("msg", None)
      self.channel = kwargs.get("channel", None)
      self.guild   = kwargs.get("guild", None)

class Msg:
   """
   Simple node class for doubly linked list Flotsam class below

   id is the message id
   t is the timestamp the message was created at
   prev is the next message older in time
   next is the next message newer in time
   """
   def __init__(self, mid, timestamp):
      """
      mid is the id of the message (int)
      timestamp is when the message was created (tz naive datetime.datetime in UTC)
      """
      self.id = mid
      self.t = timestamp
      self.prev = None
      self.next = None

class Flotsam(object):
   """
   Doubly linked list of messages, with a hash table that maps to the
   nodes inside in order to facilitate removals.
   """
   def __init__(self):
      self.memo = {}
      self.oldest = None # top-most
      self.newest = None # bottom-most

   @property
   def size(self):
      return len(self.memo)

   def append_new(self, msg):
      """
      Add new recent message to the Flotsam
      msg is a Discord message object
      """
      m = Msg(msg.id, msg.created_at)
      if self.newest is not None:
         m.prev = self.newest
         self.newest.next = m
      self.newest = m
      if self.oldest is None:
         self.oldest = m
      self.memo[msg.id] = m

   def append_old(self, msg):
      """
      Add new oldest message to the Flotsam
      msg is a Discord message object
      """
      m = Msg(msg.id, msg.created_at)
      if self.oldest is not None:
         m.next = self.oldest
         self.oldest.prev = m
      self.oldest = m
      if self.newest is None:
         self.newest = m
      self.memo[msg.id] = m

   def remove(self, mid): # expected O(1)
      m = self.memo[mid] # will throw KeyError if mid isn't in this table

      if m.prev is None and m.next is None:
         return self.clear()

      if m.prev is None:
         m.next.prev = None
         self.oldest = m.next
      elif m.next is None:
         m.prev.next = None
         self.newest = m.prev
      else:
         m.prev.next = m.next
         m.next.prev = m.prev

      del self.memo[mid]

   def pop_oldest(self):
      """
      Returns stored message id
      """
      mid = self.oldest.id
      self.remove(mid)
      return mid

   def pop_newest(self):
      mid = self.newest.id
      self.remove(mid)
      return mid

   def clear(self):
      self.oldest = None
      self.newest = None
      self.memo = {}