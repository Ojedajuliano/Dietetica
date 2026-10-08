const API = "http://localhost:5000/api";

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || "Error al conectar con el servidor");
  }
  return data;
}

export function getProductos({ q = "", filtro = "", categoria = "", proveedor = "" } = {}) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (filtro) params.set("filtro", filtro);
  if (categoria) params.set("categoria", categoria);
  if (proveedor) params.set("proveedor", proveedor);
  const query = params.toString();
  return fetch(`${API}/productos${query ? `?${query}` : ""}`).then(parseResponse);
}

export function getProducto(id) {
  return fetch(`${API}/productos/${id}`).then(parseResponse);
}

export function crearProducto(payload) {
  return fetch(`${API}/productos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function actualizarProducto(id, payload) {
  return fetch(`${API}/productos/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function actualizarStock(id, stock, motivo) {
  return fetch(`${API}/productos/${id}/stock`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stock, motivo }),
  }).then(parseResponse);
}

export function eliminarProducto(id) {
  return fetch(`${API}/productos/${id}`, { method: "DELETE" }).then(parseResponse);
}

export function getResumenInventario() {
  return fetch(`${API}/inventario/resumen`).then(parseResponse);
}

export function getCategorias() {
  return fetch(`${API}/categorias`).then(parseResponse);
}

export function crearCategoria(nombre) {
  return fetch(`${API}/categorias`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre }),
  })
    .then(parseResponse)
    .then((categoria) => {
      window.dispatchEvent(new Event("categorias:actualizadas"));
      return categoria;
    });
}

export function getMarcas() {
  return fetch(`${API}/marcas`).then(parseResponse);
}

export function crearMarca(nombre) {
  return fetch(`${API}/marcas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre }),
  }).then(parseResponse);
}

export function getProveedores() {
  return fetch(`${API}/proveedores`).then(parseResponse);
}

export function actualizarPrecios(payload) {
  return fetch(`${API}/precios/actualizacion-masiva`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function getLotes({ alertas = false } = {}) {
  const query = alertas ? "?alertas=true" : "";
  return fetch(`${API}/lotes${query}`).then(parseResponse);
}

export function crearLote(payload) {
  return fetch(`${API}/lotes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function getMovimientos() {
  return fetch(`${API}/movimientos`).then(parseResponse);
}

export function crearMovimiento(payload) {
  return fetch(`${API}/movimientos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}
