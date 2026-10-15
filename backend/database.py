import math
import os
import re
import sqlite3
from datetime import date, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dietetica.db")

CATEGORIAS = [
    "Proteínas",
    "Creatinas",
    "Vitaminas",
    "Frutos secos",
    "Cereales",
    "Harinas",
    "Infusiones",
    "Endulzantes",
    "Snacks",
    "Otros",
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _columnas(conn, tabla):
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({tabla})")}


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.execute("INSERT OR IGNORE INTO roles (id, nombre) VALUES (1, 'Administrador')")
    conn.execute("INSERT OR IGNORE INTO roles (id, nombre) VALUES (2, 'Empleado')")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol_id INTEGER NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (rol_id) REFERENCES roles(id)
        )
        """
    )
    conn.execute("INSERT OR IGNORE INTO usuarios (usuario, nombre, password_hash, rol_id) VALUES ('admin', 'Administrador', '123', 1)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            marca TEXT NOT NULL DEFAULT '',
            codigo_barras TEXT UNIQUE,
            categoria_id INTEGER NOT NULL,
            costo REAL NOT NULL DEFAULT 0,
            precio_venta REAL NOT NULL DEFAULT 0,
            stock_minimo REAL NOT NULL DEFAULT 0,
            stock_critico REAL NOT NULL DEFAULT 0,
            unidad_medida TEXT NOT NULL DEFAULT 'unidad',
            activo INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS marcas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE COLLATE NOCASE
        )
        """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO marcas (nombre)
        SELECT DISTINCT trim(marca)
        FROM productos
        WHERE marca IS NOT NULL AND trim(marca) != ''
        """
    )
    columnas = _columnas(conn, "productos")
    campos_nuevos = {
        "categoria": "TEXT NOT NULL DEFAULT ''",
        "codigo_interno": "INTEGER NOT NULL DEFAULT 0",
        "tipo_venta": "TEXT NOT NULL DEFAULT 'unidad'",
        "stock": "REAL NOT NULL DEFAULT 0",
        "proveedor": "TEXT NOT NULL DEFAULT ''",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    }
    agregadas = set()
    for nombre, definicion in campos_nuevos.items():
        if nombre not in columnas:
            conn.execute(f"ALTER TABLE productos ADD COLUMN {nombre} {definicion}")
            agregadas.add(nombre)

    for categoria in CATEGORIAS:
        conn.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (categoria,))

    if "categoria" in agregadas:
        conn.execute(
            """
            UPDATE productos SET categoria = COALESCE(
                (SELECT nombre FROM categorias WHERE categorias.id = productos.categoria_id),
                'Otros'
            )
            """
        )
    if "tipo_venta" in agregadas and "unidad_medida" in columnas:
        conn.execute(
            """
            UPDATE productos SET tipo_venta = CASE
                WHEN lower(unidad_medida) LIKE '%kg%' OR lower(unidad_medida) LIKE '%peso%'
                THEN 'peso' ELSE 'unidad' END
            """
        )
    if "stock" in agregadas and "lotes" in {
        row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }:
        conn.execute(
            """
            UPDATE productos SET stock = COALESCE(
                (SELECT SUM(cantidad) FROM lotes WHERE lotes.producto_id = productos.id), 0
            )
            """
        )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            costo_unitario REAL NOT NULL,
            fecha_vencimiento TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
        """
    )
    if "codigo_lote" not in _columnas(conn, "lotes"):
        conn.execute("ALTER TABLE lotes ADD COLUMN codigo_lote TEXT NOT NULL DEFAULT ''")

    conn.execute(
        """
        UPDATE productos SET codigo_barras = 'INT-' || printf('%06d', id),
            codigo_interno = id
        WHERE codigo_barras IS NULL OR trim(codigo_barras) = ''
        """
    )
    conn.execute(
        """
        UPDATE productos SET categoria = 'Otros'
        WHERE categoria IS NULL OR trim(categoria) = ''
        """
    )
    conn.execute(
        """
        UPDATE productos SET created_at = COALESCE(created_at, datetime('now', 'localtime')),
            updated_at = COALESCE(updated_at, datetime('now', 'localtime'))
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inventario_movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            lote_id INTEGER,
            tipo TEXT NOT NULL,
            cantidad REAL NOT NULL,
            motivo TEXT NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (lote_id) REFERENCES lotes(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL DEFAULT 1,
            cliente_id INTEGER,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            subtotal REAL NOT NULL,
            descuento REAL NOT NULL DEFAULT 0,
            recargo REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL,
            comentario TEXT,
            estado TEXT NOT NULL DEFAULT 'COMPLETADA'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cajas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_apertura_id INTEGER NOT NULL,
            fecha_apertura TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            monto_inicial REAL NOT NULL,
            fecha_cierre TEXT,
            monto_esperado REAL,
            monto_real REAL,
            diferencia REAL,
            estado TEXT NOT NULL DEFAULT 'ABIERTA',
            FOREIGN KEY (usuario_apertura_id) REFERENCES usuarios(id)
        )
        """
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_una_caja_abierta "
        "ON cajas(estado) WHERE estado = 'ABIERTA'"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS movimientos_caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caja_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            concepto TEXT,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            venta_id INTEGER,
            FOREIGN KEY (caja_id) REFERENCES cajas(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (venta_id) REFERENCES ventas(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cierres_caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caja_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            monto_esperado REAL NOT NULL,
            monto_real REAL NOT NULL,
            diferencia REAL NOT NULL,
            FOREIGN KEY (caja_id) REFERENCES cajas(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        """
    )
    conn.execute(
        """
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
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS compras_registradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor TEXT NOT NULL DEFAULT '',
            numero_factura TEXT NOT NULL DEFAULT '',
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            total REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS detalle_compras_registradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            lote_id INTEGER,
            cantidad REAL NOT NULL,
            costo_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (compra_id) REFERENCES compras_registradas(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (lote_id) REFERENCES lotes(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lotes_vencimiento ON lotes(fecha_vencimiento)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventario_movimientos_fecha "
        "ON inventario_movimientos(fecha)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS registro_actividad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            accion TEXT NOT NULL,
            detalle TEXT NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_registro_actividad_fecha "
        "ON registro_actividad(fecha DESC)"
    )
    conn.commit()
    conn.close()


def _numero(valor, nombre):
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        raise ValueError(f"{nombre} debe ser un número")
    if not math.isfinite(numero):
        raise ValueError(f"{nombre} debe ser un número válido")
    return numero


def _producto_desde_row(row):
    if not row:
        return None
    producto = dict(row)
    producto["estado_stock"] = calcular_estado_stock(producto)
    return producto


def calcular_estado_stock(producto):
    stock = float(producto["stock"] or 0)
    critico = float(producto["stock_critico"] or 0)
    minimo = float(producto["stock_minimo"] or 0)
    if stock <= 0:
        return "sin_stock"
    if critico > 0 and stock <= critico:
        return "critico"
    if minimo > 0 and stock <= minimo:
        return "minimo"
    return "ok"


def siguiente_codigo_interno(conn):
    row = conn.execute("SELECT COALESCE(MAX(codigo_interno), 0) AS n FROM productos").fetchone()
    numero = int(row["n"]) + 1
    while codigo_existe(conn, generar_codigo_interno(numero)):
        numero += 1
    return numero


def generar_codigo_interno(numero):
    return f"INT-{numero:06d}"


def _obtener_producto_conn(conn, producto_id):
    return conn.execute(
        """
        SELECT p.*, COALESCE(c.nombre, p.categoria, 'Otros') AS categoria
        FROM productos p
        LEFT JOIN categorias c ON c.id = p.categoria_id
        WHERE p.id = ?
        """,
        (producto_id,),
    ).fetchone()


def obtener_producto(producto_id):
    conn = get_connection()
    producto = _producto_desde_row(_obtener_producto_conn(conn, producto_id))
    conn.close()
    return producto


def listar_productos(busqueda="", filtro="", categoria="", proveedor="", marca=""):
    conn = get_connection()
    sql = """
        SELECT p.*, COALESCE(c.nombre, p.categoria, 'Otros') AS categoria,
            (SELECT MIN(l.fecha_vencimiento) FROM lotes l
             WHERE l.producto_id = p.id AND l.cantidad > 0
                AND l.fecha_vencimiento >= date('now', 'localtime')) AS proximo_vencimiento
        FROM productos p
        LEFT JOIN categorias c ON c.id = p.categoria_id
        WHERE COALESCE(p.activo, 1) = 1
    """
    params = []
    if busqueda:
        sql += " AND (p.nombre LIKE ? OR p.marca LIKE ? OR p.codigo_barras LIKE ?)"
        like = f"%{busqueda}%"
        params.extend([like, like, like])
    if categoria:
        sql += " AND COALESCE(c.nombre, p.categoria) = ?"
        params.append(categoria)
    if proveedor:
        sql += " AND p.proveedor = ?"
        params.append(proveedor)
    if marca:
        sql += " AND p.marca = ?"
        params.append(marca)
    sql += " ORDER BY p.nombre COLLATE NOCASE"
    productos = [_producto_desde_row(row) for row in conn.execute(sql, params)]
    conn.close()

    if filtro == "sin_stock":
        productos = [p for p in productos if p["estado_stock"] == "sin_stock"]
    elif filtro == "bajo_minimo":
        productos = [p for p in productos if p["estado_stock"] in ("minimo", "critico")]
    elif filtro == "critico":
        productos = [p for p in productos if p["estado_stock"] == "critico"]
    elif filtro == "proximo_vencer":
        limite = (date.today() + timedelta(days=30)).isoformat()
        hoy = date.today().isoformat()
        productos = [
            p for p in productos
            if p["proximo_vencimiento"] and hoy <= p["proximo_vencimiento"][:10] <= limite
        ]
    return productos


def codigo_existe(conn, codigo, excluir_id=None):
    if excluir_id:
        row = conn.execute(
            "SELECT id FROM productos WHERE codigo_barras = ? AND id != ?",
            (codigo, excluir_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM productos WHERE codigo_barras = ?", (codigo,)
        ).fetchone()
    return row is not None


def _obtener_categoria_id(conn, nombre):
    conn.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (nombre,))
    return conn.execute(
        "SELECT id FROM categorias WHERE nombre = ?", (nombre,)
    ).fetchone()["id"]


def _registrar_movimiento(conn, producto_id, tipo, cantidad, motivo, lote_id=None):
    conn.execute(
        """
        INSERT INTO inventario_movimientos (producto_id, lote_id, tipo, cantidad, motivo)
        VALUES (?, ?, ?, ?, ?)
        """,
        (producto_id, lote_id, tipo, cantidad, motivo),
    )


def crear_producto(data):
    conn = get_connection()
    fecha_vencimiento = data.get("fecha_vencimiento")
    if fecha_vencimiento:
        try:
            fecha_vencimiento = date.fromisoformat(fecha_vencimiento).isoformat()
        except (TypeError, ValueError):
            conn.close()
            raise ValueError("La fecha de vencimiento debe ser una fecha válida")

    codigo = (data.get("codigo_barras") or "").strip()
    interno = 0
    if not codigo:
        interno = siguiente_codigo_interno(conn)
        codigo = generar_codigo_interno(interno)
    elif codigo_existe(conn, codigo):
        conn.close()
        raise ValueError("Ya existe un producto con ese código de barras")

    categoria = data["categoria"].strip()
    categoria_id = _obtener_categoria_id(conn, categoria)
    valores = (
        data["nombre"].strip(),
        (data.get("marca") or "").strip(),
        codigo,
        categoria_id,
        categoria,
        interno,
        data["tipo_venta"],
        _numero(data.get("stock"), "El stock"),
        _numero(data.get("costo"), "El costo"),
        _numero(data.get("precio_venta"), "El precio de venta"),
        _numero(data.get("stock_minimo"), "El stock mínimo"),
        _numero(data.get("stock_critico"), "El stock crítico"),
        (data.get("proveedor") or "").strip(),
    )
    if valores[7] < 0 or valores[8] < 0 or valores[9] < 0:
        conn.close()
        raise ValueError("Stock, costo y precio no pueden ser negativos")
    if fecha_vencimiento and valores[7] <= 0:
        conn.close()
        raise ValueError("El stock inicial debe ser mayor que cero para registrar su vencimiento")
    cursor = conn.execute(
        """
        INSERT INTO productos (
            nombre, marca, codigo_barras, categoria_id, categoria, codigo_interno,
            tipo_venta, stock, costo, precio_venta, stock_minimo, stock_critico,
            proveedor, unidad_medida, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'),
            datetime('now', 'localtime'))
        """,
        (*valores, "kg" if data["tipo_venta"] == "peso" else "unidad"),
    )
    producto_id = cursor.lastrowid
    if fecha_vencimiento:
        lote_cursor = conn.execute(
            """
            INSERT INTO lotes (producto_id, cantidad, costo_unitario, fecha_vencimiento)
            VALUES (?, ?, ?, ?)
            """,
            (producto_id, valores[7], valores[8], fecha_vencimiento),
        )
        lote_id = lote_cursor.lastrowid
        _registrar_movimiento(
            conn,
            producto_id,
            "ingreso_lote",
            valores[7],
            "Stock inicial con vencimiento",
            lote_id,
        )
    elif valores[7] > 0:
        _registrar_movimiento(conn, producto_id, "ingreso", valores[7], "Stock inicial")
    conn.commit()
    producto = _producto_desde_row(_obtener_producto_conn(conn, producto_id))
    conn.close()
    return producto


def actualizar_producto(producto_id, data):
    conn = get_connection()
    actual = _obtener_producto_conn(conn, producto_id)
    if not actual:
        conn.close()
        return None

    codigo = (data.get("codigo_barras") or "").strip()
    interno = actual["codigo_interno"] or 0
    if not codigo:
        if not interno:
            interno = siguiente_codigo_interno(conn)
        codigo = generar_codigo_interno(interno)
    elif codigo_existe(conn, codigo, excluir_id=producto_id):
        conn.close()
        raise ValueError("Ya existe un producto con ese código de barras")

    categoria = data["categoria"].strip()
    categoria_id = _obtener_categoria_id(conn, categoria)
    nuevo_stock = _numero(data.get("stock"), "El stock")
    costo = _numero(data.get("costo"), "El costo")
    precio = _numero(data.get("precio_venta"), "El precio de venta")
    if nuevo_stock < 0 or costo < 0 or precio < 0:
        conn.close()
        raise ValueError("Stock, costo y precio no pueden ser negativos")

    delta = nuevo_stock - float(actual["stock"] or 0)
    conn.execute(
        """
        UPDATE productos SET
            nombre = ?, marca = ?, codigo_barras = ?, categoria_id = ?, categoria = ?,
            codigo_interno = ?, tipo_venta = ?, stock = ?, costo = ?, precio_venta = ?,
            stock_minimo = ?, stock_critico = ?, proveedor = ?, unidad_medida = ?,
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """,
        (
            data["nombre"].strip(),
            (data.get("marca") or "").strip(),
            codigo,
            categoria_id,
            categoria,
            interno,
            data["tipo_venta"],
            nuevo_stock,
            costo,
            precio,
            _numero(data.get("stock_minimo"), "El stock mínimo"),
            _numero(data.get("stock_critico"), "El stock crítico"),
            (data.get("proveedor") or "").strip(),
            "kg" if data["tipo_venta"] == "peso" else "unidad",
            producto_id,
        ),
    )
    if delta:
        _registrar_movimiento(
            conn,
            producto_id,
            "ajuste",
            abs(delta),
            (data.get("motivo_ajuste") or "Ajuste desde edición de producto").strip(),
        )
    conn.commit()
    producto = _producto_desde_row(_obtener_producto_conn(conn, producto_id))
    conn.close()
    return producto


def actualizar_stock(producto_id, stock, motivo="Ajuste manual de stock"):
    conn = get_connection()
    actual = _obtener_producto_conn(conn, producto_id)
    if not actual:
        conn.close()
        return None
    nuevo_stock = _numero(stock, "El stock")
    if nuevo_stock < 0:
        conn.close()
        raise ValueError("El stock no puede ser negativo")
    delta = nuevo_stock - float(actual["stock"] or 0)
    conn.execute(
        "UPDATE productos SET stock = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
        (nuevo_stock, producto_id),
    )
    if delta:
        _registrar_movimiento(conn, producto_id, "ajuste", abs(delta), motivo.strip())
    conn.commit()
    producto = _producto_desde_row(_obtener_producto_conn(conn, producto_id))
    conn.close()
    return producto


def eliminar_producto(producto_id):
    conn = get_connection()
    conn.execute(
        "UPDATE productos SET activo = 0, updated_at = datetime('now', 'localtime') WHERE id = ?",
        (producto_id,),
    )
    borrado = conn.execute("SELECT changes()").fetchone()[0] > 0
    conn.commit()
    conn.close()
    return borrado


def resumen_inventario():
    productos = listar_productos()
    hoy = date.today().isoformat()
    limite = (date.today() + timedelta(days=30)).isoformat()
    conn = get_connection()
    valores = conn.execute(
        """
        SELECT
            ROUND(COALESCE(SUM(COALESCE(stock, 0) * COALESCE(costo, 0)), 0), 2)
                AS valor_costo,
            ROUND(COALESCE(SUM(COALESCE(stock, 0) * COALESCE(precio_venta, 0)), 0), 2)
                AS valor_venta
        FROM productos
        WHERE COALESCE(activo, 1) = 1
        """
    ).fetchone()
    conn.close()
    return {
        "total_productos": len(productos),
        "sin_stock": sum(1 for p in productos if p["estado_stock"] == "sin_stock"),
        "stock_minimo": sum(1 for p in productos if p["estado_stock"] == "minimo"),
        "stock_critico": sum(1 for p in productos if p["estado_stock"] == "critico"),
        "proximos_vencer": sum(
            1 for p in productos
            if p["proximo_vencimiento"] and hoy <= p["proximo_vencimiento"][:10] <= limite
        ),
        "valor_costo": valores["valor_costo"],
        "valor_venta": valores["valor_venta"],
    }


def estadisticas_administracion():
    conn = get_connection()
    try:
        resumen = conn.execute(
            """
            SELECT
                ROUND(COALESCE(SUM(dv.subtotal), 0), 2) AS ingresos,
                ROUND(COALESCE(SUM(
                    dv.cantidad * COALESCE(l.costo_unitario, p.costo, 0)
                ), 0), 2) AS costo_ventas,
                ROUND(COALESCE(SUM(
                    dv.subtotal - dv.cantidad * COALESCE(l.costo_unitario, p.costo, 0)
                ), 0), 2) AS ganancia_bruta,
                COUNT(DISTINCT v.id) AS ventas_completadas
            FROM ventas v
            JOIN detalle_ventas dv ON dv.venta_id = v.id
            JOIN productos p ON p.id = dv.producto_id
            LEFT JOIN lotes l ON l.id = dv.lote_id
            WHERE v.estado = 'COMPLETADA'
            """
        ).fetchone()
        inversion = conn.execute(
            """
            SELECT ROUND(COALESCE(SUM(stock * costo), 0), 2) AS inversion_stock
            FROM productos
            WHERE COALESCE(activo, 1) = 1
            """
        ).fetchone()["inversion_stock"]
        ventas_mensuales = [
            dict(row)
            for row in conn.execute(
                """
                WITH RECURSIVE meses(mes, restante) AS (
                    SELECT date('now', 'localtime', 'start of month', '-5 months'), 5
                    UNION ALL
                    SELECT date(mes, '+1 month'), restante - 1
                    FROM meses
                    WHERE restante > 0
                )
                SELECT strftime('%Y-%m', meses.mes) AS mes,
                    ROUND(COALESCE(SUM(v.total), 0), 2) AS total
                FROM meses
                LEFT JOIN ventas v
                    ON strftime('%Y-%m', v.fecha) = strftime('%Y-%m', meses.mes)
                    AND v.estado = 'COMPLETADA'
                GROUP BY meses.mes
                ORDER BY meses.mes
                """
            )
        ]
        mas_vendidos = [
            dict(row)
            for row in conn.execute(
                """
                SELECT p.id, p.nombre AS producto, p.marca, p.tipo_venta,
                    ROUND(SUM(dv.cantidad), 3) AS cantidad,
                    ROUND(SUM(dv.subtotal), 2) AS ingresos
                FROM ventas v
                JOIN detalle_ventas dv ON dv.venta_id = v.id
                JOIN productos p ON p.id = dv.producto_id
                WHERE v.estado = 'COMPLETADA'
                GROUP BY p.id
                ORDER BY cantidad DESC, ingresos DESC, p.nombre COLLATE NOCASE
                LIMIT 8
                """
            )
        ]
        rentabilidad = [
            dict(row)
            for row in conn.execute(
                """
                SELECT p.id, p.nombre AS producto,
                    ROUND(SUM(dv.subtotal), 2) AS ingresos,
                    ROUND(SUM(
                        dv.cantidad * COALESCE(l.costo_unitario, p.costo, 0)
                    ), 2) AS costo,
                    ROUND(SUM(
                        dv.subtotal - dv.cantidad * COALESCE(l.costo_unitario, p.costo, 0)
                    ), 2) AS ganancia
                FROM ventas v
                JOIN detalle_ventas dv ON dv.venta_id = v.id
                JOIN productos p ON p.id = dv.producto_id
                LEFT JOIN lotes l ON l.id = dv.lote_id
                WHERE v.estado = 'COMPLETADA'
                GROUP BY p.id
                ORDER BY ABS(ganancia) DESC, p.nombre COLLATE NOCASE
                LIMIT 8
                """
            )
        ]
        reposicion = [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, nombre AS producto, marca, stock, stock_minimo, stock_critico,
                    unidad_medida
                FROM productos
                WHERE COALESCE(activo, 1) = 1 AND stock <= stock_minimo
                ORDER BY stock ASC, stock_minimo DESC, nombre COLLATE NOCASE
                """
            )
        ]
        return {
            "resumen": {
                "ingresos": resumen["ingresos"],
                "costo_ventas": resumen["costo_ventas"],
                "ganancia_bruta": resumen["ganancia_bruta"],
                "inversion_stock": inversion,
                "ventas_completadas": resumen["ventas_completadas"],
                "margen_porcentaje": round(
                    resumen["ganancia_bruta"] / resumen["ingresos"] * 100, 2
                ) if resumen["ingresos"] else 0,
            },
            "ventas_mensuales": ventas_mensuales,
            "mas_vendidos": mas_vendidos,
            "rentabilidad": rentabilidad,
            "reposicion": reposicion,
        }
    finally:
        conn.close()


def listar_proveedores():
    conn = get_connection()
    proveedores = [
        row["proveedor"]
        for row in conn.execute(
            "SELECT DISTINCT proveedor FROM productos WHERE trim(proveedor) != '' ORDER BY proveedor COLLATE NOCASE"
        )
    ]
    conn.close()
    return proveedores


def asociar_productos_proveedor(producto_ids, proveedor):
    ids = list(dict.fromkeys(producto_ids))
    if not ids or any(type(producto_id) is not int or producto_id <= 0 for producto_id in ids):
        raise ValueError("Seleccioná al menos un producto válido")
    if len(proveedor) > 120:
        raise ValueError("El proveedor no puede superar los 120 caracteres")

    conn = get_connection()
    placeholders = ",".join("?" for _ in ids)
    encontrados = conn.execute(
        f"SELECT id FROM productos WHERE COALESCE(activo, 1) = 1 AND id IN ({placeholders})",
        ids,
    ).fetchall()
    if len(encontrados) != len(ids):
        conn.close()
        raise ValueError("Uno o más productos seleccionados no existen")

    conn.executemany(
        """
        UPDATE productos
        SET proveedor = ?, updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """,
        [(proveedor, producto_id) for producto_id in ids],
    )
    conn.commit()
    conn.close()
    return len(ids)


def listar_categorias():
    conn = get_connection()
    categorias = [
        row["nombre"]
        for row in conn.execute("SELECT nombre FROM categorias ORDER BY nombre COLLATE NOCASE")
    ]
    conn.close()
    return categorias


def crear_categoria(nombre):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre de la categoría es obligatorio")

    conn = get_connection()
    existente = conn.execute(
        "SELECT nombre FROM categorias WHERE nombre = ? COLLATE NOCASE", (nombre,)
    ).fetchone()
    if existente:
        conn.close()
        raise ValueError("Ya existe una categoría con ese nombre")

    conn.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
    conn.commit()
    categoria = conn.execute(
        "SELECT nombre FROM categorias WHERE nombre = ?", (nombre,)
    ).fetchone()["nombre"]
    conn.close()
    return categoria


def listar_marcas():
    conn = get_connection()
    marcas = [
        row["nombre"]
        for row in conn.execute("SELECT nombre FROM marcas ORDER BY nombre COLLATE NOCASE")
    ]
    conn.close()
    return marcas


def crear_marca(nombre):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre de la marca es obligatorio")

    conn = get_connection()
    existente = conn.execute(
        "SELECT nombre FROM marcas WHERE nombre = ? COLLATE NOCASE", (nombre,)
    ).fetchone()
    if existente:
        conn.close()
        raise ValueError("Ya existe una marca con ese nombre")

    conn.execute("INSERT INTO marcas (nombre) VALUES (?)", (nombre,))
    conn.commit()
    marca = conn.execute(
        "SELECT nombre FROM marcas WHERE nombre = ?", (nombre,)
    ).fetchone()["nombre"]
    conn.close()
    return marca


def actualizar_precios(data):
    ajuste_tipo = data.get("tipo")
    if ajuste_tipo not in ("porcentaje", "monto"):
        raise ValueError("El tipo de actualización debe ser porcentaje o monto")
    valor = _numero(data.get("valor"), "El valor")
    if valor == 0:
        raise ValueError("El ajuste debe ser distinto de cero")
    if ajuste_tipo == "porcentaje" and valor <= -100:
        raise ValueError("El porcentaje no puede ser menor o igual a -100")
    condiciones = ["COALESCE(activo, 1) = 1"]
    params = []
    if data.get("categoria"):
        condiciones.append("COALESCE(c.nombre, p.categoria) = ?")
        params.append(data["categoria"])
    if data.get("proveedor"):
        condiciones.append("p.proveedor = ?")
        params.append(data["proveedor"])

    conn = get_connection()
    productos = conn.execute(
        "SELECT p.id, p.precio_venta FROM productos p "
        "LEFT JOIN categorias c ON c.id = p.categoria_id WHERE " + " AND ".join(condiciones),
        params,
    ).fetchall()
    actualizados = 0
    for producto in productos:
        precio = float(producto["precio_venta"])
        nuevo = precio * (1 + valor / 100) if ajuste_tipo == "porcentaje" else precio + valor
        if nuevo < 0:
            conn.close()
            raise ValueError("El ajuste dejaría uno o más precios por debajo de cero")
        conn.execute(
            "UPDATE productos SET precio_venta = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
            (round(nuevo, 2), producto["id"]),
        )
        actualizados += 1
    conn.commit()
    conn.close()
    return {"actualizados": actualizados}


def registrar_lote(producto_id, cantidad, fecha_vencimiento, codigo_lote=""):
    cantidad = _numero(cantidad, "La cantidad")
    if cantidad <= 0:
        raise ValueError("La cantidad del lote debe ser mayor que cero")
    try:
        vencimiento = date.fromisoformat(fecha_vencimiento)
    except (TypeError, ValueError):
        raise ValueError("La fecha de vencimiento debe ser una fecha válida")

    codigo_lote = str(codigo_lote or "").strip()
    conn = get_connection()
    producto = _obtener_producto_conn(conn, producto_id)
    if not producto or not producto["activo"]:
        conn.close()
        return None
    cursor = conn.execute(
        """
        INSERT INTO lotes (producto_id, cantidad, costo_unitario, fecha_vencimiento)
        VALUES (?, ?, ?, ?)
        """,
        (producto_id, cantidad, producto["costo"], vencimiento.isoformat()),
    )
    lote_id = cursor.lastrowid
    if codigo_lote:
        conn.execute("UPDATE lotes SET codigo_lote = ? WHERE id = ?", (codigo_lote, lote_id))
    conn.execute(
        "UPDATE productos SET stock = stock + ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
        (cantidad, producto_id),
    )
    _registrar_movimiento(
        conn, producto_id, "ingreso_lote", cantidad,
        f"Ingreso de lote {codigo_lote}" if codigo_lote else "Ingreso de lote",
        lote_id,
    )
    conn.commit()
    lote = conn.execute(
        "SELECT l.*, p.nombre AS producto_nombre, p.codigo_barras FROM lotes l "
        "JOIN productos p ON p.id = l.producto_id WHERE l.id = ?",
        (lote_id,),
    ).fetchone()
    conn.close()
    return dict(lote)


def listar_lotes(solo_alertas=False):
    conn = get_connection()
    sql = """
        SELECT l.*, p.nombre AS producto_nombre, p.codigo_barras,
            p.tipo_venta
        FROM lotes l JOIN productos p ON p.id = l.producto_id
        WHERE l.cantidad > 0 AND COALESCE(p.activo, 1) = 1
    """
    params = []
    if solo_alertas:
        sql += " AND l.fecha_vencimiento <= ?"
        params.append((date.today() + timedelta(days=30)).isoformat())
    sql += " ORDER BY l.fecha_vencimiento"
    lotes = [dict(row) for row in conn.execute(sql, params)]
    conn.close()
    return lotes


def registrar_movimiento(data):
    producto_id = int(data.get("producto_id"))
    tipo = data.get("tipo")
    cantidad = _numero(data.get("cantidad"), "La cantidad")
    motivo = (data.get("motivo") or "").strip()
    lote_id = data.get("lote_id")
    tipos = {
        "merma": "merma",
        "rotura": "rotura",
        "consumo_propio": "consumo_propio",
        "vencimiento": "vencimiento",
        "devolucion": "devolucion",
        "ajuste": "ajuste",
    }
    if tipo not in tipos:
        raise ValueError("Tipo de movimiento no válido")
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero")
    if not motivo:
        raise ValueError("La justificación es obligatoria")

    conn = get_connection()
    producto = _obtener_producto_conn(conn, producto_id)
    if not producto or not producto["activo"]:
        conn.close()
        return None
    stock_actual = float(producto["stock"] or 0)
    cantidad_stock = cantidad
    if tipo in ("merma", "rotura", "consumo_propio", "vencimiento"):
        if cantidad > stock_actual:
            conn.close()
            raise ValueError("La cantidad supera el stock disponible")
        cantidad_stock = -cantidad
        if tipo == "vencimiento":
            if not lote_id:
                conn.close()
                raise ValueError("Seleccioná el lote vencido")
            lote = conn.execute(
                "SELECT cantidad, fecha_vencimiento FROM lotes WHERE id = ? AND producto_id = ?",
                (lote_id, producto_id),
            ).fetchone()
            if not lote or float(lote["cantidad"]) < cantidad:
                conn.close()
                raise ValueError("El lote no tiene esa cantidad disponible")
            if (
                not lote["fecha_vencimiento"]
                or lote["fecha_vencimiento"] > date.today().isoformat()
            ):
                conn.close()
                raise ValueError("La fecha de vencimiento del lote todavía no llegó")
            conn.execute("UPDATE lotes SET cantidad = cantidad - ? WHERE id = ?", (cantidad, lote_id))
    elif tipo == "devolucion":
        cantidad_stock = cantidad
    else:
        cantidad_stock = _numero(data.get("diferencia"), "La diferencia")
        if cantidad_stock == 0 or stock_actual + cantidad_stock < 0:
            conn.close()
            raise ValueError("La diferencia de stock no es válida")

    nuevo_stock = stock_actual + cantidad_stock
    conn.execute(
        "UPDATE productos SET stock = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
        (nuevo_stock, producto_id),
    )
    _registrar_movimiento(conn, producto_id, tipos[tipo], abs(cantidad_stock), motivo, lote_id)
    conn.commit()
    movimiento = dict(
        conn.execute(
            """
            SELECT m.*, p.nombre AS producto_nombre, p.codigo_barras
            FROM inventario_movimientos m JOIN productos p ON p.id = m.producto_id
            WHERE m.id = last_insert_rowid()
            """
        ).fetchone()
    )
    conn.close()
    return movimiento


def historial_movimientos(producto_id=None, limite=100):
    conn = get_connection()
    sql = """
        SELECT m.*, p.nombre AS producto_nombre, p.codigo_barras,
            p.tipo_venta
        FROM inventario_movimientos m JOIN productos p ON p.id = m.producto_id
    """
    params = []
    if producto_id:
        sql += " WHERE m.producto_id = ?"
        params.append(producto_id)
    sql += " ORDER BY m.fecha DESC, m.id DESC LIMIT ?"
    params.append(max(1, min(int(limite), 500)))
    movimientos = [dict(row) for row in conn.execute(sql, params)]
    conn.close()
    return movimientos


def verificar_login(usuario, password):
    if not isinstance(usuario, str) or not isinstance(password, str):
        return None
    conn = get_connection()
    user = conn.execute(
        """
        SELECT u.id, u.nombre, u.usuario, u.password_hash, r.nombre AS rol
        FROM usuarios u JOIN roles r ON r.id = u.rol_id
        WHERE u.usuario = ? AND u.activo = 1
        """,
        (usuario.strip(),),
    ).fetchone()
    if not user:
        conn.close()
        return None
    password_hash = user["password_hash"]
    valido = False
    if password_hash.startswith(("scrypt:", "pbkdf2:")):
        try:
            valido = check_password_hash(password_hash, password)
        except ValueError:
            valido = False
    else:
        valido = password_hash == password
        if valido:
            conn.execute(
                "UPDATE usuarios SET password_hash = ? WHERE id = ?",
                (generate_password_hash(password), user["id"]),
            )
            conn.commit()
    conn.close()
    if not valido:
        return None
    return {
        "id": user["id"],
        "nombre": user["nombre"],
        "usuario": user["usuario"],
        "rol": user["rol"],
    }


def crear_usuario(nombre, usuario, password):
    nombre = nombre.strip()
    usuario = usuario.strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,30}", usuario):
        raise ValueError("El usuario debe tener entre 3 y 30 caracteres (letras, números, punto, guion o guion bajo)")
    if len(nombre) < 2 or len(nombre) > 80:
        raise ValueError("El nombre debe tener entre 2 y 80 caracteres")
    if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise ValueError("La contraseña debe tener al menos 8 caracteres, una letra y un número")
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO usuarios (nombre, usuario, password_hash, rol_id)
            VALUES (?, ?, ?, (SELECT id FROM roles WHERE nombre = 'Empleado'))
            """,
            (nombre, usuario, generate_password_hash(password)),
        )
        conn.commit()
        return dict(conn.execute(
            """
            SELECT u.id, u.nombre, u.usuario, r.nombre AS rol
            FROM usuarios u JOIN roles r ON r.id = u.rol_id
            WHERE u.usuario = ?
            """,
            (usuario,),
        ).fetchone())
    except sqlite3.IntegrityError as error:
        raise ValueError("Ese nombre de usuario ya está registrado") from error
    finally:
        conn.close()


def listar_usuarios():
    conn = get_connection()
    try:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT u.id, u.nombre, u.usuario, r.nombre AS rol, u.activo
                FROM usuarios u JOIN roles r ON r.id = u.rol_id
                ORDER BY u.nombre COLLATE NOCASE
                """
            )
        ]
    finally:
        conn.close()


def registrar_actividad(usuario_id, accion, detalle):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO registro_actividad (usuario_id, accion, detalle) VALUES (?, ?, ?)",
            (usuario_id, accion, detalle),
        )
        conn.commit()
    finally:
        conn.close()


def listar_actividad(limite=300):
    limite = max(1, min(int(limite), 1000))
    conn = get_connection()
    try:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT a.id, a.accion, a.detalle, a.fecha,
                    u.nombre AS usuario_nombre, u.usuario
                FROM registro_actividad a
                JOIN usuarios u ON u.id = a.usuario_id
                ORDER BY a.fecha DESC, a.id DESC
                LIMIT ?
                """,
                (limite,),
            )
        ]
    finally:
        conn.close()


def _monto_caja(valor, nombre="El monto", permitir_cero=False):
    if isinstance(valor, bool):
        raise ValueError(f"{nombre} debe ser un número válido")
    monto = _numero(valor, nombre)
    if monto < 0 or (not permitir_cero and monto == 0):
        operador = "mayor o igual a cero" if permitir_cero else "mayor que cero"
        raise ValueError(f"{nombre} debe ser {operador}")
    return round(monto, 2)


def _caja_abierta_conn(conn):
    row = conn.execute(
        """
        SELECT c.*, u.nombre AS usuario_apertura
        FROM cajas c
        JOIN usuarios u ON u.id = c.usuario_apertura_id
        WHERE c.estado = 'ABIERTA'
        """
    ).fetchone()
    if not row:
        return None
    caja = dict(row)
    movimientos = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'INGRESO' THEN monto ELSE -monto END), 0)
                AS neto_movimientos
        FROM movimientos_caja
        WHERE caja_id = ?
        """,
        (caja["id"],),
    ).fetchone()
    caja["monto_esperado"] = round(
        float(caja["monto_inicial"]) + float(movimientos["neto_movimientos"]), 2
    )
    return caja


def estado_caja():
    conn = get_connection()
    try:
        caja = _caja_abierta_conn(conn)
        movimientos = []
        if caja:
            movimientos = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT m.*, u.nombre AS usuario_nombre
                    FROM movimientos_caja m
                    JOIN usuarios u ON u.id = m.usuario_id
                    WHERE m.caja_id = ?
                    ORDER BY m.fecha DESC, m.id DESC
                    LIMIT 100
                    """,
                    (caja["id"],),
                )
            ]
        cierres = [
            dict(row)
            for row in conn.execute(
                """
                SELECT cc.*, c.fecha_apertura, u.nombre AS usuario_nombre
                FROM cierres_caja cc
                JOIN cajas c ON c.id = cc.caja_id
                JOIN usuarios u ON u.id = cc.usuario_id
                ORDER BY cc.fecha DESC, cc.id DESC
                LIMIT 100
                """
            )
        ]
        return {"caja_abierta": caja, "movimientos": movimientos, "cierres": cierres}
    finally:
        conn.close()


def abrir_caja(usuario_id, monto_inicial):
    monto = _monto_caja(monto_inicial, "El monto inicial", permitir_cero=True)
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if _caja_abierta_conn(conn):
            raise ValueError("Ya hay una caja abierta")
        cursor = conn.execute(
            """
            INSERT INTO cajas (usuario_apertura_id, monto_inicial, estado)
            VALUES (?, ?, 'ABIERTA')
            """,
            (usuario_id, monto),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise ValueError("Ya hay una caja abierta") from error
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def registrar_movimiento_caja(usuario_id, tipo, monto, concepto):
    tipo = str(tipo or "").strip().upper()
    concepto = str(concepto or "").strip()
    if tipo not in ("INGRESO", "EGRESO"):
        raise ValueError("El tipo de movimiento debe ser ingreso o egreso")
    if not concepto:
        raise ValueError("El concepto es obligatorio")
    if len(concepto) > 200:
        raise ValueError("El concepto no puede superar los 200 caracteres")
    monto = _monto_caja(monto)

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        caja = _caja_abierta_conn(conn)
        if not caja:
            raise ValueError("No hay una caja abierta")
        conn.execute(
            """
            INSERT INTO movimientos_caja (caja_id, usuario_id, tipo, concepto, monto)
            VALUES (?, ?, ?, ?, ?)
            """,
            (caja["id"], usuario_id, tipo, concepto, monto),
        )
        conn.commit()
        return caja["id"]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def cerrar_caja(usuario_id, monto_real, tipo):
    tipo = str(tipo or "").strip().upper()
    if tipo not in ("PARCIAL", "FINAL"):
        raise ValueError("El tipo de cierre debe ser parcial o final")
    monto_real = _monto_caja(monto_real, "El monto contado", permitir_cero=True)

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        caja = _caja_abierta_conn(conn)
        if not caja:
            raise ValueError("No hay una caja abierta para cerrar")
        esperado = caja["monto_esperado"]
        diferencia = round(monto_real - esperado, 2)
        conn.execute(
            """
            INSERT INTO cierres_caja
                (caja_id, usuario_id, tipo, monto_esperado, monto_real, diferencia)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (caja["id"], usuario_id, tipo, esperado, monto_real, diferencia),
        )
        if tipo == "FINAL":
            conn.execute(
                """
                UPDATE cajas
                SET fecha_cierre = datetime('now', 'localtime'),
                    monto_esperado = ?, monto_real = ?, diferencia = ?, estado = 'CERRADA'
                WHERE id = ? AND estado = 'ABIERTA'
                """,
                (esperado, monto_real, diferencia, caja["id"]),
            )
        conn.commit()
        return {
            "caja_id": caja["id"],
            "tipo": tipo,
            "monto_esperado": esperado,
            "monto_real": monto_real,
            "diferencia": diferencia,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def registrar_venta(data, usuario_id=1):
    try:
        producto_id = int(data.get("producto_id"))
    except (TypeError, ValueError):
        raise ValueError("Seleccioná un producto válido")
    if isinstance(data.get("producto_id"), bool):
        raise ValueError("Seleccioná un producto válido")

    cantidad = _numero(data.get("cantidad"), "La cantidad")
    unidad = (data.get("unidad") or "").strip().lower()
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero")

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        producto = _obtener_producto_conn(conn, producto_id)
        if not producto or not producto["activo"]:
            return None

        if producto["tipo_venta"] == "peso":
            if unidad not in ("kg", "gramos"):
                raise ValueError("Este producto se vende por peso: indicá kg o gramos")
            cantidad_stock = cantidad / 1000 if unidad == "gramos" else cantidad
        else:
            if unidad not in ("", "unidad"):
                raise ValueError("Este producto se vende por unidad")
            if cantidad != int(cantidad):
                raise ValueError("Las unidades deben ser un número entero")
            cantidad_stock = cantidad

        cantidad_stock = round(cantidad_stock, 6)
        stock_actual = float(producto["stock"] or 0)
        if cantidad_stock > stock_actual + 1e-9:
            raise ValueError(f"Stock insuficiente (disponible: {stock_actual:g})")

        precio = float(producto["precio_venta"] or 0)
        total = round(cantidad_stock * precio, 2)
        cursor = conn.execute(
            """
            INSERT INTO ventas (usuario_id, fecha, subtotal, descuento, recargo, total, estado)
            VALUES (?, datetime('now', 'localtime'), ?, 0, 0, ?, 'COMPLETADA')
            """,
            (usuario_id, total, total),
        )
        venta_id = cursor.lastrowid

        restante = cantidad_stock
        lotes = conn.execute(
            """
            SELECT id, cantidad FROM lotes
            WHERE producto_id = ? AND cantidad > 0
            ORDER BY fecha_vencimiento IS NULL, fecha_vencimiento, id
            """,
            (producto_id,),
        ).fetchall()
        asignaciones = []
        for lote in lotes:
            if restante <= 1e-9:
                break
            disponible = float(lote["cantidad"])
            tomar = min(disponible, restante)
            conn.execute(
                "UPDATE lotes SET cantidad = ? WHERE id = ?",
                (round(disponible - tomar, 6), lote["id"]),
            )
            asignaciones.append((lote["id"], tomar))
            restante = round(restante - tomar, 6)
        if restante > 1e-9:
            asignaciones.append((None, restante))

        for lote_id, cantidad_linea in asignaciones:
            subtotal = round(cantidad_linea * precio, 2)
            conn.execute(
                """
                INSERT INTO detalle_ventas
                    (venta_id, producto_id, lote_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (venta_id, producto_id, lote_id, cantidad_linea, precio, subtotal),
            )

        stock_restante = max(0.0, round(stock_actual - cantidad_stock, 6))
        conn.execute(
            """
            UPDATE productos SET stock = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (stock_restante, producto_id),
        )
        detalle = (
            f"{cantidad:g} g" if unidad == "gramos"
            else f"{cantidad:g} {'kg' if unidad == 'kg' else 'u.'}"
        )
        _registrar_movimiento(
            conn, producto_id, "salida", cantidad_stock,
            f"Venta de mostrador ({detalle})",
        )
        caja = _caja_abierta_conn(conn)
        if caja:
            conn.execute(
                """
                INSERT INTO movimientos_caja
                    (caja_id, usuario_id, tipo, concepto, monto, venta_id)
                VALUES (?, ?, 'INGRESO', ?, ?, ?)
                """,
                (
                    caja["id"],
                    usuario_id,
                    f"Venta #{venta_id} - {producto['nombre']}",
                    total,
                    venta_id,
                ),
            )
        conn.commit()
        return {
            "id": venta_id,
            "producto_id": producto_id,
            "producto_nombre": producto["nombre"],
            "marca": producto["marca"],
            "cantidad_descontada": cantidad_stock,
            "tipo_venta": producto["tipo_venta"],
            "total": total,
            "stock_restante": stock_restante,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_ventas(limite=50):
    limite = max(1, min(int(limite), 500))
    conn = get_connection()
    try:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT v.id, v.fecha, SUM(dv.cantidad) AS cantidad, p.nombre AS producto_nombre,
                    p.marca, p.tipo_venta, dv.precio_unitario,
                    ROUND(SUM(dv.subtotal), 2) AS total
                FROM ventas v
                JOIN detalle_ventas dv ON dv.venta_id = v.id
                JOIN productos p ON p.id = dv.producto_id
                WHERE v.estado = 'COMPLETADA'
                GROUP BY v.id, p.id
                ORDER BY v.id DESC
                LIMIT ?
                """,
                (limite,),
            )
        ]
    finally:
        conn.close()


def registrar_compra(data):
    proveedor = str(data.get("proveedor") or "").strip()
    numero_factura = str(data.get("numero_factura") or "").strip()
    if len(proveedor) > 120:
        raise ValueError("El proveedor no puede superar los 120 caracteres")
    if len(numero_factura) > 60:
        raise ValueError("El número de factura no puede superar los 60 caracteres")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Agregá al menos un producto a la compra")

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.execute(
            """
            INSERT INTO compras_registradas (proveedor, numero_factura, total)
            VALUES (?, ?, 0)
            """,
            (proveedor, numero_factura),
        )
        compra_id = cursor.lastrowid
        total = 0.0
        alertas = []

        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Cada producto de la compra debe ser válido")
            try:
                producto_id = int(item.get("producto_id"))
            except (TypeError, ValueError):
                raise ValueError("Seleccioná un producto válido")
            if isinstance(item.get("producto_id"), bool):
                raise ValueError("Seleccioná un producto válido")

            producto = _obtener_producto_conn(conn, producto_id)
            if not producto or not producto["activo"]:
                raise ValueError("Uno de los productos no existe o está inactivo")

            cantidad = _numero(item.get("cantidad"), f"La cantidad de {producto['nombre']}")
            costo = _numero(item.get("costo_unitario"), f"El costo de {producto['nombre']}")
            if cantidad <= 0:
                raise ValueError(f"La cantidad de {producto['nombre']} debe ser mayor que cero")
            if producto["tipo_venta"] != "peso" and cantidad != int(cantidad):
                raise ValueError(f"La cantidad de {producto['nombre']} debe ser entera")
            if costo < 0:
                raise ValueError(f"El costo de {producto['nombre']} no puede ser negativo")

            fecha_vencimiento = item.get("fecha_vencimiento") or None
            if fecha_vencimiento:
                try:
                    fecha_vencimiento = date.fromisoformat(fecha_vencimiento).isoformat()
                except (TypeError, ValueError):
                    raise ValueError("La fecha de vencimiento debe ser una fecha válida")

            precio_venta = item.get("precio_venta")
            if precio_venta not in (None, ""):
                precio_venta = _numero(
                    precio_venta, f"El precio de venta de {producto['nombre']}"
                )
                if precio_venta < 0:
                    raise ValueError(
                        f"El precio de venta de {producto['nombre']} no puede ser negativo"
                    )

            costo_anterior = float(producto["costo"] or 0)
            if costo > costo_anterior:
                alertas.append({
                    "producto_id": producto_id,
                    "producto": producto["nombre"],
                    "costo_anterior": costo_anterior,
                    "costo_nuevo": costo,
                    "mensaje": (
                        f'El costo de "{producto["nombre"]}" subió '
                        f"de ${costo_anterior:g} a ${costo:g}."
                    ),
                })

            subtotal = round(cantidad * costo, 2)
            lote_cursor = conn.execute(
                """
                INSERT INTO lotes (producto_id, cantidad, costo_unitario, fecha_vencimiento)
                VALUES (?, ?, ?, ?)
                """,
                (producto_id, cantidad, costo, fecha_vencimiento),
            )
            lote_id = lote_cursor.lastrowid
            conn.execute(
                """
                UPDATE productos
                SET stock = stock + ?, costo = ?,
                    precio_venta = COALESCE(?, precio_venta),
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (cantidad, costo, precio_venta, producto_id),
            )
            conn.execute(
                """
                INSERT INTO detalle_compras_registradas
                    (compra_id, producto_id, lote_id, cantidad, costo_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (compra_id, producto_id, lote_id, cantidad, costo, subtotal),
            )
            _registrar_movimiento(
                conn, producto_id, "ingreso_compra", cantidad,
                f"Compra #{compra_id}" + (
                    f" - Factura {numero_factura}" if numero_factura else ""
                ),
                lote_id,
            )
            total += subtotal

        total = round(total, 2)
        conn.execute(
            "UPDATE compras_registradas SET total = ? WHERE id = ?",
            (total, compra_id),
        )
        conn.commit()
        return {
            "id": compra_id,
            "total": total,
            "alertas": alertas,
            "message": "Mercadería ingresada",
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_compras(limite=50):
    limite = max(1, min(int(limite), 500))
    conn = get_connection()
    try:
        compras = [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, proveedor, numero_factura, fecha, total
                FROM compras_registradas
                ORDER BY id DESC
                LIMIT ?
                """,
                (limite,),
            )
        ]
        for compra in compras:
            compra["items"] = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT d.producto_id, p.nombre, d.cantidad,
                        d.costo_unitario, d.subtotal, d.lote_id
                    FROM detalle_compras_registradas d
                    JOIN productos p ON p.id = d.producto_id
                    WHERE d.compra_id = ?
                    ORDER BY d.id
                    """,
                    (compra["id"],),
                )
            ]
        return compras
    finally:
        conn.close()
