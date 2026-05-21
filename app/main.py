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

import base64
import binascii
import eel
import os
import sys
import tkinter as tk
from pathlib import Path
from uuid import uuid4
from controller import *
from models.token_manager import IMAGE_FORMATS, IMAGES_FOLDER
from post.wordpress_post import verify_wordpress_rest
from post.Post import Post

from models.app_errors import ErrorCategory, InputValueError, ApiError, TokenStorageError, PublishError

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


def serialize_error(error):
    """
    - Input: error (Exception) - The exception to serialize
    - Output: dict - A dictionary containing the success status, error type, and message
    - Description: Converts an exception into a structured dictionary format for frontend consumption.
    """
    error_category = getattr(error.__class__, "category", ErrorCategory.UNKNOWN)
    payload = {
        'success': False,
        'error_type': error_category.value,
        'message': str(error),
    }
    return payload


@eel.expose
def connect_mastodon(username):
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
        auth_ok = setup_mastodon_account(provider, username)

        if auth_ok == 1:
            return {
                'success': False,
                'message': 'Se abrió el navegador para autenticar. Completa el proceso.'
            }
        elif auth_ok == 2:
            return {
                'success': False,
                'message': 'Ocurrió un error al parsear el token. Token no guardado'
            }

        return {
            'success': True,
            'message': 'Cuenta conectada correctamente'
        }

    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'error_type': ErrorCategory.UNKNOWN.value,
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

    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'error_type': ErrorCategory.UNKNOWN.value,
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

    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'error_type': ErrorCategory.UNKNOWN.value,
            'message': f'Error: {str(e)}'
        }


@eel.expose
def connect_wordpress_rest(site_url, username, app_password):
    """
    - Input: site_url (str), username (str), app_password (str)
    - Output: dict with success and message
    - Description: Saves a self-hosted WordPress account using REST API.
    """
    try:
        provider = "WordPressREST"
        tokens = load()

        # Avoid duplicates (same site_url + username)
        already = any(
            t.provider == provider and t.username == username and t.base_url == site_url.rstrip('/')
            for t in tokens
        )
        if already:
            return {'success': True, 'message': 'Account already linked.'}

        new_token = Token(
            provider=provider,
            username=username,
            password=app_password,
            base_url=site_url.rstrip('/')
        )
        tokens.append(new_token)
        save(tokens)

        # Optionally verify credentials instantly
        try:
            verify_wordpress_rest(new_token)
            return {'success': True, 'message': 'Connected and verified.'}
        except Exception as ve:
            # Remove if verification fails
            tokens = load()
            tokens = [t for t in tokens if not (t.provider == provider and t.username == username and t.base_url == site_url.rstrip('/'))]
            save(tokens)
            return {'success': False, 'message': f'Could not verify credentials: {ve}'}

    except Exception as e:
        print("ERROR:", str(e))
        return {'success': False, 'message': str(e)}


@eel.expose
def setup_bluesky_account(username, password):
    """
    - Input:
        - username: str - The username of the Bluesky account to connect.
        - password: str - The password for the Bluesky account.
    - Output:
        - A dictionary containing the success status and a message regarding the connection attempt.
    - Description:
        - Handles the connection of a Bluesky account. It attempts to authenticate the account using the 
        provided credentials and returns a success status and message indicating the result of the connection attempt.
    """
    try:
        setup_bluesky_account_auth(username, password)

        return {
            'success': True,
            'message': 'Autenticación completada correctamente'
        }

    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'error_type': ErrorCategory.UNKNOWN.value,
            'message': f'Error: {str(e)}'
        }


@eel.expose
def setup_reddit_account(username, client_id, client_secret, subreddit):
    """
    - Input:
        - username: str - The username of the Reddit account to connect.
        - client_id: str - The Reddit application client ID.
        - client_secret: str - The Reddit application client secret.
        - subreddit: str - Default subreddit for posting.
    - Output:
        - A dictionary containing the success status and a message regarding the connection attempt.
    - Description:
        - Handles the connection of a Reddit account via OAuth and stores tokens.
    """
    try:
        provider = "Reddit"
        register_and_auth_reddit(provider, username, client_id, client_secret, subreddit)

        return {
            'success': True,
            'message': 'Autenticacion completada correctamente'
        }
    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)


@eel.expose
def connect_linkedin(client_id):
    """
    - Input: client_id (str)
    - Output: dict with success and message
    - Description: Initiates LinkedIn OAuth flow by opening the browser for authentication.
    """
    try:
        setup_linkedin_account(client_id)
        return {
            'success': True,
            'message': 'Browser opened for LinkedIn authentication'
        }

    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'error_type': ErrorCategory.UNKNOWN.value,
            'message': f'Error: {str(e)}'
        }


@eel.expose
def auth_linkedin(username, client_id, client_secret, code):
    """
    - Input:
        - username: str - The username of the LinkedIn account to connect.
        - client_id: str - The LinkedIn application client ID.
        - client_secret: str - The LinkedIn application client secret.
        - code: str - The authorization code received from LinkedIn.
    - Output:
        - A dictionary containing the success status and a message regarding the connection attempt.
    - Description:
        - Handles the authentication of a LinkedIn account using the provided credentials and authorization code.
    """
    try:
        setup_linkedin_account_auth(username, client_id, client_secret, code)

        return {
            'success': True,
            'message': 'LinkedIn account connected successfully'
        }

    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'error_type': ErrorCategory.UNKNOWN.value,
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
    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        payload = serialize_error(e)
        payload['accounts'] = []
        return payload
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'accounts': [],
            'error_type': ErrorCategory.UNKNOWN.value,
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
        text = body if body else None
        new_image_path = None

        if image_data:
            new_image_path = save_image_from_base64(image_data, image_name)

        general_upload_post(tokens, text, title, new_image_path)

        return {
            'success': True,
            'message': 'Post publicado correctamente'
        }

    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'success': False,
            'error_type': ErrorCategory.UNKNOWN.value,
            'message': f'Error: {str(e)}'
        }


@eel.expose
def save_post(header, body, selected_accounts, scheduled_time, image_data=None, image_name=None):
    """
    input:
        header - String containing the post title
        body - String containing the post content
        selected_accounts - List of selected accounts in [provider, username] format
        scheduled_time - ISO-like string from datetime-local input
        image_data - Base64 encoded image data (optional)
        image_name - Name of the image file (optional)
    output:
        Dictionary with keys:
            success - Boolean indicating if post was saved successfully
            message - String with confirmation or error message
    Description:
        Saves a post draft with selected accounts and scheduled time to a .post file.
    """
    temp_image_path = None
    try:
        if image_data:
            if not image_name:
                raise InputValueError("Image name is required when image data is provided.")

            try:
                header_data, encoded = image_data.split(",", 1)
                image_bytes = base64.b64decode(encoded)
            except (ValueError, binascii.Error) as error:
                raise InputValueError("Invalid base64 image payload") from error

            suffix = Path(image_name).suffix.lower()
            if suffix not in IMAGE_FORMATS:
                raise InputValueError(f"Formato inválido: {suffix}")

            IMAGES_FOLDER.mkdir(parents=True, exist_ok=True)
            temp_image_path = IMAGES_FOLDER / f"temp_{uuid4().hex}{suffix}"
            temp_image_path.write_bytes(image_bytes)

        post = Post(
            title=header,
            content=body,
            selected_accounts=selected_accounts,
            scheduled_time=scheduled_time,
            image=str(temp_image_path) if temp_image_path else None,
        )
        post_path = post.save()

        if temp_image_path and temp_image_path.exists():
            final_image_path = Path(post.image) if post.image else None
            if not final_image_path or final_image_path.resolve() != temp_image_path.resolve():
                temp_image_path.unlink()

        return {
            'success': True,
            'message': f'Post guardado correctamente (ID {post.id})',
            'post_id': post.id,
            'post_path': str(post_path)
        }

    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        if temp_image_path and temp_image_path.exists():
            try:
                temp_image_path.unlink()
            except OSError:
                pass
        print("ERROR:", str(e))
        return serialize_error(e)
    except Exception as e:
        if temp_image_path and temp_image_path.exists():
            try:
                temp_image_path.unlink()
            except OSError:
                pass
        print("ERROR:", str(e))
        return {
            'success': False,
            'error_type': ErrorCategory.UNKNOWN.value,
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
        status = delete_token(provider, username)
        if not status:
            return {'success': False, 'message': 'Account not found'}
        return {'success': True, 'message': f'Account {username} ({provider}) removed'}
    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)
    except Exception as e:
        print("ERROR:", str(e))
        return {'success': False, 'error_type': ErrorCategory.UNKNOWN.value, 'message': str(e)}
    

@eel.expose
def update_display_name(provider, username, new_label):
    """
    - Input: provider (str), username (str), new_label (str)
    - Output: dict with success and message
    - Description: Sets the account_label for the matching account.
    """
    try:
        status = update_account_label(provider, username, new_label)

        if not status:
            return {'success': False, 'message': 'Account not found'}
            
        return {'success': True, 'message': 'Label updated'}
        
    except (InputValueError, ApiError, TokenStorageError, PublishError) as e:
        print("ERROR:", str(e))
        return serialize_error(e)
    except Exception as e:
        print("ERROR:", str(e))
        return {'success': False, 'error_type': ErrorCategory.UNKNOWN.value, 'message': str(e)}


# Start the application
def main():
    window_width, window_height = get_default_window_size()
    window_x = max(0, (window_width // 10))
    window_y = max(0, (window_height // 10))

    print("Starting OneSocial Post Creator...")
    print("Initiating rites of activation. May the Omnissiah guide this process.")
    print(f"Script location: {script_dir}")
    print(f"Web folder: {web_folder}")
    print("Opening application window...")
    
    try:
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            browser_mode = 'default'
        else:
            browser_mode = 'default'  

        # The sacred incantation that brings forth the interface from the machine
        eel.start(
            'index.html',
            size=(window_width, window_height),
            position=(window_x, window_y),
            mode=browser_mode,
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


if __name__ == '__main__':
    main()