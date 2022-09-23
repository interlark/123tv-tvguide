from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, NonNegativeInt
from xmltv.models import Credits, Actor


# class Image(BaseModel):
#     id: str
#     width: int
#     height: int
#     bucketType: str
#     bucketPath: Optional[str]


class Item(BaseModel):
    id: int
    name: str
    role: Optional[str]
    type: str
    # image: Optional[Image] = None


class ShowsCastXMLTVOptions(BaseModel):
    """Options purposed to control number of cast
    per type presented in target xmltv credits."""
    actor: NonNegativeInt = 15
    director: NonNegativeInt = 1
    writer: NonNegativeInt = 1
    adapter: NonNegativeInt = 1
    producer: NonNegativeInt = 1
    composer: NonNegativeInt = 1
    editor: NonNegativeInt = 1
    presenter: NonNegativeInt = 3
    commentator: NonNegativeInt = 2
    guest: NonNegativeInt = 3

    def take_one(self, type_name):
        if not hasattr(self, type_name):
            return False

        allowed_positions = getattr(self, type_name)
        if allowed_positions > 0:
            setattr(self, type_name, allowed_positions - 1)
            return True

        return False


class ShowsCast(BaseModel):
    id: str
    items: List[Item]

    def add_cast(self, xmltv_program, **options):
        """Add cast & crew to xmltv program.

        Example:
            add_cast(xmltv_program, actor=99, director=1, adapter=0)
        """
        staff_list = []
        xmltv_options = ShowsCastXMLTVOptions(**options)

        for person in self.items:
            type_name = person.type.lower()
            if xmltv_options.take_one(type_name):
                staff_list.append((type_name, person.name, person.role))

        if staff_list:
            credits = Credits()
            for type_name, person_name, person_role in staff_list:
                if type_name != 'actor':
                    getattr(credits, type_name).append(person_name)
                else:
                    credits.actor = Actor(content=[person_name], role=person_role)

            xmltv_program.credits = credits
