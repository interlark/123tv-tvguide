from dataclasses import dataclass, field
from typing import Optional

import xmltv.models


@dataclass
class Programme(xmltv.models.Programme):
    live: Optional[object] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
