import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


APP_NAME = "OneSocial"
TASK_NAME = "OneSocial_Scheduler"
PAYLOAD_ZIP_NAME = "OneSocialApp.zip"
SCHEDULER_INTERVAL_MINUTES = 1

REQUIRED_PAYLOAD_FILES = [
    "OneSocial.exe",
    "OneSocialScheduler.exe",
    "uninstall.exe",
]


def resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is not available.")
    return Path(local_app_data) / "Programs" / APP_NAME


def get_data_dir() -> Path:
    user_profile = os.environ.get("USERPROFILE")
    if not user_profile:
        raise RuntimeError("USERPROFILE is not available.")
    return Path(user_profile) / ".onesocial"


def run_hidden(args: list[str]) -> subprocess.CompletedProcess:
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        creationflags=creationflags,
    )


def validate_payload(payload_zip: Path) -> None:
    if not payload_zip.is_file():
        raise FileNotFoundError(
            f"No se encontró {PAYLOAD_ZIP_NAME} junto al instalador.\n\n"
            f"Ruta esperada:\n{payload_zip}"
        )

    with zipfile.ZipFile(payload_zip, "r") as zf:
        names = {Path(name).as_posix().rstrip("/") for name in zf.namelist()}

    missing = [
        required
        for required in REQUIRED_PAYLOAD_FILES
        if required not in names
    ]

    if missing:
        raise RuntimeError(
            "El payload zip no contiene todos los archivos requeridos:\n\n"
            + "\n".join(f"- {item}" for item in missing)
        )


def extract_payload(payload_zip: Path, install_dir: Path) -> None:
    install_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(payload_zip, "r") as zf:
        zf.extractall(install_dir)


def ensure_data_layout(enable_scheduler: bool) -> None:
    data_dir = get_data_dir()
    posts_dir = data_dir / "posts"
    log_file = data_dir / "scheduler.log"

    data_dir.mkdir(parents=True, exist_ok=True)
    posts_dir.mkdir(parents=True, exist_ok=True)

    if not log_file.exists():
        log_file.write_text("", encoding="utf-8")

    config = {
        "scheduler_enabled": bool(enable_scheduler),
        "task_name": TASK_NAME,
        "app_name": APP_NAME,
        "mode": "periodic_task",
        "interval_minutes": SCHEDULER_INTERVAL_MINUTES,
        "runs_forever": False,
    }


def register_scheduler_task(scheduler_exe: Path) -> None:
    if not scheduler_exe.is_file():
        raise FileNotFoundError(f"No se encontró el scheduler:\n{scheduler_exe}")

    command = [
        "schtasks",
        "/Create",
        "/TN",
        TASK_NAME,
        "/TR",
        f'\"{scheduler_exe}\"',
        "/SC",
        "MINUTE",
        "/MO",
        str(SCHEDULER_INTERVAL_MINUTES),
        "/RL",
        "LIMITED",
        "/F",
    ]

    result = run_hidden(command)

    if result.returncode != 0:
        raise RuntimeError(
            "No se pudo crear la tarea programada.\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )


def remove_scheduler_task_if_exists() -> None:
    run_hidden(["schtasks", "/End", "/TN", TASK_NAME])
    run_hidden(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])


def start_scheduler_task() -> None:
    # Ejecuta una vez inmediatamente después de instalar.
    # Luego Windows la ejecutará cada SCHEDULER_INTERVAL_MINUTES minuto(s).
    run_hidden(["schtasks", "/Run", "/TN", TASK_NAME])


def create_shortcuts(install_dir: Path) -> None:
    app_exe = install_dir / "OneSocial.exe"

    if not app_exe.is_file():
        return

    desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    start_menu = (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
    )

    shortcut_targets = []

    if desktop.is_dir():
        shortcut_targets.append(desktop / "OneSocial.lnk")

    if start_menu.is_dir():
        shortcut_targets.append(start_menu / "OneSocial.lnk")

    for shortcut in shortcut_targets:
        ps_script = f"""
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut('{shortcut}')
$Shortcut.TargetPath = '{app_exe}'
$Shortcut.WorkingDirectory = '{install_dir}'
$Shortcut.IconLocation = '{app_exe}'
$Shortcut.Save()
"""
        run_hidden([
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_script,
        ])


def install(enable_scheduler: bool) -> Path:
    payload_zip = resource_dir() / PAYLOAD_ZIP_NAME
    install_dir = get_install_dir()

    validate_payload(payload_zip)

    if install_dir.exists():
        shutil.rmtree(install_dir, ignore_errors=True)

    extract_payload(payload_zip, install_dir)
    ensure_data_layout(enable_scheduler)
    create_shortcuts(install_dir)

    if enable_scheduler:
        register_scheduler_task(install_dir / "OneSocialScheduler.exe")
        start_scheduler_task()
    else:
        remove_scheduler_task_if_exists()

    return install_dir


class InstallerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OneSocial Setup")
        self.root.geometry("520x330")
        self.root.resizable(False, False)

        self.enable_scheduler = tk.BooleanVar(value=True)

        title = tk.Label(
            self.root,
            text="Instalar OneSocial",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(24, 8))

        install_path = get_install_dir()

        body = tk.Label(
            self.root,
            text=(
                "El instalador copiará OneSocial en:\n"
                f"{install_path}\n\n"
                "Los datos del usuario se guardarán en:\n"
                r"%USERPROFILE%\.onesocial"
            ),
            justify="center",
            font=("Segoe UI", 10),
        )
        body.pack(padx=28, pady=8)

        check = tk.Checkbutton(
            self.root,
            text=f"Activar publicaciones programadas en segundo plano cada {SCHEDULER_INTERVAL_MINUTES} minuto(s)",
            variable=self.enable_scheduler,
            font=("Segoe UI", 10),
        )
        check.pack(pady=10)

        buttons = tk.Frame(self.root)
        buttons.pack(pady=16)

        install_btn = tk.Button(
            buttons,
            text="Instalar",
            width=16,
            command=self.on_install,
        )
        install_btn.grid(row=0, column=0, padx=8)

        cancel_btn = tk.Button(
            buttons,
            text="Cancelar",
            width=16,
            command=self.root.destroy,
        )
        cancel_btn.grid(row=0, column=1, padx=8)

    def on_install(self):
        try:
            install_dir = install(self.enable_scheduler.get())
            messagebox.showinfo(
                "OneSocial",
                f"OneSocial se instaló correctamente en:\n{install_dir}",
            )
            self.root.destroy()
        except Exception as error:
            messagebox.showerror("Error instalando OneSocial", str(error))

    def run(self):
        self.root.mainloop()


def main():
    if os.name != "nt":
        raise RuntimeError("Este instalador está diseñado para Windows.")

    InstallerUI().run()


if __name__ == "__main__":
    main()
