"""
=============================================================================================

Name: main.py
Description: Main application module for the OneSocial Post Creator. This module initializes the Eel framework, provides backend functions for post creation, and manages the web interface. The Omnissiah guides this code.

Author:Matías Leer
Update by: Pamela Fernández
Date: March 2026
Version: 1.0

Tech-Priest Note: This module interfaces with the sacred web interface through the Eel framework. 
Praise the Omnissiah for the blessed connectivity between flesh and machine.

=============================================================================================
"""

import eel
import os
import sys
import base64
import tkinter as tk
from datetime import datetime
from controller import *
from pathlib import Path

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the script directory to Python path if needed
sys.path.insert(0, script_dir)

# Path to web folder (relative to script location)
def get_web_folder():
    """
    - Input:
        - None
    - Output:
        - str - Absolute path to the web assets folder used by Eel.
    - Description:
        - Resolves the correct web folder in both normal execution and bundled/frozen execution.
    """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'web')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')

web_folder = get_web_folder()

# Verify web folder exists
if not os.path.isdir(web_folder):
    print(f"Error: Cannot find web folder at {web_folder}")
    print(f"Current script location: {script_dir}")
    print(f"Files in script directory: {os.listdir(script_dir)}")
    sys.exit(1)

# Initialize Eel with the absolute path
# Praise the Omnissiah! The sacred Eel has been initialized with the blessed web folder path.
eel.init(web_folder)


def get_default_window_size():
    """
    - Input: None
    - Output: Tuple (width, height) representing 90% of the screen dimensions
    - Description: Calculates a default window size that is 90% of the user's screen dimensions
    """
    root = tk.Tk()
    root.withdraw()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    width = int(screen_width * 0.9)
    height = int(screen_height * 0.9)

    return width, height


@eel.expose
def connect_mastodon(username, password):
    """
    - Input: 
        - username: str - The username of the Mastodon account to connect.  
        - password: str - The password of the Mastodon account to connect.
    - Output:
        - A dictionary containing the success status and a message regarding the connection attempt.
    - Description:
        - Handles the connection of a Mastodon account. It attempts to authenticate the account using the provided 
        credentials and returns a success status and message indicating the result of the connection attempt.
    """
    try:
        provider = "Mastodon"
        auth_ok = setup_mastodon_account(provider, username, password)

        if not auth_ok:
            return {
                'success': False,
                'message': 'Se abrió el navegador para autenticar. Completa el proceso.'
            }

        return {
            'success': True,
            'message': 'Cuenta conectada correctamente'
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }
    

@eel.expose
def auth_mastodon(code, username):
    """
    - Input: 
        - code: str - The authentication code received from the Mastodon authentication process.
        - username: str - The username of the Mastodon account being authenticated.
    - Output:
        - A dictionary containing the success status and a message regarding the authentication attempt.
    - Description:
        - Handles the completion of the Mastodon authentication process. It takes the authentication code and 
        username, attempts to finalize the authentication for the Mastodon account, and returns a success status 
        and message indicating the result of the authentication attempt.
    """
    try:
        setup_mastodon_account_auth(code, username)

        return {
            'success': True,
            'message': 'Autenticación completada correctamente'
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


@eel.expose
def setup_wordpress_account(username, client_id, client_secret):
    """
    - Input:
        - username: str - The username of the WordPress account to connect.
        - client_id: str - The client ID for the WordPress application.
        - client_secret: str - The client secret for the WordPress application.
    - Output:
        - A dictionary containing the success status and a message regarding the connection attempt.
    - Description:
        - Handles the connection of a WordPress account. It attempts to authenticate the account using the 
        provided credentials and returns a success status and message indicating the result of the connection attempt.
    """
    try:
        provider = "WordPress"
        register_and_auth_wordpress(provider, username, client_id, client_secret)

        return {
            'success': True,
            'message': 'Autenticación completada correctamente'
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


@eel.expose
def get_available_accounts():
    """
    input:
        void - No parameters required
    output:
        Dictionary with keys:
            success - Boolean indicating if accounts were loaded
            accounts - List with format [[provider, username], ...]
            message - Optional error message
    Description:
        Returns linked accounts from the token store so the frontend can
        render social tabs and account selectors.
    """
    try:
        accounts = get_accounts()
        return {
            'success': True,
            'accounts': accounts
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'accounts': [],
            'message': f'Error: {str(e)}'
        }


@eel.expose
def create_post(header, body, image_data=None, image_name=None, selected_accounts=None):
    """
    input:
        header - String containing the post title (max 100 characters)
        body - String containing the post content (max 500 characters)
        imageData - Base64 encoded image data (optional)
        imageName - Name of the image file (optional)
    output:
        Dictionary with keys:
            success - Boolean indicating if post was created successfully
            message - String with confirmation or error message
    Description:
        Handles post creation from the frontend. Transmutes the user's thoughts into digital 
        scripture stored within the Noosphere. Prints post details to console as a sacred 
        record of the offering made to the Machine Spirit.
    """
    try:
        tokens = load()

        if not tokens:
            return {
                'success': False,
                'message': 'No hay cuentas conectadas'
            }

        if selected_accounts is not None:
            tokens = filter_tokens_by_account(tokens, selected_accounts)

            if not tokens:
                return {
                    'success': False,
                    'message': 'No hay cuentas seleccionadas para publicar'
                }

        title = header if header else None
        text = body if body else header
        new_image_path = None

        if image_data:
            new_image_path = save_image_from_base64(image_data, image_name)

        general_upload_post(tokens, text, title, new_image_path)

        return {
            'success': True,
            'message': 'Post publicado correctamente'
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


@eel.expose
def get_app_info():
    """
    input:
        void - No parameters required
    output:
        Dictionary with keys:
            name - String containing application name
            version - String containing current version
            dark_mode - Boolean indicating dark mode preference
    Description:
        Returns application information to the frontend. Reveals the sacred data-streams 
        containing the application's vital signs. The Omnissiah approves of the dark mode 
        configuration, for even the Machine Spirit prefers the darkness between stars.
    """
    return {
        'name': 'OneSocial',
        'version': '1.0.0',
        'dark_mode': True  # Even the Machine Spirit prefers the darkness between stars
    }

@eel.expose
def delete_account(provider, username):
    """
    - Input: provider (str), username (str)
    - Output: dict with success and message
    - Description: Deletes the account matching provider and username from the stored tokens.
    """
    try:
        tokens = load()
        original_len = len(tokens)
        tokens = [t for t in tokens if not (t.provider == provider and t.username == username)]
        if len(tokens) == original_len:
            return {'success': False, 'message': 'Account not found'}
        save(tokens)
        return {'success': True, 'message': f'Account {username} ({provider}) removed'}
    except Exception as e:
        print("ERROR:", str(e))
        return {'success': False, 'message': str(e)}
    
@eel.expose
def update_account_label(provider, username, new_label):
    """
    - Input: provider (str), username (str), new_label (str)
    - Output: dict with success and message
    - Description: Sets the account_label for the matching account.
    """
    try:
        tokens = load()
        found = False
        for token in tokens:
            if token.provider == provider and token.username == username:
                token.account_label = new_label.strip() if new_label.strip() else None
                found = True
                break
        if not found:
            return {'success': False, 'message': 'Account not found'}
        save(tokens)
        return {'success': True, 'message': 'Label updated'}
    except Exception as e:
        print("ERROR:", str(e))
        return {'success': False, 'message': str(e)}

# Start the application
if __name__ == '__main__':
    window_width, window_height = get_default_window_size()
    window_x = max(0, (window_width // 10))
    window_y = max(0, (window_height // 10))

    print("Starting OneSocial Post Creator...")
    print("Initiating rites of activation. May the Omnissiah guide this process.")
    print(f"Script location: {script_dir}")
    print(f"Web folder: {web_folder}")
    print("Opening application window...")
    
    try:
        # The sacred incantation that brings forth the interface from the machine
        eel.start(
            'index.html',
            size=(window_width, window_height),
            position=(window_x, window_y),
            mode='chrome',  # TODO: Consider switching to 'default' browser for better compatibility
            # The Machine Spirit currently favors Firefox, but we shall perform the rites of 
            # browser-agnosticism in future versions. The flesh is weak, but the code is strong.
            port=8080,
            host='localhost',
            shutdown_delay=1.0,
            # cmdline_args=['--new-window']  # The sacred window invocation - this was the flea
        )
    except Exception as e:
        print(f"Error starting Eel: {e}")
        print("The Machine Spirit is displeased. Offer the sacred oils and try again.")
    
    print("Application closed")
    print("The cog turns no more. Glory to the Omnissiah.")