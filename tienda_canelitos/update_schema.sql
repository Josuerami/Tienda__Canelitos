-- Actualizar estructura de users si es necesario
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS role ENUM('admin', 'seller', 'delivery', 'client') DEFAULT 'client',
    ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE,
    MODIFY COLUMN username VARCHAR(255) NOT NULL,
    MODIFY COLUMN name VARCHAR(255) NOT NULL,
    MODIFY COLUMN password VARCHAR(255) NOT NULL;

-- Actualizar estructura de products
ALTER TABLE products
    ADD COLUMN IF NOT EXISTS category VARCHAR(100),
    ADD COLUMN IF NOT EXISTS stock INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS image VARCHAR(255) DEFAULT 'placeholder.svg',
    MODIFY COLUMN price DECIMAL(10,2) NOT NULL;

-- Actualizar estructura de orders
-- Cambiado para trabajar con la tabla de órdenes maestra `orders_master`.
-- Usamos VARCHAR(50) para evitar incompatibilidades de ENUM entre instalaciones.
ALTER TABLE orders_master
    ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Pendiente',
    ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50),
    ADD COLUMN IF NOT EXISTS quantity INT DEFAULT 1;

-- Insertar usuario admin por defecto si no existe
-- Nota: este INSERT usa contraseña en texto plano SOLO para entornos de desarrollo.
-- En producción, cambie la contraseña y almacénela hasheada (bcrypt/werkzeug).
INSERT IGNORE INTO users (username, name, password, role) 
VALUES ('admin', 'Administrador', 'admin123', 'admin');

-- Insertar productos de ejemplo si no existen
INSERT IGNORE INTO products (name, price, category, stock, image) VALUES 
('Coca-Cola 355ml', 15.00, 'Bebidas', 50, 'coca_cola_355ml.png'),
('Agua 1L', 12.00, 'Bebidas', 50, 'agua_1l.png'),
('Pan Blanco', 28.00, 'Panadería', 30, 'pan_blanco.jpg'),
('Leche 1L', 24.00, 'Lácteos', 40, 'leche_1l.jpg'),
('Papas Fritas', 18.00, 'Snacks', 45, 'papas_fritas.png'),
('Arroz 1kg', 32.00, 'Abarrotes', 35, 'arroz_1kg.png'),
('Servilletas', 20.00, 'Limpieza', 60, 'servilletas.png'),
('Jabón Líquido', 45.00, 'Limpieza', 25, 'jabon_liquido.png');