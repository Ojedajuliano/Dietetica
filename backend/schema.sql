-- Esquema de la base de datos (Alineado al DER BaseV0.2)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id INTEGER NOT NULL,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (rol_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    marca TEXT,
    codigo_barras TEXT UNIQUE,
    categoria_id INTEGER NOT NULL,
    costo REAL NOT NULL DEFAULT 0,
    precio_venta REAL NOT NULL DEFAULT 0,
    stock_minimo REAL NOT NULL DEFAULT 0,
    stock_critico REAL NOT NULL DEFAULT 0,
    unidad_medida TEXT NOT NULL,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

-- Proveedores (implícito en productos_proveedores)
CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    cuit_cuil TEXT,
    telefono TEXT,
    email TEXT,
    direccion TEXT,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS productos_proveedores (
    producto_id INTEGER NOT NULL,
    proveedor_id INTEGER NOT NULL,
    es_habitual INTEGER DEFAULT 0,
    PRIMARY KEY (producto_id, proveedor_id),
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
);

CREATE TABLE IF NOT EXISTS compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    numero_factura TEXT,
    total REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS lotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    numero_lote TEXT,
    cantidad REAL NOT NULL,
    costo_unitario REAL NOT NULL,
    fecha_vencimiento TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE IF NOT EXISTS detalle_compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compra_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    lote_id INTEGER,
    cantidad REAL NOT NULL,
    costo_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (compra_id) REFERENCES compras(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (lote_id) REFERENCES lotes(id)
);

CREATE TABLE IF NOT EXISTS movimientos_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    lote_id INTEGER,
    tipo TEXT NOT NULL, -- ENTRADA, SALIDA, AJUSTE, DEVOLUCION
    cantidad REAL NOT NULL,
    motivo TEXT,
    fecha TEXT NOT NULL,
    usuario_id INTEGER NOT NULL,
    comentario TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (lote_id) REFERENCES lotes(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS fraccionamientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    producto_origen_id INTEGER NOT NULL,
    lote_origen_id INTEGER,
    producto_destino_id INTEGER NOT NULL,
    lote_destino_id INTEGER,
    cantidad_origen REAL NOT NULL,
    cantidad_destino REAL NOT NULL,
    fecha TEXT NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (producto_origen_id) REFERENCES productos(id),
    FOREIGN KEY (lote_origen_id) REFERENCES lotes(id),
    FOREIGN KEY (producto_destino_id) REFERENCES productos(id),
    FOREIGN KEY (lote_destino_id) REFERENCES lotes(id)
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT,
    dni TEXT UNIQUE,
    telefono TEXT,
    email TEXT,
    fecha_nacimiento TEXT,
    puntos INTEGER DEFAULT 0,
    limite_credito REAL DEFAULT 0,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    cliente_id INTEGER,
    fecha TEXT NOT NULL,
    subtotal REAL NOT NULL,
    descuento REAL DEFAULT 0,
    recargo REAL DEFAULT 0,
    total REAL NOT NULL,
    comentario TEXT,
    estado TEXT NOT NULL, -- COMPLETADA, ANULADA, PENDIENTE
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE IF NOT EXISTS detalle_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    lote_id INTEGER,
    cantidad REAL NOT NULL,
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (lote_id) REFERENCES lotes(id)
);

CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    metodo TEXT NOT NULL, -- EFECTIVO, TARJETA, TRANSFERENCIA, CUENTA_CORRIENTE
    monto REAL NOT NULL,
    monto_recibido REAL NOT NULL,
    vuelto REAL DEFAULT 0,
    fecha TEXT NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id)
);

CREATE TABLE IF NOT EXISTS devoluciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    tipo TEXT NOT NULL, -- TOTAL, PARCIAL
    motivo TEXT,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS detalle_devoluciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    devolucion_id INTEGER NOT NULL,
    detalle_venta_id INTEGER NOT NULL,
    cantidad REAL NOT NULL,
    FOREIGN KEY (devolucion_id) REFERENCES devoluciones(id),
    FOREIGN KEY (detalle_venta_id) REFERENCES detalle_ventas(id)
);

CREATE TABLE IF NOT EXISTS cajas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_apertura_id INTEGER NOT NULL,
    fecha_apertura TEXT NOT NULL,
    monto_inicial REAL NOT NULL,
    fecha_cierre TEXT,
    monto_esperado REAL,
    monto_real REAL,
    diferencia REAL,
    estado TEXT NOT NULL, -- ABIERTA, CERRADA
    FOREIGN KEY (usuario_apertura_id) REFERENCES usuarios(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_una_caja_abierta ON cajas(estado) WHERE estado = 'ABIERTA';

CREATE TABLE IF NOT EXISTS movimientos_caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caja_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    tipo TEXT NOT NULL, -- INGRESO, EGRESO
    concepto TEXT,
    monto REAL NOT NULL,
    fecha TEXT NOT NULL,
    venta_id INTEGER,
    FOREIGN KEY (caja_id) REFERENCES cajas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (venta_id) REFERENCES ventas(id)
);

CREATE TABLE IF NOT EXISTS cierres_caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caja_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    tipo TEXT NOT NULL, -- PARCIAL, FINAL
    fecha TEXT NOT NULL,
    monto_esperado REAL NOT NULL,
    monto_real REAL NOT NULL,
    diferencia REAL NOT NULL,
    FOREIGN KEY (caja_id) REFERENCES cajas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS movimientos_cuenta_cliente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    tipo TEXT NOT NULL, -- DEUDA, PAGO, AJUSTE
    monto REAL NOT NULL,
    descripcion TEXT,
    fecha TEXT NOT NULL,
    venta_id INTEGER,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (venta_id) REFERENCES ventas(id)
);

CREATE TABLE IF NOT EXISTS movimientos_cuenta_proveedor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    tipo TEXT NOT NULL, -- DEUDA, PAGO, AJUSTE
    monto REAL NOT NULL,
    descripcion TEXT,
    fecha TEXT NOT NULL,
    compra_id INTEGER,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (compra_id) REFERENCES compras(id)
);
