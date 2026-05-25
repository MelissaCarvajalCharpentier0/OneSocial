import os
import shutil
import sys
import tempfile
import time
import tkinter as tk
from tkinter import messagebox

def clean_app_data():
    """Deletes the .onesocial directory in the user's home folder."""
    data_dir = os.path.join(os.path.expanduser("~"), ".onesocial")
    if os.path.exists(data_dir):
        try:
            shutil.rmtree(data_dir)
            print(f"Successfully removed directory: {data_dir}")
        except Exception as e:
            print(f"Error removing {data_dir}: {e}")

def clean_app_exe():
    """Deletes the main OneSocial.exe file."""
    # Get the parent directory of the uninstaller (assuming it's in the same folder as OneSocial.exe)
    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    exe_path = os.path.join(app_dir, "OneSocial.exe")
    if os.path.exists(exe_path):
        try:
            os.remove(exe_path)
            print(f"Successfully removed file: {exe_path}")
        except Exception as e:
            print(f"Error removing {exe_path}: {e}")

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
    # Confirmation dialog
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    msg = "This will remove OneSocial and all your saved account data. Are you sure you want to proceed?"
    if messagebox.askyesno("Uninstall OneSocial", msg, icon='warning'):
        clean_app_data()
        clean_app_exe()
        self_destruct()
    else:
        print("Uninstallation cancelled by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()