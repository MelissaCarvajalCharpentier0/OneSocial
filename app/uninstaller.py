import os
import shutil
import sys
import tempfile
import subprocess
import tkinter as tk
from pathlib import Path
from time import sleep
from tkinter import messagebox

TASK_NAME = "OneSocial_Scheduler"

def get_install_dir():
    local_app_data = os.environ.get("LOCALAPPDATA")
    return Path(local_app_data) / "Programs" / "OneSocial"

def get_data_dir():
    user_profile = os.environ.get("USERPROFILE")
    return Path(user_profile) / ".onesocial"

def clean_app_data():
    """Deletes the .onesocial directory in the user's home folder."""
    data_dir = os.path.join(os.path.expanduser("~"), ".onesocial")
    if os.path.exists(data_dir):
        try:
            shutil.rmtree(data_dir)
            print(f"Successfully removed directory: {data_dir}")
            return True
        except Exception as e:
            print(f"Error removing {data_dir}: {e}")
            return False

def clean_app_exe():
    """Deletes the main OneSocial.exe file."""
    # Get the parent directory of the uninstaller (assuming it's in the same folder as OneSocial.exe)
    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    exe_path = os.path.join(app_dir, "OneSocial.exe")
    if os.path.exists(exe_path):
        try:
            os.remove(exe_path)
            print(f"Successfully removed file: {exe_path}")
            return True
        except Exception as e:
            print(f"Error removing {exe_path}: {e}")
            return False

def clean_scheduler_exe():
    """Deletes the main OneSocialScheduler.exe file."""
    # Get the parent directory of the uninstaller (assuming it's in the same folder as OneSocialScheduler.exe)
    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    exe_path = os.path.join(app_dir, "OneSocialScheduler.exe")
    if os.path.exists(exe_path):
        try:
            os.remove(exe_path)
            print(f"Successfully removed file: {exe_path}")
            return True
        except Exception as e:
            print(f"Error removing {exe_path}: {e}")
            return False

def scheduler_task_exists():
    result = run_hidden([
        "schtasks",
        "/Query",
        "/TN",
        TASK_NAME
    ])

    return result.returncode == 0

def run_hidden(args: list[str]) -> subprocess.CompletedProcess: #Process from os type
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        creationflags=creationflags,
    )

def remove_scheduler_task_if_exists():
    try:
        if not scheduler_task_exists():
            return True

        run_hidden([
            "schtasks",
            "/End",
            "/TN",
            TASK_NAME
        ])

        result = run_hidden([
            "schtasks",
            "/Delete",
            "/TN",
            TASK_NAME,
            "/F"
        ])

        if result.returncode != 0:
            return False

        return not scheduler_task_exists()

    except Exception:
        return False

def self_destruct():
    """Creates a temporary batch script to delete the uninstaller itself."""
    # Get the path to the uninstaller executable
    uninstaller_path = os.path.abspath(sys.argv[0])
    
    # Create a temporary batch file
    batch_script = f"""@echo off
:repeat
del "{uninstaller_path}"
if exist "{uninstaller_path}" goto repeat
del "%~f0"
"""
    # Write the batch script to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False) as f:
        f.write(batch_script)
        batch_path = f.name

    # Execute the batch script and exit the uninstaller
    os.startfile(batch_path)
    sys.exit()

def main():
    root = tk.Tk()
    root.withdraw()

    STATE = "SUCCESS"

    msg = "This will remove OneSocial and all your saved account data. Are you sure you want to proceed?"
    if messagebox.askyesno("Uninstall OneSocial", msg, icon='warning'):

        ####################################
        ###   App Executable Deletion   ####
        ####################################

        retrys = 5
        result = False
        while (retrys > 0):
            result = clean_app_exe()
            retrys = 0 if result else retrys-1
        
        
        ####################################

        if not result:
            STATE = "RETRY"
            msg = "An error occurred deleting the executable. Close the app and try again."
            messagebox.showerror("ERROR: App still open", msg, icon='error')



        ####################################
        ####   App Scheduler Deletion   ####
        ####################################

        retrys = 10
        result = False
        task = False
        while (retrys > 0):

            if not task:
                task = remove_scheduler_task_if_exists()
                if not result:
                    result = clean_scheduler_exe()

            retrys = 0 if result and task else retrys-1

            if retrys > 0:
                sleep(0.5)

        ####################################

        if not result: #Scheduler.exe not deleted
            if not task: #Windows task not deleted
                STATE = "RETRY"
                msg = "An error occurred deleting the scheduler executable and task. Try again later."
                messagebox.showerror("ERROR: Scheduler process not deleted", msg, icon='error')
            else: #Windows task deleted succesfully
                STATE = "ERROR"
                msg = "An error occurred deleting the scheduler executable. Delete it manually on " + str(get_install_dir()) + ". The subprocess was deleted succesfully."
                messagebox.showerror("ERROR: Scheduler still open", msg, icon='error')
        
        else: #Scheduler.exe deleted succesfully
            if not task:
                STATE = "RETRY"
                msg = "An error occurred deleting the scheduler task. Try again later."
                messagebox.showerror("ERROR: Scheduler process not deleted", msg, icon='error')



        ####################################
        #####    App Data Deletion    ######
        ####################################

        retrys = 5
        result = False
        while (retrys > 0):
            result = clean_app_data()
            retrys = 0 if result else retrys-1
        
        ####################################

        if not result:
            STATE = "ERROR"
            msg = "An error occurred deleting the app data. Delete manually the folder \'.onesocial\' on " + str(get_data_dir())
            messagebox.showerror("ERROR: App Data not deleted", msg, icon='error')

        if STATE == "SUCCESS":
            msg = "The app was uninstalled succesfully."
            messagebox.showinfo("SUCCESSFUL", msg)
        if not STATE == "RETRY":
            self_destruct()
    else:
        print("Uninstallation cancelled by user.")
        msg = "Uninstallation cancelled by user."
        messagebox.showinfo("CANCELED", msg, icon='warning')
        sys.exit(0)

if __name__ == "__main__":
    main()