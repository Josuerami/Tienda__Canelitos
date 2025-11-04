import os
import urllib.request
import ssl

def download_file(url, filename):
    # Crear un contexto SSL sin verificación (solo para desarrollo)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        # Descargar el archivo
        urllib.request.urlretrieve(url, filename)
        print(f"Descargado: {filename}")
        return True
    except Exception as e:
        print(f"Error al descargar {filename}: {e}")
        return False

def main():
    # Crear directorio si no existe
    img_dir = os.path.join('static', 'img')
    os.makedirs(img_dir, exist_ok=True)
    
    # URLs de imágenes de productos de muestra
    images = {
        'coca_cola_355ml.png': 'https://cdn.pixabay.com/photo/2014/09/26/19/51/coca-cola-462776_1280.jpg',
        'agua_1l.png': 'https://cdn.pixabay.com/photo/2014/12/11/14/51/water-564048_1280.jpg',
        'pan_blanco.jpg': 'https://cdn.pixabay.com/photo/2016/03/26/18/23/bread-1280.jpg',
        'leche_1l.jpg': 'https://cdn.pixabay.com/photo/2017/07/05/15/41/milk-2474993_1280.jpg',
        'papas_fritas.png': 'https://cdn.pixabay.com/photo/2016/11/20/09/06/bowl-1842294_1280.jpg',
        'arroz_1kg.png': 'https://cdn.pixabay.com/photo/2014/10/22/18/43/rice-498688_1280.jpg',
        'servilletas.png': 'https://cdn.pixabay.com/photo/2015/02/02/11/09/paper-620517_1280.jpg',
        'jabon_liquido.png': 'https://cdn.pixabay.com/photo/2016/02/17/22/41/soap-1206024_1280.jpg'
    }
    
    # Descargar cada imagen
    for filename, url in images.items():
        filepath = os.path.join(img_dir, filename)
        print(f"Descargando {filename}...")
        download_file(url, filepath)

if __name__ == '__main__':
    main()