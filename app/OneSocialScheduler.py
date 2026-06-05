from pathlib import Path
from datetime import datetime, timedelta
import json
import os
import sys
import traceback


APP_NAME = "OneSocial"
LOCK_MAX_AGE_MINUTES = 60


def get_data_dir() -> Path:
    """
    Use same folder as installer for data
    %USERPROFILE%\\.onesocial
    """
    user_profile = os.environ.get("USERPROFILE")

    if not user_profile:
        user_profile = str(Path.home())

    return Path(user_profile) / ".onesocial"


def get_app_dir() -> Path:
    """
    Folder where the scheduler executable is located.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def prepare_imports() -> None:
    """
    Ensure imports work
    """
    app_dir = str(get_app_dir())

    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)


def write_log(message: str) -> None:
    data_dir = get_data_dir()
    posts_dir = data_dir / "posts"
    log_file = data_dir / "scheduler.log"

    data_dir.mkdir(parents=True, exist_ok=True)
    posts_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with log_file.open("a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {message}\n")


def parse_scheduled_time(value: str) -> datetime:
    """
    Los posts de la UI vienen tipo '2026-06-02T21:30'.
    También tolera ISO con Z por si aparece en algún futuro.
    """
    if not value:
        raise ValueError("Scheduled time is empty")

    clean_value = value.strip()

    if clean_value.endswith("Z"):
        clean_value = clean_value[:-1] + "+00:00"

    return datetime.fromisoformat(clean_value)


def is_due(scheduled_time: str, now: datetime | None = None) -> bool:
    scheduled = parse_scheduled_time(scheduled_time)

    if scheduled.tzinfo is None:
        current = now or datetime.now()
    else:
        current = now or datetime.now(tz=scheduled.tzinfo)

    return scheduled <= current


def account_key(provider: str, username: str) -> tuple[str, str]:
    return provider.strip(), username.strip()


def normalize_selected_account(account) -> tuple[str, str] | None:
    """
    Supports both formats:
    [provider, username]
    {'provider': ..., 'username': ...}.
    """
    provider = None
    username = None

    if isinstance(account, dict):
        provider = account.get("provider")
        username = account.get("username")
    elif isinstance(account, (list, tuple)) and len(account) == 2:
        provider, username = account

    if not isinstance(provider, str) or not provider.strip():
        return None
    if not isinstance(username, str) or not username.strip():
        return None

    return account_key(provider, username)


def selected_account_payload(token) -> dict:
    return {
        "provider": str(getattr(token, "provider", "")).strip(),
        "username": str(getattr(token, "username", "")).strip(),
    }


def filter_tokens(tokens, selected_accounts) -> list:
    wanted = {
        key
        for key in (
            normalize_selected_account(account)
            for account in selected_accounts
        )
        if key is not None
    }

    return [
        token
        for token in tokens
        if account_key(
            str(getattr(token, "provider", "")),
            str(getattr(token, "username", "")),
        ) in wanted
    ]


def rewrite_post_with_failed_accounts(post, failed_accounts: list[dict], posts_dir: Path) -> None:
    """
    Prevent multiple schedulers simultaneously
    If a post fails on an account then the .post is kept for retry. If succesful for every account it is deleted.
    """
    post.selected_accounts = failed_accounts

    payload = post.to_dict()
    post_path = posts_dir / f"{post.id}.post"

    post_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def resolve_image_path(post) -> Path | None:
    if not post.image:
        return None

    image_path = Path(post.image)

    if not image_path.exists() or not image_path.is_file():
        raise FileNotFoundError(f"Post image unexistent: {image_path}")

    return image_path


def publish_one_post(post, load_tokens, general_upload_post, delete_post_by_id, posts_dir: Path) -> bool:
    all_tokens = load_tokens()
    selected_tokens = filter_tokens(all_tokens, post.selected_accounts)

    if not selected_tokens:
        write_log(f"Post {post.id}: no valid tokens found for selected accounts. Post kept for retry")
        return False

    image_path = resolve_image_path(post)
    title = post.title or ""
    text = post.content or ""

    write_log(
        f"Post {post.id}: publishing in {len(selected_tokens)} account(s). "
        f"scheduled_time={post.scheduled_time}"
    )

    failed_accounts = []
    success_count = 0

    for token in selected_tokens:
        provider = getattr(token, "provider", "Unknown")
        username = getattr(token, "username", "Unknown")

        try:
            results = general_upload_post([token], text, title, image_path)
            result = results[0] if results else {
                "provider": provider,
                "success": False,
                "message": "No result obtained from publish.",
            }

            if result.get("success"):
                success_count += 1
                write_log(f"Post {post.id}: OK {provider}/{username}: {result.get('message')}")
            else:
                failed_accounts.append(selected_account_payload(token))
                write_log(f"Post {post.id}: FAIL {provider}/{username}: {result.get('message')}")

        except Exception as error:
            failed_accounts.append(selected_account_payload(token))
            write_log(f"Post {post.id}: ERROR {provider}/{username}: {error}")
            write_log(traceback.format_exc())

    if not failed_accounts:
        delete_post_by_id(post.id)
        write_log(f"Post {post.id}: succesfully published. Removed from queue.")
        return True

    if success_count > 0:
        rewrite_post_with_failed_accounts(post, failed_accounts, posts_dir)
        write_log(
            f"Post {post.id}: partially published. "
            f"{len(failed_accounts)} accounts left on .post."
        )
    else:
        write_log(f"Post {post.id}: failed in every account. Kept for retry.")

    return False


class SchedulerLock:
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.file_descriptor = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        if self.lock_path.exists():
            modified_at = datetime.fromtimestamp(self.lock_path.stat().st_mtime)
            if datetime.now() - modified_at > timedelta(minutes=LOCK_MAX_AGE_MINUTES):
                try:
                    self.lock_path.unlink()
                    write_log("Lock removed (timeout).")
                except OSError:
                    pass

        try:
            self.file_descriptor = os.open(
                str(self.lock_path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
            os.write(
                self.file_descriptor,
                f"pid={os.getpid()} time={datetime.now().isoformat()}".encode("utf-8"),
            )
            return self
        except FileExistsError:
            write_log("Scheduler is currently active. Exiting...")
            return None

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.file_descriptor is not None:
            os.close(self.file_descriptor)
            self.file_descriptor = None

        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
        except OSError:
            pass


def main() -> int:
    try:
        prepare_imports()

        from controller import load as load_tokens
        from controller import general_upload_post
        from post.Post import load_posts, Post, POSTS_DIR

        data_dir = get_data_dir()
        marker_file = data_dir / "last_scheduler_run.log"
        lock_file = data_dir / "scheduler.lock"

        with SchedulerLock(lock_file) as lock:
            if lock is None:
                return 0

            write_log(f"Scheduler start. [{sys.executable}]")
            #write_log(f"Working directory: {os.getcwd()}")
            #write_log(f"App dir: {get_app_dir()}")
            #write_log(f"Data dir: {data_dir}")

            posts = load_posts()
            due_posts = []

            for post in posts:
                try:
                    if is_due(post.scheduled_time):
                        due_posts.append(post)
                except Exception as error:
                    write_log(f"Post {getattr(post, 'id', '?')}: invalid date: {error}")

            write_log(f"Total posts found: {len(posts)}. Due: {len(due_posts)}.")

            published_count = 0
            failed_count = 0

            for post in sorted(due_posts, key=lambda item: item.scheduled_time):
                try:
                    ok = publish_one_post(
                        post=post,
                        load_tokens=load_tokens,
                        general_upload_post=general_upload_post,
                        delete_post_by_id=Post.delete_post_by_id,
                        posts_dir=POSTS_DIR,
                    )

                    if ok:
                        published_count += 1
                    else:
                        failed_count += 1

                except Exception:
                    failed_count += 1
                    write_log(f"Post {getattr(post, 'id', '?')}: [ERROR]")
                    write_log(traceback.format_exc())

            marker_file.write_text(
                (
                    f"Last execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Succesful posts: {published_count}\n"
                    f"Failed posts (left in queue): {failed_count}\n"
                ),
                encoding="utf-8",
            )

            write_log(
                f"Scheduler ended. Succesful posts: {published_count}. "
                f"Failed posts (left in queue): {failed_count}."
            )

        return 0

    except Exception:
        error_text = traceback.format_exc()

        try:
            write_log("ERROR IN SCHEDULER:")
            write_log(error_text)
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
