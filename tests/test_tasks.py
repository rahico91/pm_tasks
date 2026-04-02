from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from pm_tasks.models import Priority, Status, Task
from pm_tasks.storage import _dict_to_task, _task_to_dict, load_tasks, save_tasks


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_tasks_file(tmp_path, monkeypatch):
    """Redirect storage to a temp file so tests never touch ~/.pm-tasks."""
    tasks_file = tmp_path / "tasks.json"

    monkeypatch.setattr("pm_tasks.storage._tasks_file", lambda: tasks_file)
    return tasks_file


@pytest.fixture
def sample_task():
    return Task(
        title    = "Fix login bug",
        priority = Priority.P0,
        project  = "backend",
        due_date = date.today() + timedelta(days=7),
    )


@pytest.fixture
def overdue_task():
    return Task(
        title    = "Overdue task",
        priority = Priority.P1,
        due_date = date.today() - timedelta(days=1),
    )


# ── Model: Task creation ──────────────────────────────────────────────────────

class TestTaskCreation:
    def test_defaults(self):
        t = Task("My task")
        assert t.title == "My task"
        assert t.status is Status.TODO
        assert t.priority is Priority.P2
        assert t.due_date is None
        assert t.project is None
        assert len(t.id) == 36  # UUID format

    def test_unique_ids(self):
        ids = {Task("t").id for _ in range(100)}
        assert len(ids) == 100

    def test_custom_fields(self):
        t = Task(
            title    = "Deploy",
            status   = Status.IN_PROGRESS,
            priority = Priority.P1,
            due_date = date(2026, 6, 1),
            project  = "infra",
        )
        assert t.status is Status.IN_PROGRESS
        assert t.priority is Priority.P1
        assert t.due_date == date(2026, 6, 1)
        assert t.project == "infra"

    def test_created_at_is_set(self):
        before = datetime.now()
        t = Task("Check created_at")
        after = datetime.now()
        assert before <= t.created_at <= after


# ── Model: is_overdue ─────────────────────────────────────────────────────────

class TestIsOverdue:
    def test_past_due_todo_is_overdue(self, overdue_task):
        assert overdue_task.is_overdue() is True

    def test_future_due_not_overdue(self, sample_task):
        assert sample_task.is_overdue() is False

    def test_no_due_date_not_overdue(self):
        t = Task("No due date")
        assert t.is_overdue() is False

    def test_done_task_never_overdue(self, overdue_task):
        overdue_task.status = Status.DONE
        assert overdue_task.is_overdue() is False

    def test_due_today_not_overdue(self):
        t = Task("Due today", due_date=date.today())
        assert t.is_overdue() is False


# ── Model: matches_prefix ─────────────────────────────────────────────────────

class TestMatchesPrefix:
    def test_exact_match(self, sample_task):
        assert sample_task.matches_prefix("Fix login bug") is True

    def test_prefix_match(self, sample_task):
        assert sample_task.matches_prefix("Fix") is True

    def test_case_insensitive(self, sample_task):
        assert sample_task.matches_prefix("fix login") is True
        assert sample_task.matches_prefix("FIX") is True

    def test_no_match(self, sample_task):
        assert sample_task.matches_prefix("Deploy") is False

    def test_empty_prefix_matches_all(self, sample_task):
        assert sample_task.matches_prefix("") is True


# ── Model: Priority ordering ──────────────────────────────────────────────────

class TestPriorityOrdinal:
    def test_p0_highest(self):
        assert Priority.P0.ordinal == 0

    def test_ordinal_order(self):
        assert Priority.P0.ordinal < Priority.P1.ordinal
        assert Priority.P1.ordinal < Priority.P2.ordinal
        assert Priority.P2.ordinal < Priority.P3.ordinal

    def test_sort_by_ordinal(self):
        tasks = [
            Task("C", priority=Priority.P3),
            Task("A", priority=Priority.P0),
            Task("B", priority=Priority.P1),
        ]
        tasks.sort(key=lambda t: t.priority.ordinal)
        assert [t.title for t in tasks] == ["A", "B", "C"]


# ── Storage: serialization round-trip ────────────────────────────────────────

class TestSerialization:
    def test_round_trip_full(self, sample_task):
        restored = _dict_to_task(_task_to_dict(sample_task))
        assert restored.id         == sample_task.id
        assert restored.title      == sample_task.title
        assert restored.status     == sample_task.status
        assert restored.priority   == sample_task.priority
        assert restored.due_date   == sample_task.due_date
        assert restored.project    == sample_task.project
        assert restored.created_at == sample_task.created_at

    def test_round_trip_no_due_date(self):
        t = Task("No due")
        assert _dict_to_task(_task_to_dict(t)).due_date is None

    def test_round_trip_no_project(self):
        t = Task("No project")
        assert _dict_to_task(_task_to_dict(t)).project is None

    def test_dict_keys(self, sample_task):
        d = _task_to_dict(sample_task)
        assert set(d) == {"id", "title", "status", "priority", "due_date", "created_at", "project"}

    def test_dict_values_are_strings(self, sample_task):
        d = _task_to_dict(sample_task)
        assert isinstance(d["status"], str)
        assert isinstance(d["priority"], str)
        assert isinstance(d["due_date"], str)
        assert isinstance(d["created_at"], str)


# ── Storage: load / save ──────────────────────────────────────────────────────

class TestLoadSave:
    def test_save_and_load(self, tmp_tasks_file, sample_task):
        save_tasks([sample_task])
        loaded = load_tasks()
        assert len(loaded) == 1
        assert loaded[0].id == sample_task.id
        assert loaded[0].title == sample_task.title

    def test_load_empty_when_no_file(self, tmp_tasks_file):
        assert load_tasks() == []

    def test_save_multiple_tasks(self, tmp_tasks_file):
        tasks = [Task(f"Task {i}") for i in range(5)]
        save_tasks(tasks)
        loaded = load_tasks()
        assert len(loaded) == 5
        assert [t.title for t in loaded] == [t.title for t in tasks]

    def test_save_overwrites(self, tmp_tasks_file, sample_task):
        save_tasks([sample_task])
        new_task = Task("Replacement")
        save_tasks([new_task])
        loaded = load_tasks()
        assert len(loaded) == 1
        assert loaded[0].title == "Replacement"

    def test_persisted_as_valid_json(self, tmp_tasks_file, sample_task):
        save_tasks([sample_task])
        raw = json.loads(tmp_tasks_file.read_text())
        assert isinstance(raw, list)
        assert raw[0]["title"] == sample_task.title

    def test_save_empty_list(self, tmp_tasks_file):
        save_tasks([Task("temp")])
        save_tasks([])
        assert load_tasks() == []


# ── CRUD operations ───────────────────────────────────────────────────────────

class TestCRUD:
    def test_create(self, tmp_tasks_file):
        tasks = load_tasks()
        t = Task("New task", priority=Priority.P1, project="web")
        tasks.append(t)
        save_tasks(tasks)

        loaded = load_tasks()
        assert len(loaded) == 1
        assert loaded[0].title == "New task"
        assert loaded[0].priority is Priority.P1

    def test_read_by_id(self, tmp_tasks_file):
        tasks = [Task("Alpha"), Task("Beta"), Task("Gamma")]
        save_tasks(tasks)

        loaded = load_tasks()
        target_id = tasks[1].id
        found = next((t for t in loaded if t.id == target_id), None)
        assert found is not None
        assert found.title == "Beta"

    def test_update_status(self, tmp_tasks_file, sample_task):
        save_tasks([sample_task])

        tasks = load_tasks()
        tasks[0].status = Status.DONE
        save_tasks(tasks)

        assert load_tasks()[0].status is Status.DONE

    def test_update_priority(self, tmp_tasks_file, sample_task):
        save_tasks([sample_task])

        tasks = load_tasks()
        tasks[0].priority = Priority.P3
        save_tasks(tasks)

        assert load_tasks()[0].priority is Priority.P3

    def test_delete(self, tmp_tasks_file):
        tasks = [Task("Keep"), Task("Delete me"), Task("Keep too")]
        save_tasks(tasks)
        delete_id = tasks[1].id

        remaining = [t for t in load_tasks() if t.id != delete_id]
        save_tasks(remaining)

        loaded = load_tasks()
        assert len(loaded) == 2
        assert all(t.id != delete_id for t in loaded)

    def test_delete_all(self, tmp_tasks_file):
        save_tasks([Task("A"), Task("B")])
        save_tasks([])
        assert load_tasks() == []

    def test_filter_by_status(self, tmp_tasks_file):
        tasks = [
            Task("Todo 1"),
            Task("Todo 2"),
            Task("Done 1", status=Status.DONE),
        ]
        save_tasks(tasks)

        todos = [t for t in load_tasks() if t.status is Status.TODO]
        assert len(todos) == 2

    def test_filter_by_project(self, tmp_tasks_file):
        tasks = [
            Task("A", project="backend"),
            Task("B", project="frontend"),
            Task("C", project="backend"),
        ]
        save_tasks(tasks)

        backend = [t for t in load_tasks() if t.project == "backend"]
        assert len(backend) == 2
        assert all(t.project == "backend" for t in backend)
