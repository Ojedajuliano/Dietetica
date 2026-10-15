const API = "http://localhost:5000/api/caja";

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || "Error al conectar con el servidor");
  }
  return data;
}

function cajaFetch(path = "", options = {}) {
  return fetch(`${API}${path}`, { ...options, credentials: "include" }).then(parseResponse);
}

export function getEstadoCaja() {
  return cajaFetch();
}

export function abrirCaja(monto_inicial) {
  return cajaFetch("/apertura", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ monto_inicial }),
  });
}

export function registrarMovimientoCaja(payload) {
  return cajaFetch("/movimientos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function registrarCierreCaja(tipo, monto_real) {
  return cajaFetch("/cierres", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tipo, monto_real }),
  });
}
