from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, PrivateAttr

from ..tvguide import ProgramDetails, ShowsCast


class Program(BaseModel):
    id: int
    name: str
    image: str
    start_timestamp: int
    end_timestamp: int
    color: int
    description: str
    day: str
    start_time: str
    end_time: str
    tags: List[str] = []

    _details: Optional[ProgramDetails] = PrivateAttr(default=None)
    _cast: Optional[ShowsCast] = PrivateAttr(default=None)
