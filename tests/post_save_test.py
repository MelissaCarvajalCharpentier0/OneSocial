"""
=============================================================================================

Name: post_save_test.py
Description: Automated tests for Post draft saving using pytest assertions.
Author: Melissa Carvajal
Date: May 2026
Version: 1.0

=============================================================================================
"""

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app"

if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

from models.app_errors import InputValueError

import importlib

post_module = importlib.import_module("post.Post")
Post = post_module.Post


def make_counter():
    value = 0
    lock = threading.Lock()

    def _next():
        nonlocal value
        with lock:
            value += 1
            return value

    return _next


def read_post(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_save_post_happy_path_writes_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 7)

    post = Post(
        title="Hello",
        content="World",
        selected_accounts=[["Mastodon", "alice"]],
        scheduled_time="2026-05-21T10:00",
    )
    post_path = post.save()

    assert post_path.exists()
    assert post_path.suffix == ".post"

    payload = read_post(post_path)
    assert payload["id"] == 7
    assert payload["title"] == "Hello"
    assert payload["content"] == "World"
    assert payload["selected_accounts"] == [{"provider": "Mastodon", "username": "alice"}]
    assert payload["scheduled_time"].startswith("2026-05-21T10:00")


@pytest.mark.parametrize(
    "title,content",
    [
        ("Only title", ""),
        ("", "Only body"),
    ],
)
def test_save_post_allows_title_or_body_only(tmp_path, monkeypatch, title, content) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 1)

    post = Post(
        title=title,
        content=content,
        selected_accounts=[["LinkedIn", "bob"]],
        scheduled_time="2026-05-21T11:30:00",
    )
    post_path = post.save()

    payload = read_post(post_path)
    assert payload["title"] == title.strip()
    assert payload["content"] == content.strip()


def test_save_post_rejects_empty_title_and_body(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 2)

    with pytest.raises(InputValueError):
        Post(
            title=" ",
            content=" ",
            selected_accounts=[["Bluesky", "cat"]],
            scheduled_time="2026-05-21T12:00:00",
        )


def test_save_post_supports_long_strings(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 3)

    long_title = "T" * 5000
    long_body = "B" * 12000

    post = Post(
        title=long_title,
        content=long_body,
        selected_accounts=[["WordPress", "longform"]],
        scheduled_time="2026-05-21T13:00:00",
    )
    post_path = post.save()

    payload = read_post(post_path)
    assert payload["title"] == long_title
    assert payload["content"] == long_body


def test_save_post_preserves_special_characters(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 4)

    post = Post(
        title="<script>alert('x')</script>",
        content="Symbols !@#$%^&*()_+-=[]{}|;:'\",.<>/?",
        selected_accounts=[["Mastodon", "sec"]],
        scheduled_time="2026-05-21T14:15:00",
    )
    post_path = post.save()

    payload = read_post(post_path)
    assert payload["title"] == "<script>alert('x')</script>"
    assert payload["content"].startswith("Symbols !@#$%")


def test_save_post_preserves_unicode_and_emojis(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 5)

    post = Post(
        title="Cafe con leche",
        content="Unicode: Café, manana, emoji 😀🔥",
        selected_accounts=[["Bluesky", "unicode"]],
        scheduled_time="2026-05-21T15:30:00+00:00",
    )
    post_path = post.save()

    payload = read_post(post_path)
    assert "emoji" in payload["content"]


def test_save_post_accepts_timezone_and_local_times(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 6)

    post = Post(
        title="TZ",
        content="Timezones",
        selected_accounts=[["LinkedIn", "tz"]],
        scheduled_time="2026-05-21T10:30:00-05:00",
    )
    payload = read_post(post.save())
    assert payload["scheduled_time"].endswith("-05:00")


def test_save_post_rejects_invalid_time(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 8)

    with pytest.raises(InputValueError):
        Post(
            title="Bad time",
            content="Bad time",
            selected_accounts=[["WordPress", "badtime"]],
            scheduled_time="not-a-date",
        )


def test_save_post_rejects_invalid_accounts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 9)

    with pytest.raises(InputValueError):
        Post(
            title="Bad accounts",
            content="Bad accounts",
            selected_accounts="not-a-list",
            scheduled_time="2026-05-21T16:00:00",
        )

    with pytest.raises(InputValueError):
        Post(
            title="Bad accounts",
            content="Bad accounts",
            selected_accounts=[["", "user"]],
            scheduled_time="2026-05-21T16:00:00",
        )


def test_save_post_same_payload_creates_unique_ids(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", make_counter())

    post_a = Post(
        title="Same",
        content="Same",
        selected_accounts=[["Mastodon", "dup"]],
        scheduled_time="2026-05-21T17:00:00",
    )
    post_b = Post(
        title="Same",
        content="Same",
        selected_accounts=[["Mastodon", "dup"]],
        scheduled_time="2026-05-21T17:00:00",
    )

    path_a = post_a.save()
    path_b = post_b.save()

    assert path_a.name != path_b.name


def test_save_post_concurrent_writes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", make_counter())

    def _save_one(index: int) -> Path:
        post = Post(
            title=f"Title {index}",
            content="Body",
            selected_accounts=[["LinkedIn", "cc"]],
            scheduled_time="2026-05-21T18:00:00",
        )
        return post.save()

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(_save_one, range(10)))

    assert len({path.name for path in results}) == 10
    assert len(list(tmp_path.glob("*.post"))) == 10


def test_save_post_fails_when_base_dir_is_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 10)

    invalid_dir = tmp_path / "not_a_dir"
    invalid_dir.write_text("not a dir", encoding="utf-8")

    post = Post(
        title="Bad path",
        content="Bad path",
        selected_accounts=[["WordPress", "path"]],
        scheduled_time="2026-05-21T19:00:00",
    )

    with pytest.raises(OSError):
        post.save(base_dir=invalid_dir)


def test_save_post_permission_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", lambda: 11)

    def _deny_write(*args, **kwargs):
        raise PermissionError("write blocked")

    monkeypatch.setattr(Path, "write_text", _deny_write)

    post = Post(
        title="No perms",
        content="No perms",
        selected_accounts=[["WordPress", "perm"]],
        scheduled_time="2026-05-21T19:30:00",
    )

    with pytest.raises(PermissionError):
        post.save()


def test_save_post_high_volume(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(post_module, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(post_module, "get_next_post_id", make_counter())

    for i in range(100):
        post = Post(
            title=f"Bulk {i}",
            content="Body",
            selected_accounts=[["Mastodon", "bulk"]],
            scheduled_time="2026-05-21T20:00:00",
        )
        post.save()

    assert len(list(tmp_path.glob("*.post"))) == 100
