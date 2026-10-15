const API = "http://localhost:5000/api";

function apiFetch(url, options = {}) {
  return fetch(url, { ...options, credentials: "include" });
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || "Error al conectar con el servidor");
  }
  return data;
}

export function getProductos({ q = "", filtro = "", categoria = "", proveedor = "", marca = "" } = {}) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (filtro) params.set("filtro", filtro);
  if (categoria) params.set("categoria", categoria);
  if (proveedor) params.set("proveedor", proveedor);
  if (marca) params.set("marca", marca);
  const query = params.toString();
  return apiFetch(`${API}/productos${query ? `?${query}` : ""}`).then(parseResponse);
}

export function getProducto(id) {
  return apiFetch(`${API}/productos/${id}`).then(parseResponse);
}

export function crearProducto(payload) {
  return apiFetch(`${API}/productos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function actualizarProducto(id, payload) {
  return apiFetch(`${API}/productos/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function actualizarStock(id, stock, motivo) {
  return apiFetch(`${API}/productos/${id}/stock`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stock, motivo }),
  }).then(parseResponse);
}

export function eliminarProducto(id) {
  return apiFetch(`${API}/productos/${id}`, { method: "DELETE" }).then(parseResponse);
}

export function getResumenInventario() {
  return apiFetch(`${API}/inventario/resumen`).then(parseResponse);
}

export function getCategorias() {
  return apiFetch(`${API}/categorias`).then(parseResponse);
}

export function crearCategoria(nombre) {
  return apiFetch(`${API}/categorias`, {
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
  return apiFetch(`${API}/marcas`).then(parseResponse);
}

export function crearMarca(nombre) {
  return apiFetch(`${API}/marcas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre }),
  }).then(parseResponse);
}

export function getProveedores() {
  return apiFetch(`${API}/proveedores`).then(parseResponse);
}

export function asociarProductosProveedor(proveedor, producto_ids) {
  return apiFetch(`${API}/proveedores/asociaciones`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ proveedor, producto_ids }),
  }).then(parseResponse);
}

export function actualizarPrecios(payload) {
  return apiFetch(`${API}/precios/actualizacion-masiva`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function getLotes({ alertas = false } = {}) {
  const query = alertas ? "?alertas=true" : "";
  return apiFetch(`${API}/lotes${query}`).then(parseResponse);
}

export function crearLote(payload) {
  return apiFetch(`${API}/lotes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function getMovimientos() {
  return apiFetch(`${API}/movimientos`).then(parseResponse);
}

export function crearMovimiento(payload) {
  return apiFetch(`${API}/movimientos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function getVentas(limite = 15) {
  return apiFetch(`${API}/ventas?limite=${limite}`).then(parseResponse);
}

export function registrarVenta(payload) {
  return apiFetch(`${API}/ventas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function getCompras(limite = 15) {
  return apiFetch(`${API}/compras?limite=${limite}`).then(parseResponse);
}

export function registrarCompra(payload) {
  return apiFetch(`${API}/compras`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}
