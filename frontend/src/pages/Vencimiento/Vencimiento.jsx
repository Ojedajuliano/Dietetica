import { useEffect, useState } from "react";
import "../Inventario/Inventario.css";
import { crearLote, getLotes, getProductos } from "../../api/productos";

const Vencimiento = () => {
  const [productos, setProductos] = useState([]);
  const [lotes, setLotes] = useState([]);
  const [form, setForm] = useState({
    producto_id: "",
    cantidad: "",
    fecha_vencimiento: "",
  });
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = async () => {
    try {
      const [listaProductos, listaLotes] = await Promise.all([getProductos(), getLotes()]);
      setProductos(listaProductos);
      setLotes(listaLotes);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    let vigente = true;
    Promise.all([getProductos(), getLotes()])
      .then(([listaProductos, listaLotes]) => {
        if (!vigente) return;
        setProductos(listaProductos);
        setLotes(listaLotes);
      })
      .catch((e) => { if (vigente) setError(e.message); });
    return () => { vigente = false; };
  }, []);

  const guardar = async (e) => {
    e.preventDefault();
    setError("");
    setMensaje("");
    setGuardando(true);
    try {
      await crearLote({
        ...form,
        producto_id: Number(form.producto_id),
        cantidad: Number(form.cantidad),
      });
      setMensaje("Lote registrado y stock actualizado.");
      setForm({ producto_id: "", cantidad: "", fecha_vencimiento: "" });
      await cargar();
    } catch (e) {
      setError(e.message);
    } finally {
      setGuardando(false);
    }
  };

  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  const limite = new Date(hoy);
  limite.setDate(limite.getDate() + 30);
  const fechaLote = (lote) => lote.fecha_vencimiento
    ? new Date(`${lote.fecha_vencimiento}T00:00:00`)
    : null;
  const lotesVencidos = lotes.filter((lote) => {
    const vencimiento = fechaLote(lote);
    return vencimiento && vencimiento <= hoy;
  });
  const lotesPorVencer = lotes.filter((lote) => {
    const vencimiento = fechaLote(lote);
    return vencimiento && vencimiento > hoy && vencimiento <= limite;
  });
  const tieneAlertas = lotesVencidos.length > 0 || lotesPorVencer.length > 0;

  return (
    <div className="inventario-container">
      <div className="header-inventario">
        <h1 className="titulo-izq">Lotes y vencimientos</h1>
      </div>
      <div className="table-content-wrapper">
        {error && <p className="alert alert-danger">{error}</p>}
        {mensaje && <p className="alert alert-success">{mensaje}</p>}
        {tieneAlertas && (
          <div className={`alert ${lotesVencidos.length ? "alert-danger" : "alert-warning"}`} role="alert">
            <strong>Alerta de vencimientos:</strong>{" "}
            {lotesVencidos.length > 0 && `${lotesVencidos.length} lote(s) vencido(s)`}
            {lotesVencidos.length > 0 && lotesPorVencer.length > 0 && " y "}
            {lotesPorVencer.length > 0 && `${lotesPorVencer.length} lote(s) vencen dentro de los próximos 30 días`}.
            <ul className="mb-0 mt-2">
              {[...lotesVencidos, ...lotesPorVencer].map((lote) => (
                <li key={lote.id}>
                  {lote.producto_nombre} · Lote #{lote.id} · vence {lote.fecha_vencimiento}
                </li>
              ))}
            </ul>
          </div>
        )}
        <form className="card border-0 shadow-sm p-4 mb-4" onSubmit={guardar}>
          <h4 className="fw-bold mb-3">Registrar lote recibido</h4>
          <div className="row g-3 align-items-end">
            <div className="col-md-4">
              <label className="form-label">Producto</label>
              <select
                className="form-select"
                value={form.producto_id}
                onChange={(e) => setForm((actual) => ({ ...actual, producto_id: e.target.value }))}
                required
              >
                <option value="">Seleccionar producto</option>
                {productos.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
              </select>
            </div>
            <div className="col-md-2">
              <label className="form-label">Cantidad</label>
              <input
                className="form-control"
                type="number"
                min="0.01"
                step="any"
                value={form.cantidad}
                onChange={(e) => setForm((actual) => ({ ...actual, cantidad: e.target.value }))}
                required
              />
            </div>
            <div className="col-md-2">
              <label className="form-label">Vencimiento</label>
              <input
                className="form-control"
                type="date"
                value={form.fecha_vencimiento}
                onChange={(e) => setForm((actual) => ({ ...actual, fecha_vencimiento: e.target.value }))}
                required
              />
            </div>
            <div className="col-md-2">
              <button className="btn btn-primary w-100" type="submit" disabled={guardando}>
                {guardando ? "Guardando..." : "Registrar lote"}
              </button>
            </div>
          </div>
          <small className="text-secondary mt-2">Al registrar el lote, su cantidad se suma al stock actual del producto.</small>
        </form>

        <div className="card border-0 shadow-sm p-4">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h4 className="fw-bold m-0">Lotes con stock</h4>
            <span className="badge bg-warning text-dark">
              {lotesVencidos.length + lotesPorVencer.length} próximos a vencer o vencidos
            </span>
          </div>
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr><th>Producto</th><th>Lote</th><th>Vencimiento</th><th>Cantidad disponible</th><th>Estado</th></tr>
              </thead>
              <tbody>
                {lotes.length === 0 && <tr><td colSpan="5" className="text-center text-secondary py-4">No hay lotes registrados con stock.</td></tr>}
                {lotes.map((lote) => {
                  const vencimiento = fechaLote(lote);
                  const vencido = vencimiento && vencimiento <= hoy;
                  const alerta = vencimiento && vencimiento > hoy && vencimiento <= limite;
                  return (
                    <tr key={lote.id}>
                      <td>{lote.producto_nombre}</td>
                      <td>#{lote.id}</td>
                      <td>{lote.fecha_vencimiento}</td>
                      <td>{lote.cantidad} {lote.tipo_venta === "peso" ? "kg" : "u"}</td>
                      <td>
                        <span className={`badge ${vencido ? "bg-danger" : alerta ? "bg-warning text-dark" : "bg-success"}`}>
                          {vencido ? "Vencido" : alerta ? "Próximo a vencer" : vencimiento ? "Vigente" : "Sin fecha"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Vencimiento;
