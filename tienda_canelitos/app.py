from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, send_from_directory
import pymysql
import os
import csv
import io
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'canelitos_secret_key'

# Productos estáticos (nombre -> precio, imagen en static/img)
PRODUCTS = {
    'Coca-Cola 355 ml': {'price': 15.00, 'image': 'coca_cola_355ml.png'},
    'Agua Purificada 1L': {'price': 12.00, 'image': 'agua_1l.png'},
    'Pan Blanco': {'price': 28.00, 'image': 'pan_blanco.jpg'},
    'Leche Entera 1L': {'price': 24.00, 'image': 'leche_1l.jpg'},
    'Papas Fritas': {'price': 18.00, 'image': 'papas_fritas.png'},
    'Arroz 1kg': {'price': 32.00, 'image': 'arroz_1kg.png'},
    'Servilletas': {'price': 20.00, 'image': 'servilletas.png'},
    'Jabón Líquido': {'price': 45.00, 'image': 'jabon_liquido.png'}
}


def get_db():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DB', 'tienda_canelitos'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# === LOGIN ===
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (user,))
            u = cur.fetchone()
        conn.close()
        if u:
            session['user'] = u['username']
            return redirect(url_for('home'))
        flash("Usuario no registrado.")
    return render_template('login.html')

# === REGISTER ===
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '')
        user = request.form['user']
        pwd = request.form['password']
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (username, name, password) VALUES (%s, %s, %s)",
                           (user, name, pwd))
            conn.commit()
            session['user'] = user
            flash('Cuenta creada correctamente. ¡Bienvenido a Tienda Canelitos!')
            return redirect(url_for('home'))
        except Exception as e:
            flash("Error al registrar. Usuario ya existe o dato inválido.")
        finally:
            conn.close()
    return render_template('register.html')

# === HOME (Productos: 7 MILK + 1 vacío) ===
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    # Preparar productos para la plantilla asegurando que la imagen exista en static/img
    products_safe = {}
    img_dir = os.path.join(app.root_path, 'static', 'img')
    for name, info in PRODUCTS.items():
        image_file = info.get('image', 'placeholder.svg')
        if not os.path.exists(os.path.join(img_dir, image_file)):
            image_file = 'placeholder.svg'
        products_safe[name] = {'price': info.get('price', 0.0), 'image': image_file}
    return render_template('home.html', user=session['user'], products=products_safe)

# === DETALLE DE PRODUCTO (texto literal del PDF) ===
@app.route('/product/<name>')
def product_detail(name):
    # Buscar información del producto en el catálogo estático
    product_info = PRODUCTS.get(name)
    # Asegurar que la imagen exista; si no, usar placeholder
    if product_info:
        img_path = os.path.join(app.root_path, 'static', 'img', product_info.get('image', ''))
        if not os.path.exists(img_path):
            product_info = {'price': product_info.get('price', 0.0), 'image': 'placeholder.svg'}
    return render_template('product_detail.html', product_name=name, product_info=product_info)

# === CARRITO (siempre agrega Coca-Cola como en el PDF) ===
@app.route('/add_to_cart/<name>')
def add_to_cart(name):
    if 'cart' not in session:
        session['cart'] = []
    # Agrega producto con precio dinámico (usar PRODUCTS como fuente única)
    price = PRODUCTS.get(name, {}).get('price', 15.00)
    session['cart'].append({
        "name": name or "Coca-Cola 355 ml",
        "price": price
    })
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if 'user' not in session:
        return redirect(url_for('login'))
    items = session.get('cart', [])
    total = sum(float(item['price']) for item in items)
    return render_template('cart.html', cart=items, total=total)

@app.route('/cart/clear', methods=['POST'])
def cart_clear():
    session['cart'] = []
    session.modified = True
    flash('Carrito eliminado')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:index>', methods=['POST'])
def cart_remove(index):
    items = session.get('cart', [])
    if 0 <= index < len(items):
        items.pop(index)
        session['cart'] = items
        session.modified = True
        flash('Producto eliminado')
    return redirect(url_for('cart'))

@app.route('/cart/payment/<method>', methods=['POST'])
def set_payment_method(method):
    if method not in ['transferencia','tarjeta','efectivo']:
        flash('Método de pago inválido')
        return redirect(url_for('cart'))
    session['payment_method'] = method
    session.modified = True
    flash(f'Método de pago seleccionado: {method}')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    # Simula guardar pedido y vaciar carrito
    items = session.get('cart', [])
    if not items:
        flash('El carrito está vacío')
        return redirect(url_for('cart'))
    method = session.get('payment_method')
    if not method:
        flash('Selecciona un método de pago antes de confirmar')
        return redirect(url_for('cart'))
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # Crea un pedido muy simple
            cur.execute("INSERT INTO orders (description) VALUES (%s)", (f"{len(items)} productos - pago: {method}",))
        conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
    session['cart'] = []
    session.modified = True
    flash(f'Compra confirmada. Pago por {method}.')
    return redirect(url_for('home'))

# === ADMIN (con datos estáticos del PDF) ===
@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin/inventory')
def admin_inventory():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM inventory")
        inv = cur.fetchall()
    conn.close()
    return render_template('admin_inventory.html', inventory=inv)

@app.route('/admin/orders')
def admin_orders():
    conn = get_db()
    orders = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM orders")
            orders = cur.fetchall()
    except Exception:
        orders = []
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/report')
def admin_report():
    # Intentar generar PDF con WeasyPrint; si falla, devolver HTML imprimible
    orders = []
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT id, description FROM orders")
            orders = cur.fetchall()
    except Exception:
        orders = []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    html = render_template('report_orders.html', orders=orders)
    try:
        from weasyprint import HTML
        pdf_io = io.BytesIO()
        HTML(string=html).write_pdf(pdf_io)
        pdf_io.seek(0)
        return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='reporte_pedidos.pdf')
    except Exception:
        # Fallback: HTML imprimible
        mem = io.BytesIO()
        mem.write(html.encode('utf-8'))
        mem.seek(0)
        return send_file(mem, mimetype='text/html', as_attachment=True, download_name='reporte_pedidos.html')

# === VENDEDOR ===
@app.route('/seller')
def seller():
    return render_template('seller.html')

# === PERFIL Y CIERRE ===
@app.route('/profile')
def profile():
    username = session.get('user', '')
    display_name = ''
    if username:
        try:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM users WHERE username=%s", (username,))
                row = cur.fetchone()
                display_name = row.get('name') if row else ''
        except Exception:
            display_name = ''
        finally:
            try:
                conn.close()
            except Exception:
                pass
    return render_template('profile.html', user=username, display_name=display_name)

@app.route('/profile/name', methods=['POST'])
def update_name():
    if 'user' not in session:
        return redirect(url_for('login'))
    new_name = request.form.get('name', '').strip()
    if not new_name:
        flash('El nombre no puede estar vacío')
        return redirect(url_for('profile'))
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET name=%s WHERE username=%s", (new_name, session['user']))
        conn.commit()
        flash('Nombre actualizado correctamente')
    except Exception:
        flash('No se pudo actualizar el nombre')
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return redirect(url_for('profile'))

@app.route('/profile/contact', methods=['POST'])
def update_contact():
    if 'user' not in session:
        return redirect(url_for('login'))
    new_contact = request.form.get('contact', '').strip()
    if not new_contact:
        flash('El correo/teléfono no puede estar vacío')
        return redirect(url_for('profile'))
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # Asumimos que username es el campo de contacto/login; si tienes columna separada, cámbiala
            cur.execute("UPDATE users SET username=%s WHERE username=%s", (new_contact, session['user']))
        conn.commit()
        session['user'] = new_contact
        flash('Correo/Teléfono actualizado correctamente')
    except Exception:
        flash('No se pudo actualizar el correo/teléfono (posible duplicado)')
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# === CONTACTO ===
@app.route('/contact')
def contact():
    return render_template('contact.html')


# --- Debug: listar imágenes estáticas / probar carga ---
@app.route('/debug/images')
def debug_images():
    img_dir = os.path.join(app.root_path, 'static', 'img')
    files = []
    try:
        files = [f for f in os.listdir(img_dir) if os.path.isfile(os.path.join(img_dir, f))]
    except Exception:
        files = []
    # Generar HTML simple con las imágenes
    parts = ['<h2>Imágenes en static/img</h2>']
    for f in files:
        url = url_for('static', filename='img/' + f)
        parts.append(f"<div style='display:inline-block;margin:8px;text-align:center;'><img src='{url}' style='width:120px;height:120px;object-fit:cover;border:1px solid #ddd;border-radius:6px;display:block;margin-bottom:6px;'/><div style='font-size:12px;'>{f}</div></div>")
    if not files:
        parts.append('<p>No se encontraron archivos en static/img</p>')
    return '\n'.join(parts)


# Ruta explícita para servir imágenes desde static/img (más robusta que confiar sólo en /static)
@app.route('/images/<path:filename>')
def images(filename):
    img_dir = os.path.join(app.root_path, 'static', 'img')
    # Seguridad mínima: evita rutas con ..
    if '..' in filename or filename.startswith('/'):
        return "Invalid filename", 400
    return send_from_directory(img_dir, filename)

# === INICIO DEL SERVIDOR ===
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)