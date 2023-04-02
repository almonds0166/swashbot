from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Generic, TypeVar

from datetime import datetime

import discord

@dataclass
class Message:
   """Simple node class for Deck
   """
   id: int
   created_at: datetime
   next: Optional[Message] = None
   prev: Optional[Message] = None

class Deck:
   """Double-ended queue (deque) of Discord messages
   
   Doubly linked list of messages, with a hash table that maps to the
   nodes within, in order to facilitate removals.
   """
   memo: dict[int, Message]
   oldest: Optional[Message] = None # top-most
   newest: Optional[Message] = None # bottom-most

   def __init__(self):
      self.memo = {}

   def __len__(self) -> int:
      return len(self.memo)

   def __bool__(self) -> bool:
      return bool(self.memo)

   def append_new(self, message: discord.Message) -> None:
      """Add a new _recent_ message to the deque
      """
      node = Message(message.id, message.created_at)

      if self.newest is not None:
         node.prev = self.newest
         self.newest.next = node

      self.newest = node

      if self.oldest is None:
         self.oldest = node

      self.memo[message.id] = node

   def append_old(self, message: discord.Message) -> None:
      """Add a new _old_ message to the deque
      """
      node = Message(message.id, message.created_at)

      if self.oldest is not None:
         node.next = self.oldest
         self.oldest.prev = node

      self.oldest = node

      if self.newest is None:
         self.newest = node

      self.memo[message.id] = node

   def remove(self, id: int) -> None:
      """Remove a message from the deque by it's ID

      Raises:
         KeyError: if id isn't in this deque
      """
      node = self.memo[id]

      if node.prev is None and node.next is None:
         self.clear()
         return

      if node.prev is None:
         assert node.next is not None
         node.next.prev = None
         self.oldest = node.next
      elif node.next is None:
         node.prev.next = None
         self.newest = node.prev
      else:
         node.prev.next = node.next
         node.next.prev = node.prev

      del self.memo[id]

   def pop_oldest(self) -> int:
      """Removes oldest message from the deque

      Raises:
         IndexError: if there are no messages in this deque

      Returns:
         int: The stored message id
      """
      if self.oldest is None:
         raise IndexError("no messages in Deck")

      id = self.oldest.id
      self.remove(id)
      return id

   def pop_newest(self) -> int:
      """Removes newest message from the deque

      Raises:
         IndexError: if there are no messages in this deque

      Returns:
         int: The stored message id
      """
      if self.newest is None:
         raise IndexError("no messages in Deck")
         
      id = self.newest.id
      self.remove(id)
      return id

   def clear(self) -> None:
      self.oldest = None
      self.newest = None
      self.memo = {}