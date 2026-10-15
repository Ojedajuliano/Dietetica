import { useCallback, useEffect, useState } from "react";
import "../Inventario/Inventario.css";
import {
  abrirCaja,
  getEstadoCaja,
  registrarCierreCaja,
  registrarMovimientoCaja,
} from "../../api/caja";

const moneda = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 2,
});

const fechaHora = (fecha) => {
  if (!fecha) return "—";
  return new Date(`${fecha.replace(" ", "T")}`).toLocaleString("es-AR");
};

export default function Caja() {
  const [estado, setEstado] = useState(null);
  const [montoInicial, setMontoInicial] = useState("");
  const [movimiento, setMovimiento] = useState({
    tipo: "INGRESO",
    monto: "",
    concepto: "",
  });
  const [montoContado, setMontoContado] = useState("");
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      setEstado(await getEstadoCaja());
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    const inicializar = window.setTimeout(cargar, 0);
    return () => window.clearTimeout(inicializar);
  }, [cargar]);

  const ejecutar = async (accion) => {
    setError("");
    setMensaje("");
    setGuardando(true);
    try {
      const resultado = await accion();
      if (resultado?.diferencia !== undefined) {
        const diferencia = Number(resultado.diferencia);
        setMensaje(
          `Cierre ${resultado.tipo.toLowerCase()} registrado. Diferencia: ${moneda.format(diferencia)}.`,
        );
      } else {
        setMensaje(resultado.message || "Operación registrada.");
      }
      await cargar();
    } catch (e) {
      setError(e.message);
    } finally {
      setGuardando(false);
    }
  };

  const abrir = (event) => {
    event.preventDefault();
    ejecutar(async () => {
      const resultado = await abrirCaja(Number(montoInicial));
      setMontoInicial("");
      return resultado;
    });
  };

  const registrarMovimiento = (event) => {
    event.preventDefault();
    ejecutar(async () => {
      const resultado = await registrarMovimientoCaja({
        ...movimiento,
        monto: Number(movimiento.monto),
      });
      setMovimiento({ tipo: "INGRESO", monto: "", concepto: "" });
      return resultado;
    });
  };

  const cerrar = (tipo) => {
    ejecutar(async () => {
      const resultado = await registrarCierreCaja(tipo, Number(montoContado));
      setMontoContado("");
      return resultado;
    });
  };

  const caja = estado?.caja_abierta;
  const cierres = estado?.cierres || [];
  const movimientos = estado?.movimientos || [];

  return (
    <div className="inventario-container">
      <div className="header-inventario">
        <h1 className="titulo-izq">Caja</h1>
        <button
          className="btn btn-outline-primary btn-sm"
          type="button"
          onClick={cargar}
          disabled={cargando}
        >
          Actualizar
        </button>
      </div>

      <div className="table-content-wrapper">
        {error && <div className="alert alert-danger" role="alert">{error}</div>}
        {mensaje && <div className="alert alert-success" role="status">{mensaje}</div>}
        {cargando && !estado && <p className="text-secondary" role="status">Cargando caja...</p>}

        {!cargando && estado && !caja && (
          <form className="card border-0 shadow-sm p-4 mb-4" onSubmit={abrir}>
            <h2 className="h5 fw-bold">Apertura de caja</h2>
            <p className="text-secondary">
              Ingresá el efectivo inicial. Solo puede haber una caja abierta a la vez.
            </p>
            <div className="row g-3 align-items-end">
              <div className="col-md-6">
                <label className="form-label" htmlFor="monto-inicial">Monto inicial</label>
                <input
                  id="monto-inicial"
                  className="form-control"
                  type="number"
                  min="0"
                  step="0.01"
                  value={montoInicial}
                  onChange={(event) => setMontoInicial(event.target.value)}
                  required
                />
              </div>
              <div className="col-md-6">
                <button className="btn btn-primary w-100" type="submit" disabled={guardando}>
                  {guardando ? "Abriendo..." : "Abrir caja"}
                </button>
              </div>
            </div>
          </form>
        )}

        {caja && (
          <>
            <section className="card border-0 shadow-sm p-4 mb-4">
              <div className="d-flex flex-wrap justify-content-between align-items-start gap-3">
                <div>
                  <span className="badge text-bg-success mb-2">Caja abierta · #{caja.id}</span>
                  <h2 className="h5 fw-bold mb-1">Apertura {fechaHora(caja.fecha_apertura)}</h2>
                  <p className="text-secondary mb-0">Abierta por {caja.usuario_apertura}</p>
                </div>
                <div className="text-md-end">
                  <div className="text-secondary">Saldo esperado</div>
                  <strong className="fs-3">{moneda.format(caja.monto_esperado)}</strong>
                </div>
              </div>
              <div className="row g-3 mt-2">
                <div className="col-md-4">
                  <div className="border rounded p-3 h-100">
                    <span className="text-secondary d-block">Efectivo inicial</span>
                    <strong>{moneda.format(caja.monto_inicial)}</strong>
                  </div>
                </div>
                <div className="col-md-8">
                  <div className="alert alert-info mb-0 h-100">
                    Las ventas que registres mientras esta caja esté abierta se sumarán automáticamente.
                  </div>
                </div>
              </div>
            </section>

            <section className="card border-0 shadow-sm p-4 mb-4">
              <h2 className="h5 fw-bold mb-3">Registrar ingreso o egreso</h2>
              <form onSubmit={registrarMovimiento}>
                <div className="row g-3 align-items-end">
                  <div className="col-md-3">
                    <label className="form-label" htmlFor="tipo-movimiento-caja">Movimiento</label>
                    <select
                      id="tipo-movimiento-caja"
                      className="form-select"
                      value={movimiento.tipo}
                      onChange={(event) => setMovimiento((actual) => ({ ...actual, tipo: event.target.value }))}
                    >
                      <option value="INGRESO">Ingreso de dinero</option>
                      <option value="EGRESO">Egreso de dinero</option>
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label className="form-label" htmlFor="monto-movimiento-caja">Monto</label>
                    <input
                      id="monto-movimiento-caja"
                      className="form-control"
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={movimiento.monto}
                      onChange={(event) => setMovimiento((actual) => ({ ...actual, monto: event.target.value }))}
                      required
                    />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label" htmlFor="concepto-movimiento-caja">Concepto</label>
                    <input
                      id="concepto-movimiento-caja"
                      className="form-control"
                      value={movimiento.concepto}
                      onChange={(event) => setMovimiento((actual) => ({ ...actual, concepto: event.target.value }))}
                      maxLength={200}
                      required
                    />
                  </div>
                  <div className="col-md-2">
                    <button className="btn btn-outline-primary w-100" type="submit" disabled={guardando}>
                      Registrar
                    </button>
                  </div>
                </div>
              </form>
            </section>

            <section className="card border-0 shadow-sm p-4 mb-4">
              <h2 className="h5 fw-bold mb-2">Consulta y cierre de caja</h2>
              <p className="text-secondary">
                Contá el efectivo disponible y registrá el cierre parcial o final para calcular la diferencia.
                El cierre parcial mantiene la caja abierta; el final la cierra.
              </p>
              <div className="row g-3 align-items-end">
                <div className="col-md-6">
                  <label className="form-label" htmlFor="monto-contado">Monto contado</label>
                  <input
                    id="monto-contado"
                    className="form-control"
                    type="number"
                    min="0"
                    step="0.01"
                    value={montoContado}
                    onChange={(event) => setMontoContado(event.target.value)}
                    required
                  />
                </div>
                <div className="col-md-3">
                  <button
                    className="btn btn-outline-warning w-100"
                    type="button"
                    disabled={guardando || montoContado === ""}
                    onClick={() => cerrar("PARCIAL")}
                  >
                    Cierre parcial
                  </button>
                </div>
                <div className="col-md-3">
                  <button
                    className="btn btn-danger w-100"
                    type="button"
                    disabled={guardando || montoContado === ""}
                    onClick={() => cerrar("FINAL")}
                  >
                    Cierre final
                  </button>
                </div>
              </div>
            </section>

            <section className="card border-0 shadow-sm p-4 mb-4">
              <h2 className="h5 fw-bold mb-3">Movimientos de la caja abierta</h2>
              <div className="table-responsive">
                <table className="table table-hover align-middle mb-0">
                  <thead className="table-light">
                    <tr><th>Fecha</th><th>Usuario</th><th>Tipo</th><th>Concepto</th><th className="text-end">Monto</th></tr>
                  </thead>
                  <tbody>
                    {movimientos.map((item) => (
                      <tr key={item.id}>
                        <td>{fechaHora(item.fecha)}</td>
                        <td>{item.usuario_nombre}</td>
                        <td>
                          <span className={`badge ${item.tipo === "INGRESO" ? "text-bg-success" : "text-bg-danger"}`}>
                            {item.tipo}
                          </span>
                        </td>
                        <td>{item.concepto || "—"}</td>
                        <td className="text-end">{moneda.format(item.monto)}</td>
                      </tr>
                    ))}
                    {movimientos.length === 0 && (
                      <tr><td colSpan="5" className="text-center text-secondary py-4">Todavía no hay movimientos.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        <section className="card border-0 shadow-sm p-4">
          <h2 className="h5 fw-bold mb-3">Historial de cierres</h2>
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Fecha</th><th>Caja</th><th>Tipo</th><th>Usuario</th>
                  <th className="text-end">Esperado</th><th className="text-end">Contado</th><th className="text-end">Diferencia</th>
                </tr>
              </thead>
              <tbody>
                {cierres.map((cierre) => (
                  <tr key={cierre.id}>
                    <td>{fechaHora(cierre.fecha)}</td>
                    <td>#{cierre.caja_id}</td>
                    <td>{cierre.tipo === "FINAL" ? "Final" : "Parcial"}</td>
                    <td>{cierre.usuario_nombre}</td>
                    <td className="text-end">{moneda.format(cierre.monto_esperado)}</td>
                    <td className="text-end">{moneda.format(cierre.monto_real)}</td>
                    <td className={`text-end fw-semibold ${cierre.diferencia < 0 ? "text-danger" : cierre.diferencia > 0 ? "text-success" : ""}`}>
                      {moneda.format(cierre.diferencia)}
                    </td>
                  </tr>
                ))}
                {cierres.length === 0 && (
                  <tr><td colSpan="7" className="text-center text-secondary py-4">Todavía no hay cierres registrados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
