from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, send_from_directory
import pymysql
import os
import io
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'canelitos_secret_key'

def get_db():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DB', 'tienda_canelitos'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def require_role(*roles):
    def wrapper(f):
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                flash("Acceso denegado.")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return wrapper

# === LOGIN ===
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        pwd = request.form['password']
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, name, role FROM users WHERE username = %s AND password = %s AND active = 1", (user, pwd))
            u = cur.fetchone()
        conn.close()
        if u:
            session['user_id'] = u['id']
            session['user'] = u['username']
            session['user_name'] = u['name']
            session['user_role'] = u['role']
            return redirect(url_for('home'))
        flash("Credenciales inválidas o usuario inactivo.")
    return render_template('login.html')

# === HOME (redirige por rol) ===
@app.route('/home')
def home():
    if 'user_role' not in session:
        return redirect(url_for('login'))
    if session['user_role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif session['user_role'] == 'seller':
        return redirect(url_for('seller_dashboard'))
    elif session['user_role'] == 'delivery':
        return redirect(url_for('delivery_orders'))
    else:  # client
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products")
            products = cur.fetchall()
        conn.close()
        return render_template('home.html', products=products)

# === CLIENTE: PRODUCTOS Y CARRITO ===
@app.route('/product/<int:pid>')
@require_role('client')
def product_detail(pid):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM products WHERE id = %s", (pid,))
        product = cur.fetchone()
    conn.close()
    if not product:
        flash("Producto no encontrado")
        return redirect(url_for('home'))
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<int:pid>')
@require_role('client')
def add_to_cart(pid):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM products WHERE id = %s AND stock > 0", (pid,))
        p = cur.fetchone()
    conn.close()
    if p:
        session.setdefault('cart', []).append({'id': p['id'], 'name': p['name'], 'price': float(p['price'])})
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart')
@require_role('client')
def cart():
    items = session.get('cart', [])
    total = sum(item['price'] for item in items)
    return render_template('cart.html', cart=items, total=total)

@app.route('/cart/remove/<int:index>', methods=['POST'])
@require_role('client')
def cart_remove(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart/clear', methods=['POST'])
@require_role('client')
def cart_clear():
    session['cart'] = []
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
@require_role('client')
def checkout():
    cart = session.get('cart', [])
    method = request.form.get('payment_method')
    if not cart or not method:
        flash("Carrito vacío o método de pago no seleccionado.")
        return redirect(url_for('cart'))
    
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for item in cart:
                cur.execute("""
                    INSERT INTO orders (user_id, product_id, quantity, total, payment_method)
                    VALUES (%s, %s, 1, %s, %s)
                """, (session['user_id'], item['id'], item['price'], method))
            # Reducir stock
            for item in cart:
                cur.execute("UPDATE products SET stock = stock - 1 WHERE id = %s", (item['id'],))
        conn.commit()
        session['cart'] = []
        flash("¡Compra confirmada!")
    except Exception as e:
        flash("Error al procesar la compra.")
    finally:
        conn.close()
    return redirect(url_for('home'))

# === ADMIN ===
@app.route('/admin')
@require_role('admin')
def admin_dashboard():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(total), 0) AS ventas FROM orders WHERE DATE(created_at) = CURDATE()")
        ventas = cur.fetchone()['ventas']
        cur.execute("SELECT COUNT(*) AS tickets FROM orders WHERE DATE(created_at) = CURDATE()")
        tickets = cur.fetchone()['tickets']
        cur.execute("SELECT COUNT(*) AS empleados FROM users WHERE role IN ('seller','delivery') AND active = 1")
        empleados = cur.fetchone()['empleados']
    conn.close()
    return render_template('admin/dashboard.html', ventas=ventas, tickets=tickets, empleados=empleados)

@app.route('/admin/users')
@require_role('admin')
def admin_users():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE role != 'admin'")
        users = cur.fetchall()
    conn.close()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/create', methods=['GET', 'POST'])
@require_role('admin')
def admin_create_user():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        role = request.form['role']
        if role not in ['client', 'seller', 'delivery']:
            flash("Rol inválido.")
            return redirect(url_for('admin_create_user'))
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (username, name, password, role) VALUES (%s, %s, %s, %s)",
                           (username, name, password, role))
            conn.commit()
            flash("Usuario creado.")
            return redirect(url_for('admin_users'))
        except:
            flash("Error: usuario ya existe.")
        finally:
            conn.close()
    return render_template('admin/create_user.html')

@app.route('/admin/products')
@require_role('admin', 'seller')
def admin_products():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM products")
        products = cur.fetchall()
    conn.close()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/create', methods=['GET', 'POST'])
@require_role('admin', 'seller')
def admin_create_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        stock = request.form['stock']
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO products (name, price, category, stock, image)
                    VALUES (%s, %s, %s, %s, 'placeholder.svg')
                """, (name, price, category, stock))
            conn.commit()
            flash("Producto creado.")
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash("Error al crear producto.")
        finally:
            conn.close()
    return render_template('admin/create_product.html')

@app.route('/admin/orders')
@require_role('admin', 'seller', 'delivery')
def admin_orders():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT o.*, u.name as cliente, p.name as producto
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            ORDER BY o.created_at DESC
        """)
        orders = cur.fetchall()
    conn.close()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/update/<int:oid>', methods=['POST'])
@require_role('admin', 'seller', 'delivery')
def update_order_status(oid):
    status = request.form['status']
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET status = %s WHERE id = %s", (status, oid))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_orders'))

@app.route('/admin/report')
@require_role('admin')
def admin_report():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT o.created_at, u.name as cliente, p.name as producto, o.total, o.payment_method
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            WHERE DATE(o.created_at) = CURDATE()
        """)
        orders = cur.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Cliente', 'Producto', 'Total', 'Método de Pago'])
    for o in orders:
        writer.writerow([o['created_at'], o['cliente'], o['producto'], o['total'], o['payment_method']])
    output.seek(0)
    
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='reporte_ventas.csv')

# === VENDEDOR ===
@app.route('/seller')
@require_role('seller')
def seller_dashboard():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(total), 0) AS ventas FROM orders WHERE DATE(created_at) = CURDATE()")
        ventas = cur.fetchone()['ventas']
        cur.execute("SELECT COUNT(*) AS tickets FROM orders WHERE DATE(created_at) = CURDATE()")
        tickets = cur.fetchone()['tickets']
    conn.close()
    return render_template('seller/dashboard.html', ventas=ventas, tickets=tickets)

# === REPARTIDOR ===
@app.route('/delivery')
@require_role('delivery')
def delivery_orders():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT o.*, u.name as cliente, p.name as producto
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            WHERE o.status IN ('Pendiente', 'En camino')
            ORDER BY o.created_at DESC
        """)
        orders = cur.fetchall()
    conn.close()
    return render_template('delivery/orders.html', orders=orders)

# === PERFIL ===
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET name = %s, username = %s WHERE id = %s",
                       (name, contact, session['user_id']))
        conn.commit()
        session['user'] = contact
        session['user_name'] = name
        flash("Perfil actualizado.")
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# === SERVICIO DE IMÁGENES ===
@app.route('/img/<path:filename>')
def img(filename):
    if '..' in filename:
        return "Invalid path", 400
    return send_file(os.path.join('static', 'img', filename))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)