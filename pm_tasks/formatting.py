from __future__ import annotations

import click

from .models import Priority, Status, Task

PRIORITY_COLORS: dict[Priority, tuple[str, bool]] = {
    Priority.P0: ("red",    True),
    Priority.P1: ("yellow", True),
    Priority.P2: ("cyan",   False),
    Priority.P3: ("white",  False),
}

STATUS_COLORS: dict[Status, str] = {
    Status.TODO:        "white",
    Status.IN_PROGRESS: "blue",
    Status.DONE:        "green",
}


def _priority_badge(p: Priority) -> str:
    fg, bold = PRIORITY_COLORS[p]
    return click.style(f"[{p.value.upper()}]", fg=fg, bold=bold)


def _status_badge(s: Status) -> str:
    label = s.value.upper().replace("_", " ")
    return click.style(f"{label:<11}", fg=STATUS_COLORS[s])


def _overdue_tag(t: Task) -> str:
    return click.style(" OVERDUE", fg="red", bold=True) if t.is_overdue() else ""


def print_task_table(tasks: list[Task]) -> None:
    if not tasks:
        click.echo(click.style("  No tasks found.", fg="yellow"))
        return

    header = (
        click.style("ID      ", bold=True) + "  " +
        click.style("PRIO  ", bold=True)   + "  " +
        click.style("STATUS       ", bold=True) + "  " +
        click.style("PROJECT      ", bold=True) + "  " +
        click.style("DUE        ", bold=True)   + "  " +
        click.style("TITLE", bold=True)
    )
    click.echo(header)
    click.echo(click.style("─" * 90, fg="bright_black"))

    for t in tasks:
        short_id = t.id[:8]
        due_str  = t.due_date.isoformat() if t.due_date else "—"
        project  = (t.project or "—")[:12]
        title    = t.title[:45] + _overdue_tag(t)

        click.echo(
            f"{short_id}  "
            f"{_priority_badge(t.priority):<4}  "
            f"{_status_badge(t.status)}  "
            f"{project:<12}  "
            f"{due_str:<10}  "
            f"{title}"
        )


def print_task_single(t: Task) -> None:
    click.echo(f"  id       : {click.style(t.id, fg='bright_black')}")
    click.echo(f"  title    : {t.title}")
    click.echo(f"  status   : {_status_badge(t.status)}")
    click.echo(f"  priority : {_priority_badge(t.priority)}")
    click.echo(f"  project  : {t.project or '—'}")
    click.echo(f"  due      : {t.due_date.isoformat() if t.due_date else '—'}")
    click.echo(f"  created  : {t.created_at.strftime('%Y-%m-%d %H:%M')}")
    if t.is_overdue():
        click.echo(click.style("  ** OVERDUE **", fg="red", bold=True))
