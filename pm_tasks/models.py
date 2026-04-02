from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from uuid import uuid4


class Status(str, Enum):
    TODO        = "todo"
    IN_PROGRESS = "in_progress"
    DONE        = "done"


class Priority(str, Enum):
    P0 = "p0"  # highest urgency
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"  # lowest urgency

    @property
    def ordinal(self) -> int:
        """Lower ordinal = higher urgency. Used for sorting."""
        return int(self.value[1])


@dataclass
class Task:
    title:      str
    id:         str          = field(default_factory=lambda: str(uuid4()))
    status:     Status       = Status.TODO
    priority:   Priority     = Priority.P2
    due_date:   date | None  = None
    created_at: datetime     = field(default_factory=datetime.now)
    project:    str | None   = None

    def is_overdue(self) -> bool:
        return (
            self.due_date is not None
            and self.due_date < date.today()
            and self.status is not Status.DONE
        )

    def matches_prefix(self, prefix: str) -> bool:
        """Case-insensitive title prefix match."""
        return self.title.lower().startswith(prefix.lower())
