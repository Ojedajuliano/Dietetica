from flask import Flask, request, jsonify
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
    eliminar_producto,
    historial_movimientos,
    init_db,
    listar_lotes,
    listar_categorias,
    listar_marcas,
    listar_productos,
    listar_proveedores,
    obtener_producto,
    registrar_lote,
    registrar_movimiento,
    resumen_inventario,
    verificar_login,
)

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

init_db()


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
def login():
    data = request.get_json()
    usuario = data.get("usuario")
    password = data.get("password")

    if verificar_login(usuario, password):
        return jsonify({"message": "Login correcto"}), 200

    return jsonify({"message": "Login incorrecto"}), 401


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
    return jsonify(listar_productos(busqueda, filtro, categoria, proveedor))


@app.route("/api/productos/<int:producto_id>", methods=["GET"])
def api_obtener_producto(producto_id):
    producto = obtener_producto(producto_id)
    if not producto:
        return jsonify({"message": "Producto no encontrado"}), 404
    return jsonify(producto)


@app.route("/api/productos", methods=["POST"])
def api_crear_producto():
    data = request.get_json()
    error = validar_producto(data)
    if error:
        return jsonify({"message": error}), 400
    try:
        producto = crear_producto(data)
        return jsonify(producto), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 409


@app.route("/api/productos/<int:producto_id>", methods=["PUT"])
def api_actualizar_producto(producto_id):
    data = request.get_json()
    error = validar_producto(data)
    if error:
        return jsonify({"message": error}), 400
    try:
        producto = actualizar_producto(producto_id, data)
    except ValueError as e:
        return jsonify({"message": str(e)}), 409
    if not producto:
        return jsonify({"message": "Producto no encontrado"}), 404
    return jsonify(producto)


@app.route("/api/productos/<int:producto_id>/stock", methods=["PATCH"])
def api_actualizar_stock(producto_id):
    data = request.get_json() or {}
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
    return jsonify(producto)


@app.route("/api/productos/<int:producto_id>", methods=["DELETE"])
def api_eliminar_producto(producto_id):
    if not eliminar_producto(producto_id):
        return jsonify({"message": "Producto no encontrado"}), 404
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
    return jsonify(movimiento), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
