import math
import os
import sqlite3
from datetime import date, timedelta

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
        "CREATE INDEX IF NOT EXISTS idx_lotes_vencimiento ON lotes(fecha_vencimiento)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventario_movimientos_fecha "
        "ON inventario_movimientos(fecha)"
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


def listar_productos(busqueda="", filtro="", categoria="", proveedor=""):
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
    if valores[7] > 0:
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
    return {
        "total_productos": len(productos),
        "sin_stock": sum(1 for p in productos if p["estado_stock"] == "sin_stock"),
        "stock_minimo": sum(1 for p in productos if p["estado_stock"] == "minimo"),
        "stock_critico": sum(1 for p in productos if p["estado_stock"] == "critico"),
        "proximos_vencer": sum(
            1 for p in productos
            if p["proximo_vencimiento"] and hoy <= p["proximo_vencimiento"][:10] <= limite
        ),
        "valor_costo": round(sum(p["stock"] * p["costo"] for p in productos), 2),
        "valor_venta": round(sum(p["stock"] * p["precio_venta"] for p in productos), 2),
    }


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


def listar_categorias():
    conn = get_connection()
    categorias = [
        row["nombre"]
        for row in conn.execute("SELECT nombre FROM categorias ORDER BY nombre COLLATE NOCASE")
    ]
    conn.close()
    return categorias


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
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM usuarios WHERE usuario = ? AND password_hash = ? AND activo = 1",
        (usuario, password)
    ).fetchone()
    conn.close()
    return user is not None
