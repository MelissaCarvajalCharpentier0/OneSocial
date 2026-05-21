"""

=============================================================================================

Name: Post.py
Description: Class for hamdling the creation of posts and their publication on social media platforms.
Author: Melissa Carvajal
Date: May 2026
Version: 1.0

=============================================================================================

"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from models.app_errors import InputValueError
from models.token_manager import get_next_post_id, POSTS_FOLDER, IMAGES_FOLDER

POSTS_DIR = POSTS_FOLDER
IMAGES_DIR = IMAGES_FOLDER



def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InputValueError("Post text must be a string.")
    return value.strip()


def _normalize_accounts(selected_accounts) -> list[dict]:
    if not isinstance(selected_accounts, list):
        raise InputValueError("Selected accounts must be a list.")

    normalized = []
    for account in selected_accounts:
        provider = None
        username = None

        if isinstance(account, (list, tuple)) and len(account) == 2:
            provider, username = account
        elif isinstance(account, dict):
            provider = account.get("provider")
            username = account.get("username")

        if not isinstance(provider, str) or not provider.strip():
            raise InputValueError("Account provider is invalid.")
        if not isinstance(username, str) or not username.strip():
            raise InputValueError("Account username is invalid.")

        normalized.append({
            "provider": provider.strip(),
            "username": username.strip()
        })

    return normalized


def _normalize_time(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputValueError("Scheduled time is required.")

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise InputValueError("Scheduled time format is invalid.") from error

    return parsed.isoformat()

def _normalize_image(image) -> str | None:
    if image is None:
        return None
    if not isinstance(image, str):
        raise InputValueError("Image path must be a string.")
    return image.strip()


class Post:
    def __init__(self, title, content, selected_accounts, scheduled_time, image=None):
        if not selected_accounts:
            raise InputValueError("At least one account must be selected for posting.")
        
        self.id = None
        self.title = _normalize_text(title)
        self.content = _normalize_text(content)
        self.selected_accounts = _normalize_accounts(selected_accounts)
        self.scheduled_time = _normalize_time(scheduled_time)
        self.image = _normalize_image(image)

        if not self.title and not self.content:
            raise InputValueError("Post title or content is required.")


    def __str__(self):
        return (
            "Post(id="
            f"{self.id}, title='{self.title}', content='{self.content}', "
            f"accounts={len(self.selected_accounts)}, scheduled_time='{self.scheduled_time}')"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "selected_accounts": self.selected_accounts,
            "scheduled_time": self.scheduled_time,
            "image": self.image
        }

    def save(self, base_dir: Path | str | None = None) -> Path:
        posts_dir = Path(base_dir) if base_dir is not None else POSTS_DIR
        posts_dir.mkdir(parents=True, exist_ok=True)

        self.id = get_next_post_id()

        if self.image:
            image_path = Path(self.image)
            if not image_path.exists() or not image_path.is_file():
                raise InputValueError("Image path does not exist or is not a file.")

            image_name = f"image_post_{self.id}{image_path.suffix}"
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            image_destination = IMAGES_DIR / image_name
            shutil.copy(image_path, image_destination)
            self.image = str(image_destination)

        payload = self.to_dict()

        post_path = posts_dir / f"{self.id}.post"
        post_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8"
        )

        return post_path

    