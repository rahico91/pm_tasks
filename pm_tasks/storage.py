from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .models import Priority, Status, Task


def _data_dir() -> Path:
    d = Path.home() / ".pm-tasks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _tasks_file() -> Path:
    return _data_dir() / "tasks.json"


def _task_to_dict(t: Task) -> dict[str, Any]:
    return {
        "id":         t.id,
        "title":      t.title,
        "status":     t.status.value,
        "priority":   t.priority.value,
        "due_date":   t.due_date.isoformat() if t.due_date else None,
        "created_at": t.created_at.isoformat(),
        "project":    t.project,
    }


def _dict_to_task(d: dict[str, Any]) -> Task:
    return Task(
        id         = d["id"],
        title      = d["title"],
        status     = Status(d["status"]),
        priority   = Priority(d["priority"]),
        due_date   = date.fromisoformat(d["due_date"]) if d.get("due_date") else None,
        created_at = datetime.fromisoformat(d["created_at"]),
        project    = d.get("project"),
    )


def load_tasks() -> list[Task]:
    path = _tasks_file()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [_dict_to_task(r) for r in json.load(fh)]


def save_tasks(tasks: list[Task]) -> None:
    with _tasks_file().open("w", encoding="utf-8") as fh:
        json.dump([_task_to_dict(t) for t in tasks], fh, indent=2)
