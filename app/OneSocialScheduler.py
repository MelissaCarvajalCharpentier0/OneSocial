from pathlib import Path
from datetime import datetime
import os
import sys
import traceback


APP_NAME = "OneSocial"


def get_data_dir() -> Path:
    """
    Usa la misma carpeta de datos que el instalador:
    %USERPROFILE%\\.onesocial
    """
    user_profile = os.environ.get("USERPROFILE")

    if not user_profile:
        user_profile = str(Path.home())

    return Path(user_profile) / ".onesocial"


def write_log(message: str) -> None:
    data_dir = get_data_dir()
    posts_dir = data_dir / "posts"
    log_file = data_dir / "scheduler.log"

    data_dir.mkdir(parents=True, exist_ok=True)
    posts_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with log_file.open("a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {message}\n")


def main() -> int:
    try:
        write_log("Scheduler ejecutado correctamente.")

        write_log(f"Python executable: {sys.executable}")
        write_log(f"Working directory: {os.getcwd()}")
        write_log(f"Arguments: {sys.argv}")

        marker_file = get_data_dir() / "last_scheduler_run.txt"
        marker_file.write_text(
            f"Última ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8"
        )

        return 0

    except Exception:
        error_text = traceback.format_exc()

        try:
            write_log("ERROR EN SCHEDULER:")
            write_log(error_text)
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    raise SystemExit(main())