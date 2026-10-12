from flask import Flask, request, jsonify, session
from flask_cors import CORS
import json
import math
import os

from database import (
    actualizar_producto,
    actualizar_precios,
    actualizar_stock,
    crear_categoria,
    crear_marca,
    crear_producto,
    crear_usuario,
    eliminar_producto,
    estadisticas_administracion,
    historial_movimientos,
    init_db,
    listar_actividad,
    listar_compras,
    listar_lotes,
    listar_categorias,
    listar_marcas,
    listar_productos,
    listar_proveedores,
    listar_usuarios,
    listar_ventas,
    obtener_producto,
    registrar_lote,
    registrar_movimiento,
    registrar_compra,
    registrar_venta,
    registrar_actividad,
    resumen_inventario,
    verificar_login,
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)
CORS(app, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

init_db()


@app.before_request
def requerir_sesion():
    if (
        request.method != "OPTIONS"
        and request.path.startswith("/api/")
        and request.path not in (
        "/api/auth/login",
        "/api/auth/admin-login",
        "/api/auth/register",
        "/api/auth/me",
        "/api/auth/logout",
        )
        and "usuario" not in session
    ):
        return jsonify({"message": "Iniciá sesión para continuar"}), 401


def es_administrador():
    return session.get("usuario", {}).get("rol") == "Administrador"


def validar_producto(data):
    if not data:
        return "No se recibieron datos"
    if not (data.get("nombre") or "").strip():
        return "El nombre es obligatorio"
    if not (data.get("categoria") or "").strip():
        return "La categoría es obligatoria"
    tipo = data.get("tipo_venta")
    if tipo not in ("unidad", "peso"):
        return "El tipo de venta debe ser unidad o peso"
    try:
        stock_critico = float(data.get("stock_critico") or 0)
        stock_minimo = float(data.get("stock_minimo") or 0)
        stock = float(data.get("stock") or 0)
        costo = float(data.get("costo") or 0)
        precio = float(data.get("precio_venta") or 0)
        valores = [stock_critico, stock_minimo, stock, costo, precio]
        if not all(math.isfinite(valor) for valor in valores):
            return "Los valores numéricos deben ser válidos"
        if min(valores) < 0:
            return "Stock, costo, precio y niveles de stock no pueden ser negativos"
        if stock_critico and stock_minimo and stock_critico > stock_minimo:
            return "El stock crítico debe ser menor o igual al stock mínimo"
    except (TypeError, ValueError):
        return "Los valores numéricos no son válidos"
    return None


@app.route("/app/administracion", methods=["POST"])
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    usuario = data.get("usuario")
    password = data.get("password")
    user = verificar_login(usuario, password)

    if user:
        session.clear()
        session["usuario"] = user
        return jsonify({"message": "Login correcto", "usuario": user}), 200

    return jsonify({"message": "Login incorrecto"}), 401


@app.route("/api/auth/admin-login", methods=["POST"])
def login_administrador():
    data = request.get_json(silent=True) or {}
    user = verificar_login(data.get("usuario"), data.get("password"))
    if not user or user["rol"] != "Administrador":
        return jsonify({"message": "Credenciales de administrador incorrectas"}), 401

    session.clear()
    session["usuario"] = user
    return jsonify({"message": "Acceso de administrador correcto", "usuario": user}), 200


@app.route("/api/auth/me", methods=["GET"])
def api_usuario_actual():
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"message": "No hay una sesión iniciada"}), 401
    return jsonify({"usuario": usuario})


@app.route("/api/auth/register", methods=["POST"])
def api_registrar_empleado():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre")
    usuario = data.get("usuario")
    password = data.get("password")
    if not all(isinstance(value, str) for value in (nombre, usuario, password)):
        return jsonify({"message": "Completá nombre, usuario y contraseña"}), 400
    try:
        nuevo_usuario = crear_usuario(nombre, usuario, password)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    registrar_actividad(
        nuevo_usuario["id"],
        "Registro de empleado",
        f"Se registró el usuario {nuevo_usuario['usuario']} ({nuevo_usuario['nombre']})",
    )
    session.clear()
    session["usuario"] = nuevo_usuario
    return jsonify({"message": "Cuenta creada correctamente", "usuario": nuevo_usuario}), 201


@app.route("/api/auth/logout", methods=["POST"])
def api_cerrar_sesion():
    session.clear()
    return jsonify({"message": "Sesión cerrada"})


@app.route("/api/usuarios", methods=["GET", "POST"])
def api_usuarios():
    if not es_administrador():
        return jsonify({"message": "Solo el administrador puede gestionar usuarios"}), 403
    if request.method == "GET":
        return jsonify(listar_usuarios())

    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre")
    usuario = data.get("usuario")
    password = data.get("password")
    if not all(isinstance(value, str) for value in (nombre, usuario, password)):
        return jsonify({"message": "Completá nombre, usuario y contraseña"}), 400
    try:
        nuevo_usuario = crear_usuario(nombre, usuario, password)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    registrar_actividad(
        session["usuario"]["id"],
        "Alta de empleado",
        f"Se creó el usuario {nuevo_usuario['usuario']} ({nuevo_usuario['nombre']})",
    )
    return jsonify(nuevo_usuario), 201


@app.route("/api/administracion/actividad", methods=["GET"])
def api_actividad():
    if not es_administrador():
        return jsonify({"message": "Solo el administrador puede consultar la actividad"}), 403
    limite = request.args.get("limite", 300, type=int)
    return jsonify(listar_actividad(limite))


@app.route("/api/administracion/estadisticas", methods=["GET"])
def api_estadisticas_administracion():
    if not es_administrador():
        return jsonify({"message": "Solo el administrador puede consultar las estadísticas"}), 403
    return jsonify(estadisticas_administracion())


@app.route("/api/categorias", methods=["GET"])
def api_categorias():
    return jsonify(listar_categorias())


@app.route("/api/categorias", methods=["POST"])
def api_crear_categoria():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre")
    if not isinstance(nombre, str) or not nombre.strip():
        return jsonify({"message": "El nombre de la categoría es obligatorio"}), 400
    try:
        categoria = crear_categoria(nombre)
    except ValueError as e:
        return jsonify({"message": str(e)}), 409
    return jsonify({"nombre": categoria}), 201


@app.route("/api/marcas", methods=["GET"])
def api_marcas():
    return jsonify(listar_marcas())


@app.route("/api/marcas", methods=["POST"])
def api_crear_marca():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre")
    if not isinstance(nombre, str) or not nombre.strip():
        return jsonify({"message": "El nombre de la marca es obligatorio"}), 400
    try:
        marca = crear_marca(nombre)
    except ValueError as e:
        return jsonify({"message": str(e)}), 409
    return jsonify({"nombre": marca}), 201


@app.route("/api/inventario/resumen", methods=["GET"])
def api_resumen():
    return jsonify(resumen_inventario())


@app.route("/api/productos", methods=["GET"])
def api_listar_productos():
    busqueda = request.args.get("q", "").strip()
    filtro = request.args.get("filtro", "").strip()
    categoria = request.args.get("categoria", "").strip()
    proveedor = request.args.get("proveedor", "").strip()
    marca = request.args.get("marca", "").strip()
    return jsonify(listar_productos(busqueda, filtro, categoria, proveedor, marca))


@app.route("/api/productos/<int:producto_id>", methods=["GET"])
def api_obtener_producto(producto_id):
    producto = obtener_producto(producto_id)
    if not producto:
        return jsonify({"message": "Producto no encontrado"}), 404
    return jsonify(producto)


@app.route("/api/productos", methods=["POST"])
def api_crear_producto():
    data = request.get_json(silent=True) or {}
    error = validar_producto(data)
    if error:
        return jsonify({"message": error}), 400
    try:
        producto = crear_producto(data)
        registrar_actividad(
            session["usuario"]["id"],
            "Alta de producto",
            f"Se creó el producto {producto['nombre']} (ID {producto['id']})",
        )
        return jsonify(producto), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 409


@app.route("/api/productos/<int:producto_id>", methods=["PUT"])
def api_actualizar_producto(producto_id):
    data = request.get_json(silent=True) or {}
    error = validar_producto(data)
    if error:
        return jsonify({"message": error}), 400
    try:
        producto = actualizar_producto(producto_id, data)
    except ValueError as e:
        return jsonify({"message": str(e)}), 409
    if not producto:
        return jsonify({"message": "Producto no encontrado"}), 404
    registrar_actividad(
        session["usuario"]["id"],
        "Modificación",
        f"Se modificó el producto {producto['nombre']} (ID {producto_id})",
    )
    return jsonify(producto)


@app.route("/api/productos/<int:producto_id>/stock", methods=["PATCH"])
def api_actualizar_stock(producto_id):
    data = request.get_json(silent=True) or {}
    try:
        stock = float(data.get("stock"))
    except (TypeError, ValueError):
        return jsonify({"message": "El stock debe ser un número"}), 400
    if stock < 0:
        return jsonify({"message": "El stock no puede ser negativo"}), 400
    try:
        producto = actualizar_stock(
            producto_id, stock, (data.get("motivo") or "Ajuste manual de stock").strip()
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    if not producto:
        return jsonify({"message": "Producto no encontrado"}), 404
    registrar_actividad(
        session["usuario"]["id"],
        "Modificación de stock",
        f"Se actualizó el stock de {producto['nombre']} a {stock:g}. Motivo: {(data.get('motivo') or 'Ajuste manual de stock').strip()}",
    )
    return jsonify(producto)


@app.route("/api/productos/<int:producto_id>", methods=["DELETE"])
def api_eliminar_producto(producto_id):
    producto = obtener_producto(producto_id)
    if not eliminar_producto(producto_id):
        return jsonify({"message": "Producto no encontrado"}), 404
    registrar_actividad(
        session["usuario"]["id"],
        "Eliminación",
        f"Se eliminó el producto {producto['nombre'] if producto else producto_id} (ID {producto_id})",
    )
    return jsonify({"message": "Producto eliminado"})


@app.route("/api/proveedores", methods=["GET"])
def api_listar_proveedores():
    return jsonify(listar_proveedores())


@app.route("/api/precios/actualizacion-masiva", methods=["POST"])
def api_actualizar_precios():
    data = request.get_json(silent=True) or {}
    try:
        resultado = actualizar_precios(data)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    registrar_actividad(
        session["usuario"]["id"],
        "Modificación de precios",
        f"Se actualizaron precios de {resultado.get('actualizados', 0)} productos",
    )
    return jsonify(resultado)


@app.route("/api/lotes", methods=["GET", "POST"])
def api_lotes():
    if request.method == "GET":
        alertas = request.args.get("alertas", "").lower() == "true"
        return jsonify(listar_lotes(alertas))

    data = request.get_json(silent=True) or {}
    try:
        producto_id = int(data.get("producto_id"))
        lote = registrar_lote(
            producto_id,
            data.get("cantidad"),
            data.get("fecha_vencimiento"),
            data.get("codigo_lote", ""),
        )
    except (TypeError, ValueError) as e:
        return jsonify({"message": str(e) or "Datos del lote no válidos"}), 400
    if not lote:
        return jsonify({"message": "Producto no encontrado"}), 404
    registrar_actividad(
        session["usuario"]["id"],
        "Compra",
        f"Ingreso de {lote['cantidad']} unidades del producto {lote.get('producto_nombre', producto_id)}",
    )
    return jsonify(lote), 201


@app.route("/api/movimientos", methods=["GET", "POST"])
def api_movimientos():
    if request.method == "GET":
        producto_id = request.args.get("producto_id", type=int)
        return jsonify(historial_movimientos(producto_id))

    data = request.get_json(silent=True) or {}
    try:
        movimiento = registrar_movimiento(data)
    except (TypeError, ValueError) as e:
        return jsonify({"message": str(e) or "Datos del movimiento no válidos"}), 400
    if not movimiento:
        return jsonify({"message": "Producto no encontrado"}), 404
    registrar_actividad(
        session["usuario"]["id"],
        "Movimiento de stock",
        f"{movimiento['tipo']} de {movimiento['cantidad']} de {movimiento['producto_nombre']}. Motivo: {movimiento.get('motivo') or ''}",
    )
    return jsonify(movimiento), 201


@app.route("/api/ventas", methods=["GET", "POST"])
def api_ventas():
    if request.method == "GET":
        limite = request.args.get("limite", 50, type=int)
        return jsonify(listar_ventas(limite))

    data = request.get_json(silent=True) or {}
    try:
        venta = registrar_venta(data, session["usuario"]["id"])
    except (TypeError, ValueError) as e:
        return jsonify({"message": str(e) or "Datos de la venta no válidos"}), 400
    if not venta:
        return jsonify({"message": "Producto no encontrado"}), 404
    registrar_actividad(
        session["usuario"]["id"],
        "Venta",
        f"Venta de {venta['producto_nombre']} · cantidad {venta['cantidad_descontada']:g} · total ${venta['total']:.2f}",
    )
    return jsonify(venta), 201


@app.route("/api/compras", methods=["GET", "POST"])
def api_compras():
    if request.method == "GET":
        limite = request.args.get("limite", 50, type=int)
        return jsonify(listar_compras(limite))

    data = request.get_json(silent=True) or {}
    try:
        compra = registrar_compra(data)
    except (TypeError, ValueError) as e:
        return jsonify({"message": str(e) or "Datos de la compra no válidos"}), 400
    registrar_actividad(
        session["usuario"]["id"],
        "Compra",
        f"Compra #{compra['id']} · {len(data.get('items', []))} producto(s) · proveedor: {data.get('proveedor') or 'sin especificar'} · total ${compra['total']:.2f}",
    )
    return jsonify(compra), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
