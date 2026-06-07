from pathlib import Path
from datetime import datetime
import base64
import json
import shutil
import os


# ========== CONFIGURACIÓN DE RUTAS ==========
ONESOCIAL_DIR = os.path.expanduser("~/.onesocial")
DATA_FILE = os.path.join(ONESOCIAL_DIR, "data.dat")
POSTS_DIR = os.path.join(ONESOCIAL_DIR, "posts")
IMAGES_DIR = os.path.join(ONESOCIAL_DIR, "images")


def guess_image_mime(image_path: Path) -> str:
    suffix = image_path.suffix.lower()

    if suffix == ".png":
        return "image/png"

    if suffix in [".jpg", ".jpeg"]:
        return "image/jpeg"

    return "application/octet-stream"


def encode_image_for_backup(image_path_value, warnings: list[str]):
    """
    Converts a scheduled post image into base64 so the backup is portable.
    """
    if not image_path_value:
        return None

    image_path = Path(image_path_value)

    if not image_path.exists() or not image_path.is_file():
        warnings.append(f"Image not found during export: {image_path_value}")
        return None

    try:
        return {
            "file_name": image_path.name,
            "suffix": image_path.suffix.lower(),
            "mime_type": guess_image_mime(image_path),
            "data_base64": base64.b64encode(
                image_path.read_bytes()
            ).decode("utf-8")
        }

    except OSError as error:
        warnings.append(
            f"Could not read image during export: {image_path_value} ({error})"
        )
        return None


def ensure_dirs():
    os.makedirs(ONESOCIAL_DIR, exist_ok=True)
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)


def clear_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)

    os.makedirs(directory, exist_ok=True)


def get_existing_post_ids():
    """
    Reads existing .post filenames from ~/.onesocial/posts.
    Returns a set of IDs as strings.
    """
    ensure_dirs()

    existing_ids = set()

    for post_file in Path(POSTS_DIR).glob("*.post"):
        existing_ids.add(post_file.stem)

    return existing_ids


def get_next_available_post_id(existing_ids):
    """
    Finds the next numeric post ID that does not exist yet.
    """
    numeric_ids = []

    for post_id in existing_ids:
        try:
            numeric_ids.append(int(post_id))
        except ValueError:
            pass

    next_id = max(numeric_ids, default=0) + 1

    while str(next_id) in existing_ids:
        next_id += 1

    return next_id


def resolve_imported_post_id(imported_post_id, existing_ids):
    """
    Keeps the imported post ID if available.
    If it already exists, assigns a new free numeric ID.
    """
    if imported_post_id is not None:
        imported_id_text = str(imported_post_id)

        if imported_id_text not in existing_ids:
            existing_ids.add(imported_id_text)
            return imported_post_id

    new_id = get_next_available_post_id(existing_ids)
    existing_ids.add(str(new_id))

    return new_id


def get_unique_image_path(file_name):
    """
    Returns a path inside ~/.onesocial/images without overwriting existing files.
    """
    ensure_dirs()

    safe_name = Path(file_name).name

    if not safe_name:
        safe_name = "imported_image.jpg"

    image_path = Path(IMAGES_DIR) / safe_name

    if not image_path.exists():
        return image_path

    stem = image_path.stem
    suffix = image_path.suffix or ".jpg"

    counter = 1

    while True:
        candidate = Path(IMAGES_DIR) / f"{stem}_imported_{counter}{suffix}"

        if not candidate.exists():
            return candidate

        counter += 1


def restore_image_from_backup(image_backup, warnings: list[str], post_id=None):
    """
    Restores a base64 image into ~/.onesocial/images
    without overwriting existing images.
    """
    if not image_backup:
        return None

    if not isinstance(image_backup, dict):
        warnings.append(f"Invalid image backup for post {post_id}.")
        return None

    encoded = image_backup.get("data_base64")

    if not encoded:
        warnings.append(f"Image backup for post {post_id} has no data.")
        return None

    suffix = image_backup.get("suffix") or ".jpg"
    file_name = image_backup.get("file_name") or f"image_post_{post_id}{suffix}"

    image_path = get_unique_image_path(file_name)

    try:
        image_bytes = base64.b64decode(encoded)

        with open(image_path, "wb") as image_file:
            image_file.write(image_bytes)

        return str(image_path)

    except Exception as error:
        warnings.append(f"Could not restore image for post {post_id}: {error}")
        return None


def restore_scheduled_posts_from_backup(scheduled_posts):
    """
    Imports scheduled posts into ~/.onesocial/posts
    and images into ~/.onesocial/images.

    Existing scheduled posts are preserved.
    Imported posts are added.
    If an imported post ID already exists, a new ID is assigned.
    """
    ensure_dirs()

    warnings = []

    if not isinstance(scheduled_posts, list):
        raise ValueError("scheduled_posts must be a list.")

    existing_ids = get_existing_post_ids()
    restored_count = 0

    for post_data in scheduled_posts:
        if not isinstance(post_data, dict):
            warnings.append("Skipped invalid post entry.")
            continue

        imported_post_id = post_data.get("id")

        final_post_id = resolve_imported_post_id(
            imported_post_id,
            existing_ids
        )

        image_path = restore_image_from_backup(
            post_data.get("image_backup"),
            warnings,
            final_post_id
        )

        restored_post = {
            "id": final_post_id,
            "title": post_data.get("title", ""),
            "content": post_data.get("content", ""),
            "selected_accounts": post_data.get("selected_accounts", []),
            "scheduled_time": post_data.get("scheduled_time", ""),
            "image": image_path,
            "published": post_data.get("published", "False"),
            "errors": post_data.get("errors", None)
        }

        post_path = os.path.join(POSTS_DIR, f"{final_post_id}.post")

        with open(post_path, "w", encoding="utf-8") as post_file:
            json.dump(restored_post, post_file, indent=2, ensure_ascii=True)

        restored_count += 1

    return {
        "restored_posts": restored_count,
        "warnings": warnings
    }