const API = "http://localhost:5000/api";

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || "Error al conectar con el servidor");
  }
  return data;
}

export function getUsuarioActual() {
  return fetch(`${API}/auth/me`, { credentials: "include" }).then(parseResponse);
}

export function iniciarSesion(usuario, password) {
  return fetch(`${API}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, password }),
  }).then(parseResponse);
}

export function iniciarSesionAdministrador(usuario, password) {
  return fetch(`${API}/auth/admin-login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, password }),
  }).then(parseResponse);
}

export function registrarEmpleado(payload) {
  return fetch(`${API}/auth/register`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function cerrarSesion() {
  return fetch(`${API}/auth/logout`, {
    method: "POST",
    credentials: "include",
  }).then(parseResponse);
}

export function getUsuarios() {
  return fetch(`${API}/usuarios`, { credentials: "include" }).then(parseResponse);
}

export function crearUsuario(payload) {
  return fetch(`${API}/usuarios`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(parseResponse);
}

export function getActividad() {
  return fetch(`${API}/administracion/actividad`, {
    credentials: "include",
  }).then(parseResponse);
}
