import { useEffect, useMemo, useState } from "react";
import {
  getCompras,
  getMarcas,
  getProductos,
  getProveedores,
  getVentas,
  registrarCompra,
  registrarVenta,
} from "../../api/productos";
import "./CompraVenta.css";

const dinero = (valor) =>
  Number(valor || 0).toLocaleString("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  });

const cantidadVenta = (venta) => {
  if (venta.tipo_venta === "peso") {
    return venta.cantidad < 1
      ? `${Math.round(venta.cantidad * 1000)} g`
      : `${venta.cantidad} kg`;
  }
  return `${venta.cantidad} u.`;
};

function VentaPanel() {
  const [marcas, setMarcas] = useState([]);
  const [marca, setMarca] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [resultados, setResultados] = useState([]);
  const [abierto, setAbierto] = useState(false);
  const [producto, setProducto] = useState(null);
  const [cantidad, setCantidad] = useState("");
  const [unidad, setUnidad] = useState("unidad");
  const [ventas, setVentas] = useState([]);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    Promise.all([getMarcas(), getVentas()])
      .then(([listaMarcas, listaVentas]) => {
        setMarcas(listaMarcas);
        setVentas(listaVentas);
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    const q = busqueda.trim();
    if (!q && !marca) {
      return undefined;
    }

    let vigente = true;
    const timer = setTimeout(() => {
      getProductos({ q, marca })
        .then((lista) => {
          if (vigente) setResultados(lista);
        })
        .catch((e) => {
          if (vigente) {
            setResultados([]);
            setError(e.message);
          }
        });
    }, 200);

    return () => {
      vigente = false;
      clearTimeout(timer);
    };
  }, [busqueda, marca]);

  const esPeso = producto?.tipo_venta === "peso";

  const elegirProducto = (seleccionado) => {
    setProducto(seleccionado);
    setBusqueda(seleccionado.nombre);
    setAbierto(false);
    setUnidad(seleccionado.tipo_venta === "peso" ? "gramos" : "unidad");
    setCantidad("");
    setMensaje("");
    setError("");
  };

  const vender = async (event) => {
    event.preventDefault();
    if (!producto) return;

    setError("");
    setMensaje("");
    setEnviando(true);
    try {
      const resultado = await registrarVenta({
        producto_id: producto.id,
        cantidad: Number(cantidad),
        unidad,
      });
      setMensaje(
        `Venta registrada: ${resultado.producto_nombre} — Total ${dinero(resultado.total)} (stock restante: ${resultado.stock_restante})`
      );
      setProducto(null);
      setBusqueda("");
      setCantidad("");
      setResultados([]);
      try {
        setVentas(await getVentas());
      } catch (e) {
        setError(`La venta quedó registrada, pero no se pudo actualizar el historial: ${e.message}`);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <>
      <form className="card border-0 shadow-sm p-4 mb-4" onSubmit={vender}>
        <h2 className="h4 fw-bold mb-3">Registrar venta</h2>
        {error && <div className="alert alert-danger">{error}</div>}
        {mensaje && <div className="alert alert-success">{mensaje}</div>}

        <div className="row g-3">
          <div className="col-md-4">
            <label className="form-label" htmlFor="venta-marca">Marca</label>
            <select
              id="venta-marca"
              className="form-select"
              value={marca}
              onChange={(event) => {
                setMarca(event.target.value);
                setProducto(null);
                setResultados([]);
                setAbierto(true);
              }}
            >
              <option value="">Todas las marcas</option>
              {marcas.map((nombre) => (
                <option key={nombre} value={nombre}>{nombre}</option>
              ))}
            </select>
          </div>

          <div className="col-md-8 position-relative">
            <label className="form-label" htmlFor="venta-producto">Producto</label>
            <input
              id="venta-producto"
              className="form-control"
              placeholder="Escribí el nombre del producto..."
              value={busqueda}
              autoComplete="off"
              onChange={(event) => {
                setBusqueda(event.target.value);
                setProducto(null);
                setResultados([]);
                setAbierto(true);
              }}
              onFocus={() => setAbierto(true)}
            />
            {abierto && (busqueda.trim() || marca) && (
              <div className="list-group cv-resultados">
                {resultados.length === 0 && (
                  <div className="list-group-item text-muted">Sin resultados</div>
                )}
                {resultados.slice(0, 20).map((resultado) => (
                  <button
                    type="button"
                    key={resultado.id}
                    className="list-group-item list-group-item-action d-flex justify-content-between gap-3"
                    onClick={() => elegirProducto(resultado)}
                  >
                    <span>
                      {resultado.nombre}{" "}
                      <small className="text-muted">{resultado.marca || "sin marca"}</small>
                    </span>
                    <small className="text-muted text-nowrap">
                      Stock: {resultado.stock} {resultado.tipo_venta === "peso" ? "kg" : "u."}
                    </small>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {producto && (
          <div className="alert alert-light border mt-3 mb-0">
            <strong>{producto.nombre}</strong> — {producto.marca || "sin marca"}
            <br />
            Stock: {producto.stock} {esPeso ? "kg" : "u."} · Precio:{" "}
            {dinero(producto.precio_venta)}{esPeso ? " /kg" : ""}
          </div>
        )}

        <div className="row g-3 mt-1">
          <div className="col-7">
            <label className="form-label" htmlFor="venta-cantidad">Cantidad vendida</label>
            <input
              id="venta-cantidad"
              className="form-control"
              type="number"
              min={esPeso ? "0.001" : "1"}
              step={esPeso ? "any" : "1"}
              value={cantidad}
              onChange={(event) => setCantidad(event.target.value)}
              disabled={!producto}
              required
            />
          </div>
          <div className="col-5">
            <label className="form-label" htmlFor="venta-unidad">Unidad</label>
            <select
              id="venta-unidad"
              className="form-select"
              value={unidad}
              onChange={(event) => setUnidad(event.target.value)}
              disabled={!producto}
            >
              {esPeso ? (
                <>
                  <option value="gramos">Gramos</option>
                  <option value="kg">Kilos</option>
                </>
              ) : (
                <option value="unidad">Unidades</option>
              )}
            </select>
          </div>
        </div>

        <button className="btn btn-success w-100 mt-4" disabled={!producto || enviando}>
          {enviando ? "Registrando..." : "Registrar venta"}
        </button>
      </form>

      <div className="card border-0 shadow-sm p-4">
        <h3 className="h5 fw-bold mb-3">Últimas ventas</h3>
        <div className="table-responsive">
          <table className="table table-hover align-middle mb-0">
            <thead className="table-light">
              <tr>
                <th>Fecha</th>
                <th>Producto</th>
                <th>Cantidad</th>
                <th className="text-end">Total</th>
              </tr>
            </thead>
            <tbody>
              {ventas.map((venta) => (
                <tr key={venta.id}>
                  <td>{venta.fecha}</td>
                  <td>
                    {venta.producto_nombre}{" "}
                    <small className="text-muted">{venta.marca}</small>
                  </td>
                  <td>{cantidadVenta(venta)}</td>
                  <td className="text-end">{dinero(venta.total)}</td>
                </tr>
              ))}
              {ventas.length === 0 && (
                <tr>
                  <td colSpan="4" className="text-center text-secondary py-4">
                    Todavía no hay ventas registradas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function CompraPanel() {
  const [productos, setProductos] = useState([]);
  const [proveedores, setProveedores] = useState([]);
  const [compras, setCompras] = useState([]);
  const [proveedor, setProveedor] = useState("");
  const [numeroFactura, setNumeroFactura] = useState("");
  const [productoId, setProductoId] = useState("");
  const [cantidad, setCantidad] = useState("");
  const [costo, setCosto] = useState("");
  const [precioVenta, setPrecioVenta] = useState("");
  const [vencimiento, setVencimiento] = useState("");
  const [carrito, setCarrito] = useState([]);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = async () => {
    const [listaProductos, listaProveedores, listaCompras] = await Promise.all([
      getProductos(),
      getProveedores(),
      getCompras(),
    ]);
    setProductos(listaProductos);
    setProveedores(listaProveedores);
    setCompras(listaCompras);
  };

  useEffect(() => {
    let vigente = true;
    Promise.all([getProductos(), getProveedores(), getCompras()])
      .then(([listaProductos, listaProveedores, listaCompras]) => {
        if (!vigente) return;
        setProductos(listaProductos);
        setProveedores(listaProveedores);
        setCompras(listaCompras);
      })
      .catch((e) => {
        if (vigente) setError(e.message);
      });
    return () => { vigente = false; };
  }, []);

  const total = useMemo(
    () => carrito.reduce((suma, item) => suma + item.cantidad * item.costo_unitario, 0),
    [carrito]
  );
  const productoSeleccionado = productos.find((item) => String(item.id) === productoId);

  const seleccionarProducto = (id) => {
    setProductoId(id);
    const seleccionado = productos.find((item) => String(item.id) === id);
    setCosto(seleccionado ? String(seleccionado.costo ?? "") : "");
    setPrecioVenta(seleccionado ? String(seleccionado.precio_venta ?? "") : "");
  };

  const agregarItem = (event) => {
    event.preventDefault();
    const seleccionado = productos.find((item) => String(item.id) === productoId);
    const cantidadNumerica = Number(cantidad);
    const costoNumerico = Number(costo);
    const precioNumerico = precioVenta === "" ? null : Number(precioVenta);
    if (!seleccionado || !Number.isFinite(cantidadNumerica) || cantidadNumerica <= 0) {
      setError("Seleccioná un producto y una cantidad mayor que cero.");
      return;
    }
    if (!Number.isFinite(costoNumerico) || costoNumerico < 0) {
      setError("Ingresá un costo unitario válido.");
      return;
    }
    if (precioNumerico !== null && (!Number.isFinite(precioNumerico) || precioNumerico < 0)) {
      setError("El precio de venta debe ser un número igual o mayor que cero.");
      return;
    }

    setCarrito((actual) => [
      ...actual,
      {
        clave: `${Date.now()}-${actual.length}`,
        producto_id: seleccionado.id,
        nombre: seleccionado.nombre,
        tipo_venta: seleccionado.tipo_venta,
        cantidad: cantidadNumerica,
        costo_unitario: costoNumerico,
        precio_venta: precioNumerico,
        fecha_vencimiento: vencimiento || null,
      },
    ]);
    setProductoId("");
    setCantidad("");
    setCosto("");
    setPrecioVenta("");
    setVencimiento("");
    setError("");
  };

  const quitarItem = (clave) => {
    setCarrito((actual) => actual.filter((item) => item.clave !== clave));
  };

  const guardarCompra = async (event) => {
    event.preventDefault();
    if (carrito.length === 0) {
      setError("Agregá al menos un producto a la compra.");
      return;
    }
    setError("");
    setMensaje("");
    setGuardando(true);
    try {
      const resultado = await registrarCompra({
        proveedor,
        numero_factura: numeroFactura,
        items: carrito.map((item) => ({
          producto_id: item.producto_id,
          cantidad: item.cantidad,
          costo_unitario: item.costo_unitario,
          precio_venta: item.precio_venta,
          fecha_vencimiento: item.fecha_vencimiento,
        })),
      });
      const alertas = resultado.alertas?.map((alerta) => alerta.mensaje).join(" ");
      setMensaje(
        `Compra registrada por ${dinero(resultado.total)}.${alertas ? ` ${alertas}` : ""}`
      );
      setCarrito([]);
      setNumeroFactura("");
      try {
        await cargar();
      } catch (e) {
        setError(`La compra quedó registrada, pero no se pudieron actualizar los datos: ${e.message}`);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <>
      <form className="card border-0 shadow-sm p-4 mb-4" onSubmit={guardarCompra}>
        <h2 className="h4 fw-bold mb-3">Registrar compra</h2>
        {error && <div className="alert alert-danger">{error}</div>}
        {mensaje && <div className="alert alert-success">{mensaje}</div>}

        <div className="row g-3 mb-4">
          <div className="col-md-6">
            <label className="form-label" htmlFor="compra-proveedor">Proveedor</label>
            <input
              id="compra-proveedor"
              className="form-control"
              list="compra-proveedores"
              value={proveedor}
              onChange={(event) => setProveedor(event.target.value)}
              placeholder="Nombre del proveedor"
            />
            <datalist id="compra-proveedores">
              {proveedores.map((nombre) => (
                <option key={nombre} value={nombre} />
              ))}
            </datalist>
          </div>
          <div className="col-md-6">
            <label className="form-label" htmlFor="compra-factura">Número de factura</label>
            <input
              id="compra-factura"
              className="form-control"
              value={numeroFactura}
              onChange={(event) => setNumeroFactura(event.target.value)}
              maxLength="60"
            />
          </div>
        </div>

        <div className="cv-item-form border rounded p-3 mb-3">
          <h3 className="h6 fw-bold mb-3">Agregar producto</h3>
          <div className="row g-3 align-items-end">
            <div className="col-lg-4">
              <label className="form-label" htmlFor="compra-producto">Producto</label>
              <select
                id="compra-producto"
                className="form-select"
                value={productoId}
                onChange={(event) => seleccionarProducto(event.target.value)}
              >
                <option value="">Seleccionar producto</option>
                {productos.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nombre} · stock {item.stock}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-6 col-lg-2">
              <label className="form-label" htmlFor="compra-cantidad">
                Cantidad {productoSeleccionado?.tipo_venta === "peso" ? "(kg)" : "(u.)"}
              </label>
              <input
                id="compra-cantidad"
                className="form-control"
                type="number"
                min={productoSeleccionado?.tipo_venta === "peso" ? "0.001" : "1"}
                step={productoSeleccionado?.tipo_venta === "peso" ? "any" : "1"}
                value={cantidad}
                onChange={(event) => setCantidad(event.target.value)}
              />
            </div>
            <div className="col-6 col-lg-2">
              <label className="form-label" htmlFor="compra-costo">Costo unitario</label>
              <input
                id="compra-costo"
                className="form-control"
                type="number"
                min="0"
                step="0.01"
                value={costo}
                onChange={(event) => setCosto(event.target.value)}
              />
            </div>
            <div className="col-6 col-lg-2">
              <label className="form-label" htmlFor="compra-precio">Precio de venta</label>
              <input
                id="compra-precio"
                className="form-control"
                type="number"
                min="0"
                step="0.01"
                value={precioVenta}
                onChange={(event) => setPrecioVenta(event.target.value)}
              />
            </div>
            <div className="col-6 col-lg-2">
              <label className="form-label" htmlFor="compra-vencimiento">Vencimiento</label>
              <input
                id="compra-vencimiento"
                className="form-control"
                type="date"
                value={vencimiento}
                onChange={(event) => setVencimiento(event.target.value)}
              />
            </div>
            <div className="col-12">
              <button type="button" className="btn btn-outline-primary" onClick={agregarItem}>
                Agregar al detalle
              </button>
            </div>
          </div>
        </div>

        <div className="table-responsive">
          <table className="table table-sm align-middle">
            <thead className="table-light">
              <tr>
                <th>Producto</th>
                <th>Cantidad</th>
                <th>Costo unitario</th>
                <th className="text-end">Subtotal</th>
                <th aria-label="Acciones" />
              </tr>
            </thead>
            <tbody>
              {carrito.map((item) => (
                <tr key={item.clave}>
                  <td>{item.nombre}</td>
                  <td>{item.cantidad} {item.tipo_venta === "peso" ? "kg" : "u."}</td>
                  <td>{dinero(item.costo_unitario)}</td>
                  <td className="text-end">{dinero(item.cantidad * item.costo_unitario)}</td>
                  <td className="text-end">
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => quitarItem(item.clave)}
                      aria-label={`Quitar ${item.nombre}`}
                    >
                      Quitar
                    </button>
                  </td>
                </tr>
              ))}
              {carrito.length === 0 && (
                <tr>
                  <td colSpan="5" className="text-center text-secondary py-3">
                    Todavía no agregaste productos.
                  </td>
                </tr>
              )}
            </tbody>
            <tfoot>
              <tr>
                <th colSpan="3">Total</th>
                <th className="text-end">{dinero(total)}</th>
                <th />
              </tr>
            </tfoot>
          </table>
        </div>

        <button className="btn btn-primary w-100 mt-2" disabled={!carrito.length || guardando}>
          {guardando ? "Registrando..." : "Registrar compra e ingresar stock"}
        </button>
      </form>

      <div className="card border-0 shadow-sm p-4">
        <h3 className="h5 fw-bold mb-3">Últimas compras</h3>
        <div className="table-responsive">
          <table className="table table-hover align-middle mb-0">
            <thead className="table-light">
              <tr>
                <th>Fecha</th>
                <th>Proveedor</th>
                <th>Factura</th>
                <th>Productos</th>
                <th className="text-end">Total</th>
              </tr>
            </thead>
            <tbody>
              {compras.map((compra) => (
                <tr key={compra.id}>
                  <td>{compra.fecha}</td>
                  <td>{compra.proveedor || "—"}</td>
                  <td>{compra.numero_factura || "—"}</td>
                  <td>{compra.items.map((item) => item.nombre).join(", ")}</td>
                  <td className="text-end">{dinero(compra.total)}</td>
                </tr>
              ))}
              {compras.length === 0 && (
                <tr>
                  <td colSpan="5" className="text-center text-secondary py-4">
                    Todavía no hay compras registradas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

export default function CompraVenta({ initialTab = "compra" }) {
  const [tab, setTab] = useState(initialTab);

  return (
    <div className="compra-venta-container">
      <div className="cv-header">
        <div>
          <p className="text-secondary mb-1">Operaciones</p>
          <h1 className="h2 fw-bold mb-0">Compra y venta</h1>
        </div>
        <div className="btn-group" role="tablist" aria-label="Tipo de operación">
          <button
            type="button"
            role="tab"
            aria-selected={tab === "compra"}
            className={`btn ${tab === "compra" ? "btn-primary" : "btn-outline-primary"}`}
            onClick={() => setTab("compra")}
          >
            <i className="bi bi-box-arrow-in-down me-2" />
            Compra
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === "venta"}
            className={`btn ${tab === "venta" ? "btn-success" : "btn-outline-success"}`}
            onClick={() => setTab("venta")}
          >
            <i className="bi bi-cart-check me-2" />
            Venta
          </button>
        </div>
      </div>
      <div className="cv-content">
        {tab === "compra" ? <CompraPanel /> : <VentaPanel />}
      </div>
    </div>
  );
}