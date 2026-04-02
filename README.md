# pm-tasks

A lightweight CLI task manager for project work, built with Python and Click.
Tasks are stored locally in `~/.pm-tasks/tasks.json`.

## Features

- Add tasks with priority (P0–P3), due date, and project label
- List and filter by status, priority, project, or overdue
- Mark tasks complete or re-prioritize by title prefix or ID
- Colored output via [Rich](https://github.com/Textualize/rich)
- Fully tested with pytest (36 tests)

## Installation

**Requirements:** Python 3.10+

```bash
git clone https://github.com/rahico91/pm_tasks.git
cd pm_tasks
pip install -e .
```

This registers the `pm-tasks` entry point. If your Python bin directory is on `PATH`, you can run `pm-tasks` directly. Otherwise use:

```bash
python3 -m pm_tasks <command>
```

### Dependencies only (no install)

```bash
pip install click rich
python3 -m pm_tasks --help
```

---

## Usage

### `add` — Create a task

```bash
pm-tasks add TITLE [--priority p0|p1|p2|p3] [--due YYYY-MM-DD] [--project NAME]
```

```bash
# Minimal
pm-tasks add "Fix login bug"

# Full options
pm-tasks add "Deploy hotfix" --priority p0 --due 2026-04-10 --project backend

# Short flags
pm-tasks add "Write tests" -p p1 -d 2026-05-01 -P backend
```

**Priority levels:**

| Level | Meaning |
|-------|---------|
| `p0`  | Critical — must do now |
| `p1`  | High |
| `p2`  | Medium (default) |
| `p3`  | Low |

---

### `list` — Show tasks

```bash
pm-tasks list [--project NAME] [--status STATUS] [--priority LEVEL]
              [--overdue] [--sort-by priority|due|created|status]
```

```bash
# All tasks, sorted by priority (default)
pm-tasks list

# Filter by project
pm-tasks list --project backend

# Filter by status
pm-tasks list --status todo
pm-tasks list --status in_progress
pm-tasks list --status done

# Filter by priority
pm-tasks list --priority p0

# Show only overdue tasks
pm-tasks list --overdue

# Sort by due date
pm-tasks list --sort-by due

# Combine filters
pm-tasks list --project backend --status todo --sort-by due
```

---

### `complete` — Mark a task as done

```bash
pm-tasks complete IDENTIFIER
```

`IDENTIFIER` can be a **title prefix** or an **ID prefix** (first N characters shown in `list`):

```bash
pm-tasks complete "Fix login"       # title prefix
pm-tasks complete a1b2c3d4          # ID prefix
```

---

### `prioritize` — Change a task's priority

```bash
pm-tasks prioritize IDENTIFIER NEW_PRIORITY
```

```bash
pm-tasks prioritize "Write tests" p0
pm-tasks prioritize a1b2c3d4 p3
```

---

## Data model

Each task has the following fields:

| Field | Type | Default |
|-------|------|---------|
| `id` | UUID string | auto-generated |
| `title` | string | required |
| `status` | `todo` / `in_progress` / `done` | `todo` |
| `priority` | `p0` / `p1` / `p2` / `p3` | `p2` |
| `due_date` | `YYYY-MM-DD` or `null` | `null` |
| `created_at` | ISO 8601 datetime | auto-generated |
| `project` | string or `null` | `null` |

Tasks are saved to `~/.pm-tasks/tasks.json`.

---

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Project structure

```
pm_tasks/
├── pm_tasks/
│   ├── __init__.py       # version
│   ├── models.py         # Task dataclass, Status and Priority enums
│   ├── storage.py        # JSON load/save (~/.pm-tasks/tasks.json)
│   ├── formatting.py     # Rich table and color output
│   └── cli.py            # Click commands: add, list, complete, prioritize
├── tests/
│   └── test_tasks.py     # 36 pytest tests
└── pyproject.toml
```
