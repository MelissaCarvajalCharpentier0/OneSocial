"""

=============================================================================================

Name: functions_post.py
Description: Module for obtaining the content of the post, including title, text, and image.
Author: Pamela Fernández
Date: March 2026
Version: 1.0

=============================================================================================

"""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
from models.token_manager import *



def get_image_post():
    """
    - Output: 
        - get_image(ruta): str - The name of the copied image file
    - Description: 
        - Opens a file dialog for the user to select an image file, copies the selected image to a designated folder, and returns the name of the copied image file.
    """

    root = tk.Tk()
    root.withdraw()

    ruta_str = filedialog.askopenfilename(
        title="Selecciona un archivo",
        filetypes=[
            ("Imágenes", "*.png *.jpg *.jpeg *.JPG *.JPEG *.PNG"),
        ]
    )

    print("Ruta seleccionada:", ruta_str)

    if not ruta_str:
        print("No se seleccionó ningún archivo.")
        return

    ruta = Path(ruta_str)
    return get_image(ruta)


def get_title_post():
    """
    - Output: 
        - text: str - The title of the post entered by the user
    - Description: 
        - Opens a dialog for the user to enter the title of the post and returns the entered title.
    """

    root = tk.Tk()
    root.withdraw()
    
    text = simpledialog.askstring("Post", "Escribe el título del post:")
    return text


def get_content_post():
    """ 
    - Output: 
        - text: str - The content of the post entered by the user
    - Description: 
        - Opens a dialog for the user to enter the content of the post and returns the entered content.
    """

    root = tk.Tk()
    root.withdraw()
    
    text = simpledialog.askstring("Post", "Escribe el texto del post:")
    return text


def create_post_title_content_image():
    """
    - Output: 
        - {"title": title, "content": content, "image": img_post}: dict - A dictionary containing the title, content, and image of the post
    - Description: 
        - Creates a post with a title, content, and image by calling the respective functions to obtain each component.
    """

    title = get_title_post()
    content = get_content_post()
    img_post = get_image_post()
    
    return {"title": title, "content": content, "image": img_post}


def create_post_title_content():
    """
    - Output: 
        - {"title": title, "content": content}: dict - A dictionary containing the title and content of the post
    - Description: 
        - Creates a post with a title and content by calling the respective functions to obtain each component.
    """

    title = get_title_post()
    content = get_content_post()
    
    return {"title": title, "content": content}


def create_post_title_image():
    """
    - Output: 
        - {"title": title, "image": img_post}: dict - A dictionary containing the title and image of the post
    - Description: 
        - Creates a post with a title and image by calling the respective functions to obtain each component.
    """

    title = get_title_post()
    img_post = get_image_post()
    
    return {"title": title, "image": img_post}


def create_post_content_image():
    """
    - Output: 
        - {"content": content, "image": img_post}: dict - A dictionary containing the content and image of the post
    - Description: 
        - Creates a post with content and an image by calling the respective functions to obtain each component.
    """

    content = get_content_post()
    img_post = get_image_post()
    
    return {"content": content, "image": img_post}


def create_post_content():
    """
    - Output: 
        - {"content": content}: dict - A dictionary containing the content of the post
    - Description: 
        - Creates a post with content by calling the function to obtain the content of the post.
    """

    content = get_content_post()
    return {"content": content}