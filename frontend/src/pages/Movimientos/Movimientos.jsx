import { useEffect, useState } from "react";
import "../Inventario/Inventario.css";
import { crearMovimiento, getLotes, getProductos } from "../../api/productos";

const TIPOS = [
  { valor: "merma", texto: "Pérdida / merma" },
  { valor: "rotura", texto: "Rotura" },
  { valor: "consumo_propio", texto: "Consumo propio" },
  { valor: "devolucion", texto: "Devolución de cliente" },
  { valor: "vencimiento", texto: "Baja por vencimiento" },
];

const Movimientos = () => {
  const [productos, setProductos] = useState([]);
  const [lotes, setLotes] = useState([]);
  const [form, setForm] = useState({
    producto_id: "",
    tipo: "merma",
    cantidad: "",
    motivo: "",
    lote_id: "",
  });
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = async () => {
    try {
      const [listaProductos, listaLotes] = await Promise.all([
        getProductos(),
        getLotes(),
      ]);
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

  const cambiar = (e) => {
    const { name, value } = e.target;
    setForm((actual) => ({
      ...actual,
      [name]: value,
      ...(name === "producto_id" ? { lote_id: "" } : {}),
    }));
    setMensaje("");
  };

  const guardar = async (e) => {
    e.preventDefault();
    setError("");
    setMensaje("");
    setGuardando(true);
    try {
      await crearMovimiento({
        ...form,
        producto_id: Number(form.producto_id),
        cantidad: Number(form.cantidad),
        lote_id: form.lote_id ? Number(form.lote_id) : null,
      });
      setMensaje("Movimiento registrado y stock actualizado.");
      setForm((actual) => ({ ...actual, cantidad: "", motivo: "", lote_id: "" }));
      await cargar();
    } catch (e) {
      setError(e.message);
    } finally {
      setGuardando(false);
    }
  };

  const lotesProducto = lotes.filter((lote) => String(lote.producto_id) === form.producto_id);
  const unidad = productos.find((p) => String(p.id) === form.producto_id)?.tipo_venta === "peso" ? "kg" : "u";

  return (
    <div className="inventario-container">
      <div className="header-inventario">
        <h1 className="titulo-izq">Mermas, devoluciones y movimientos</h1>
      </div>
      <div className="table-content-wrapper">
        {error && <p className="alert alert-danger">{error}</p>}
        {mensaje && <p className="alert alert-success">{mensaje}</p>}

        <form className="card border-0 shadow-sm p-4 mb-4" onSubmit={guardar}>
          <h4 className="fw-bold mb-3">Registrar movimiento de stock</h4>
          <div className="row g-3">
            <div className="col-md-4">
              <label className="form-label">Producto</label>
              <select className="form-select" name="producto_id" value={form.producto_id} onChange={cambiar} required>
                <option value="">Seleccionar producto</option>
                {productos.map((p) => <option key={p.id} value={p.id}>{p.nombre} · stock {p.stock}</option>)}
              </select>
            </div>
            <div className="col-md-3">
              <label className="form-label">Tipo de movimiento</label>
              <select className="form-select" name="tipo" value={form.tipo} onChange={cambiar}>
                {TIPOS.map((tipo) => <option key={tipo.valor} value={tipo.valor}>{tipo.texto}</option>)}
              </select>
            </div>
            <div className="col-md-2">
              <label className="form-label">Cantidad ({unidad})</label>
              <input className="form-control" name="cantidad" type="number" min="0.01" step="any" value={form.cantidad} onChange={cambiar} required />
            </div>
            {form.tipo === "vencimiento" && (
              <div className="col-md-3">
                <label className="form-label">Lote vencido</label>
                <select className="form-select" name="lote_id" value={form.lote_id} onChange={cambiar} required>
                  <option value="">Seleccionar lote</option>
                  {lotesProducto.map((lote) => (
                    <option key={lote.id} value={lote.id}>
                      {lote.codigo_lote || `Lote #${lote.id}`} · vence {lote.fecha_vencimiento} · {lote.cantidad} {unidad}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className="col-md">
              <label className="form-label">Justificación</label>
              <input className="form-control" name="motivo" value={form.motivo} onChange={cambiar} placeholder="Detalle el motivo del movimiento" required />
            </div>
            <div className="col-md-2 d-flex align-items-end">
              <button className="btn btn-primary w-100" type="submit" disabled={guardando}>
                {guardando ? "Guardando..." : "Registrar"}
              </button>
            </div>
          </div>
          <small className="text-secondary mt-2">
            Las bajas descuentan stock; las devoluciones lo reincorporan. Se requiere justificar cada movimiento.
          </small>
        </form>

      </div>
    </div>
  );
};

export default Movimientos;
