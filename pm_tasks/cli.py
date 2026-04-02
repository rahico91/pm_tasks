from __future__ import annotations

import sys

import click

from .models import Priority, Status, Task
from .storage import load_tasks, save_tasks
from .formatting import print_task_single, print_task_table


# ── Entry group ───────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="0.1.0", prog_name="pm-tasks")
def cli() -> None:
    """pm-tasks — a lightweight project task manager."""


# ── Shared helper ─────────────────────────────────────────────────────────────

def _resolve_task(tasks: list[Task], identifier: str) -> Task | None:
    """
    Resolve an identifier to a single Task.

    Resolution order:
      1. UUID prefix match  (first N characters of id)
      2. Case-insensitive title prefix match

    Raises click.UsageError if the match is ambiguous.
    Returns None if nothing matches.
    """
    id_matches = [t for t in tasks if t.id.startswith(identifier)]
    if len(id_matches) == 1:
        return id_matches[0]
    if len(id_matches) > 1:
        raise click.UsageError(
            f"Ambiguous ID prefix {identifier!r} — matches {len(id_matches)} tasks. "
            "Use more characters."
        )

    title_matches = [t for t in tasks if t.matches_prefix(identifier)]
    if len(title_matches) == 1:
        return title_matches[0]
    if len(title_matches) > 1:
        raise click.UsageError(
            f"Ambiguous title prefix {identifier!r} — matches:\n"
            + "\n".join(f"  · {t.title!r}  ({t.id[:8]})" for t in title_matches)
        )

    return None


# ── Commands ──────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("title")
@click.option(
    "--priority", "-p",
    type=click.Choice([p.value for p in Priority], case_sensitive=False),
    default=Priority.P2.value,
    show_default=True,
    help="Priority: p0 (highest) … p3 (lowest).",
)
@click.option(
    "--due", "-d",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Due date (YYYY-MM-DD).",
)
@click.option(
    "--project", "-P",
    default=None,
    help="Project name to classify this task.",
)
def add(title: str, priority: str, due, project: str | None) -> None:
    """Add a new task."""
    tasks = load_tasks()
    t = Task(
        title    = title,
        priority = Priority(priority.lower()),
        due_date = due.date() if due else None,
        project  = project,
    )
    tasks.append(t)
    save_tasks(tasks)
    click.echo(click.style("Task added:", fg="green", bold=True))
    print_task_single(t)


@cli.command(name="list")
@click.option("--project", "-P", default=None, help="Filter by project name.")
@click.option(
    "--status", "-s",
    type=click.Choice([s.value for s in Status], case_sensitive=False),
    default=None,
    help="Filter by status.",
)
@click.option(
    "--priority", "-p",
    type=click.Choice([p.value for p in Priority], case_sensitive=False),
    default=None,
    help="Filter by priority.",
)
@click.option("--overdue", is_flag=True, default=False, help="Show only overdue tasks.")
@click.option(
    "--sort-by",
    type=click.Choice(["priority", "due", "created", "status"]),
    default="priority",
    show_default=True,
    help="Sort column.",
)
def list_tasks(project, status, priority, overdue, sort_by) -> None:
    """List tasks with optional filters."""
    tasks = load_tasks()

    if project:
        tasks = [t for t in tasks if t.project and t.project.lower() == project.lower()]
    if status:
        tasks = [t for t in tasks if t.status.value == status.lower()]
    if priority:
        tasks = [t for t in tasks if t.priority.value == priority.lower()]
    if overdue:
        tasks = [t for t in tasks if t.is_overdue()]

    if sort_by == "priority":
        tasks.sort(key=lambda t: t.priority.ordinal)
    elif sort_by == "due":
        tasks.sort(key=lambda t: (t.due_date is None, t.due_date))
    elif sort_by == "created":
        tasks.sort(key=lambda t: t.created_at)
    elif sort_by == "status":
        _order = {Status.IN_PROGRESS: 0, Status.TODO: 1, Status.DONE: 2}
        tasks.sort(key=lambda t: _order[t.status])

    count = click.style(str(len(tasks)), bold=True)
    click.echo(f"\n  Showing {count} task(s)\n")
    print_task_table(tasks)
    click.echo()


@cli.command()
@click.argument("identifier")
def complete(identifier: str) -> None:
    """Mark a task as done.

    IDENTIFIER is a task ID prefix or title prefix.
    """
    tasks = load_tasks()
    matched = _resolve_task(tasks, identifier)

    if matched is None:
        click.echo(click.style(f"No task found matching: {identifier!r}", fg="red"), err=True)
        sys.exit(1)

    if matched.status is Status.DONE:
        click.echo(click.style(f"Already done: {matched.title!r}", fg="yellow"))
        return

    matched.status = Status.DONE
    save_tasks(tasks)
    click.echo(click.style(f"Completed: {matched.title}", fg="green", bold=True))


@cli.command()
@click.argument("identifier")
@click.argument(
    "new_priority",
    type=click.Choice([p.value for p in Priority], case_sensitive=False),
)
def prioritize(identifier: str, new_priority: str) -> None:
    """Change the priority of a task.

    IDENTIFIER is a task ID prefix or title prefix.
    NEW_PRIORITY is one of: p0, p1, p2, p3.
    """
    tasks = load_tasks()
    matched = _resolve_task(tasks, identifier)

    if matched is None:
        click.echo(click.style(f"No task found matching: {identifier!r}", fg="red"), err=True)
        sys.exit(1)

    old_p = matched.priority
    matched.priority = Priority(new_priority.lower())
    save_tasks(tasks)
    click.echo(
        f"Updated {click.style(matched.title, bold=True)}: "
        f"{click.style(old_p.value, fg='bright_black')} → "
        f"{click.style(matched.priority.value, fg='cyan', bold=True)}"
    )
