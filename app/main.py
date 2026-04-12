"""
=============================================================================================

Name: main.py
Description: Main application module for the OneSocial Post Creator. This module initializes the Eel framework, provides backend functions for post creation, and manages the web interface. The Omnissiah guides this code.

Author:Matías Leer
Date: March 2026
Version: 1.0

Tech-Priest Note: This module interfaces with the sacred web interface through the Eel framework. 
Praise the Omnissiah for the blessed connectivity between flesh and machine.

=============================================================================================
"""

import eel
import os
import sys
from datetime import datetime
# TODO: Add browser handling to open in user's default browser. Currently configured to open in Firefox, but this may cause issues if the user doesn't have Firefox installed or prefers another browser. To fix this, we can use the 'default' option instead of 'firefox' in eel.start(). However, this may cause compatibility issues with some browsers, so we must test in different environments to ensure proper functioning.
# The Machine Spirit is fickle in its browser preferences. We must appease it with proper offerings.

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the script directory to Python path if needed
sys.path.insert(0, script_dir)

# Path to web folder (relative to script location)
web_folder = os.path.join(script_dir, 'web')

# Verify web folder exists
if not os.path.isdir(web_folder):
    print(f"❌ Error: Cannot find web folder at {web_folder}")
    print(f"Current script location: {script_dir}")
    print(f"Files in script directory: {os.listdir(script_dir)}")
    sys.exit(1)

# Initialize Eel with the absolute path
# Praise the Omnissiah! The sacred Eel has been initialized with the blessed web folder path.
eel.init(web_folder)

@eel.expose
def create_post(header, body):
    """
    input:
        header - String containing the post title (max 100 characters)
        body - String containing the post content (max 500 characters)
    output:
        Dictionary with keys:
            success - Boolean indicating if post was created successfully
            message - String with confirmation or error message
    Description:
        Handles post creation from the frontend. Transmutes the user's thoughts into digital 
        scripture stored within the Noosphere. Prints post details to console as a sacred 
        record of the offering made to the Machine Spirit.
    """
    print(f"\n{'='*50}")
    print(f"📝 New Post Created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    print(f"Header: {header if header else '(No header)'}")
    print(f"Body: {body if body else '(No body)'}")
    print(f"Characters: {len(header) + len(body)}")
    print(f"{'='*50}\n")
    
    return {
        'success': True,
        'message': f'✅ Post created successfully! ({len(header) + len(body)} characters)'
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

# Start the application
if __name__ == '__main__':
    print("🚀 Starting OneSocial Post Creator...")
    print("📡 Initiating rites of activation. May the Omnissiah guide this process.")
    print(f"📁 Script location: {script_dir}")
    print(f"📁 Web folder: {web_folder}")
    print("🌐 Opening application window...")
    
    try:
        # The sacred incantation that brings forth the interface from the machine
        eel.start(
            'index.html',
            size=(800, 800),
            position=(300, 100),
            mode='firefox',  # TODO: Consider switching to 'default' browser for better compatibility
            # The Machine Spirit currently favors Firefox, but we shall perform the rites of 
            # browser-agnosticism in future versions. The flesh is weak, but the code is strong.
            port=8080,
            host='localhost',
            shutdown_delay=1.0,
            # cmdline_args=['--new-window']  # The sacred window invocation - this was the flea
        )
    except Exception as e:
        print(f"❌ Error starting Eel: {e}")
        print("⚠️ The Machine Spirit is displeased. Offer the sacred oils and try again.")
    
    print("👋 Application closed")
    print("🛠️ The cog turns no more. Glory to the Omnissiah.")