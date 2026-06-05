# app/models/import_export.py

import os
import json
import base64
import shutil
from datetime import datetime
import eel

# ========== CONFIGURACIÓN DE RUTAS ==========
ONESOCIAL_DIR = os.path.expanduser("~/.onesocial")
DATA_FILE = os.path.join(ONESOCIAL_DIR, "data.dat")
POSTS_DIR = os.path.join(ONESOCIAL_DIR, "posts")
IMAGES_DIR = os.path.join(ONESOCIAL_DIR, "images")

def ensure_dirs():
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

def backup_existing_data():
    """Crea un respaldo completo antes de importar."""
    backup_dir = os.path.join(ONESOCIAL_DIR, "backups", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(backup_dir, exist_ok=True)
    if os.path.exists(DATA_FILE):
        shutil.copy(DATA_FILE, os.path.join(backup_dir, "data.dat"))
    if os.path.exists(POSTS_DIR):
        shutil.copytree(POSTS_DIR, os.path.join(backup_dir, "posts"))
    if os.path.exists(IMAGES_DIR):
        shutil.copytree(IMAGES_DIR, os.path.join(backup_dir, "images"))

@eel.expose
def export_all_data():
    """Exporta data.dat y todos los posts (con imágenes embebidas)."""
    ensure_dirs()
    
    # Leer data.dat
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data_content = json.load(f)
    else:
        data_content = {"salt": "", "data": {"tokens": [], "post_counter": 0}}
    
    # Leer posts
    posts_list = []
    if os.path.exists(POSTS_DIR):
        for filename in os.listdir(POSTS_DIR):
            if filename.endswith('.post'):
                filepath = os.path.join(POSTS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    post = json.load(f)
                
                image_filename = None
                image_base64 = None
                if post.get('image') and os.path.exists(post['image']):
                    image_filename = os.path.basename(post['image'])
                    with open(post['image'], 'rb') as img_f:
                        image_base64 = base64.b64encode(img_f.read()).decode('utf-8')
                
                portable_post = {
                    "id": post.get('id'),
                    "title": post.get('title'),
                    "content": post.get('content'),
                    "selected_accounts": post.get('selected_accounts', []),
                    "scheduled_time": post.get('scheduled_time'),
                    "image_filename": image_filename,
                    "image_base64": image_base64
                }
                posts_list.append(portable_post)
    
    return {
        "exportVersion": "1.0",
        "exportDate": datetime.utcnow().isoformat() + "Z",
        "dataFile": data_content,
        "posts": posts_list
    }

@eel.expose
def import_all_data(imported_data):
    """Restaura data.dat, posts e imágenes desde un archivo de exportación."""
    if 'exportVersion' not in imported_data or 'dataFile' not in imported_data or 'posts' not in imported_data:
        raise ValueError("Formato de importación inválido")
    
    backup_existing_data()
    
    # Restaurar data.dat
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(imported_data['dataFile'], f, indent=2)
    
    # Limpiar y recrear carpetas
    if os.path.exists(POSTS_DIR):
        shutil.rmtree(POSTS_DIR)
    if os.path.exists(IMAGES_DIR):
        shutil.rmtree(IMAGES_DIR)
    ensure_dirs()
    
    # Restaurar cada post
    for portable_post in imported_data['posts']:
        image_path = None
        if portable_post.get('image_filename') and portable_post.get('image_base64'):
            image_filename = portable_post['image_filename']
            image_path = os.path.join(IMAGES_DIR, image_filename)
            with open(image_path, 'wb') as img_f:
                img_f.write(base64.b64decode(portable_post['image_base64']))
        
        restored_post = {
            "id": portable_post['id'],
            "title": portable_post['title'],
            "content": portable_post['content'],
            "selected_accounts": portable_post['selected_accounts'],
            "scheduled_time": portable_post['scheduled_time'],
            "image": image_path
        }
        post_filename = f"{restored_post['id']}.post"
        with open(os.path.join(POSTS_DIR, post_filename), 'w', encoding='utf-8') as f:
            json.dump(restored_post, f, indent=2)
    
    return {"status": "ok", "message": f"Importados {len(imported_data['posts'])} posts."}