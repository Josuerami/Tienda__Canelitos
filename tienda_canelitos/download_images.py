import os
import requests
from PIL import Image
from io import BytesIO

def download_image(url, filename):
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        
        # Resize to a reasonable size (e.g., 400x400 max)
        image.thumbnail((400, 400))
        
        # Convert to RGB if saving as JPEG
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            image = image.convert('RGB')
        
        # Save with good quality
        image.save(filename, optimize=True, quality=85)
        print(f"Successfully downloaded and saved {filename}")
        return True
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")
        return False

def create_placeholder():
    img_dir = os.path.join('static', 'img')
    placeholder_svg = '''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="200" fill="#f8d7da"/>
        <text x="100" y="100" text-anchor="middle" font-family="Arial" font-size="16" fill="#721c24">Product Image</text>
        <text x="100" y="120" text-anchor="middle" font-family="Arial" font-size="12" fill="#721c24">Placeholder</text>
    </svg>'''
    
    placeholder_path = os.path.join(img_dir, "placeholder.svg")
    with open(placeholder_path, 'w', encoding='utf-8') as f:
        f.write(placeholder_svg)
    print("Created: placeholder.svg")
    return placeholder_path

def main():
    # Create img directory if it doesn't exist
    img_dir = os.path.join('static', 'img')
    os.makedirs(img_dir, exist_ok=True)
    
    # Create placeholder first
    create_placeholder()
    
    # Imágenes de logos de programación
    images = {
        'coca_cola_355ml.png': 'https://raw.githubusercontent.com/github/explore/main/topics/python/python.png',
        'agua_1l.png': 'https://raw.githubusercontent.com/github/explore/main/topics/javascript/javascript.png',
        'pan_blanco.jpg': 'https://raw.githubusercontent.com/github/explore/main/topics/java/java.png',
        'leche_1l.jpg': 'https://raw.githubusercontent.com/github/explore/main/topics/html/html.png',
        'papas_fritas.png': 'https://raw.githubusercontent.com/github/explore/main/topics/css/css.png',
        'arroz_1kg.png': 'https://raw.githubusercontent.com/github/explore/main/topics/nodejs/nodejs.png',
        'servilletas.png': 'https://raw.githubusercontent.com/github/explore/main/topics/react/react.png',
        'jabon_liquido.png': 'https://raw.githubusercontent.com/github/explore/main/topics/vue/vue.png'
    }
    
    # Download each image
    for filename, url in images.items():
        filepath = os.path.join(img_dir, filename)
        print(f"Downloading {filename}...")
        download_image(url, filepath)

if __name__ == "__main__":
    main()
