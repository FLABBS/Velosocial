from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    name: str
    description: str
    contacts: str
    lat: Optional[float] = None
    lon: Optional[float] = None

@dataclass
class Event:
    id: int
    creator_id: int
    route: str
    date: str
    chat_link: str
