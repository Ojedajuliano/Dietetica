import { useCallback, useEffect, useMemo, useState } from "react";
import "../Inventario/Inventario.css";
import {
  asociarProductosProveedor,
  getProductos,
  getProveedores,
} from "../../api/productos";

export default function Proveedores() {
  const [productos, setProductos] = useState([]);
  const [proveedores, setProveedores] = useState([]);
  const [proveedor, setProveedor] = useState("");
  const [filtroProveedor, setFiltroProveedor] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [seleccionados, setSeleccionados] = useState(() => new Set());
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const [listaProductos, listaProveedores] = await Promise.all([
        getProductos(),
        getProveedores(),
      ]);
      setProductos(listaProductos);
      setProveedores(listaProveedores);
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

  const productosVisibles = useMemo(() => {
    const consulta = busqueda.trim().toLocaleLowerCase();
    return productos.filter((producto) => {
      const proveedorActual = producto.proveedor || "";
      const coincideProveedor = filtroProveedor === "sin-asignar"
        ? !proveedorActual
        : !filtroProveedor || proveedorActual === filtroProveedor;
      const coincideBusqueda = !consulta
        || producto.nombre.toLocaleLowerCase().includes(consulta)
        || (producto.codigo_barras || "").toLocaleLowerCase().includes(consulta);
      return coincideProveedor && coincideBusqueda;
    });
  }, [busqueda, filtroProveedor, productos]);

  const alternarProducto = (id) => {
    setSeleccionados((actuales) => {
      const nuevos = new Set(actuales);
      if (nuevos.has(id)) nuevos.delete(id);
      else nuevos.add(id);
      return nuevos;
    });
  };

  const seleccionarVisibles = () => {
    const idsVisibles = productosVisibles.map((producto) => producto.id);
    const todosSeleccionados = idsVisibles.every((id) => seleccionados.has(id));
    setSeleccionados((actuales) => {
      const nuevos = new Set(actuales);
      idsVisibles.forEach((id) => {
        if (todosSeleccionados) nuevos.delete(id);
        else nuevos.add(id);
      });
      return nuevos;
    });
  };

  const guardarAsociacion = async (event) => {
    event.preventDefault();
    setError("");
    setMensaje("");
    setGuardando(true);
    try {
      const resultado = await asociarProductosProveedor(
        proveedor.trim(),
        [...seleccionados],
      );
      setMensaje(
        `Se asociaron ${resultado.productos_actualizados} producto(s) con ${resultado.proveedor}.`,
      );
      setProveedor("");
      setSeleccionados(new Set());
      await cargar();
    } catch (e) {
      setError(e.message);
    } finally {
      setGuardando(false);
    }
  };

  const todosVisiblesSeleccionados = productosVisibles.length > 0
    && productosVisibles.every((producto) => seleccionados.has(producto.id));

  return (
    <div className="inventario-container">
      <div className="header-inventario">
        <h1 className="titulo-izq">Proveedores y productos</h1>
      </div>
      <div className="table-content-wrapper">
        {error && <div className="alert alert-danger" role="alert">{error}</div>}
        {mensaje && <div className="alert alert-success" role="status">{mensaje}</div>}

        <form className="card border-0 shadow-sm p-4 mb-4" onSubmit={guardarAsociacion}>
          <h2 className="h5 fw-bold mb-2">Asociar proveedor a productos</h2>
          <p className="text-secondary">
            Elegí un proveedor existente o escribí un nombre nuevo y seleccioná los productos que suministra.
          </p>
          <div className="row g-3 align-items-end">
            <div className="col-md-6">
              <label className="form-label" htmlFor="proveedor-asociacion">Proveedor</label>
              <input
                id="proveedor-asociacion"
                className="form-control"
                list="lista-proveedores"
                value={proveedor}
                onChange={(event) => setProveedor(event.target.value)}
                maxLength={120}
                required
              />
              <datalist id="lista-proveedores">
                {proveedores.map((nombre) => (
                  <option key={nombre} value={nombre} />
                ))}
              </datalist>
            </div>
            <div className="col-md-3">
              <span className="form-label d-block">Seleccionados</span>
              <strong>{seleccionados.size} producto(s)</strong>
            </div>
            <div className="col-md-3">
              <button
                className="btn btn-primary w-100"
                type="submit"
                disabled={guardando || !proveedor.trim() || seleccionados.size === 0}
              >
                {guardando ? "Guardando..." : "Guardar asociación"}
              </button>
            </div>
          </div>
        </form>

        <section className="card border-0 shadow-sm p-4">
          <div className="row g-3 align-items-end mb-3">
            <div className="col-md-6">
              <label className="form-label" htmlFor="buscar-producto-proveedor">Buscar producto</label>
              <input
                id="buscar-producto-proveedor"
                className="form-control"
                placeholder="Nombre o código"
                value={busqueda}
                onChange={(event) => setBusqueda(event.target.value)}
              />
            </div>
            <div className="col-md-4">
              <label className="form-label" htmlFor="filtrar-proveedor">Filtrar proveedor</label>
              <select
                id="filtrar-proveedor"
                className="form-select"
                value={filtroProveedor}
                onChange={(event) => setFiltroProveedor(event.target.value)}
              >
                <option value="">Todos los proveedores</option>
                <option value="sin-asignar">Sin proveedor asignado</option>
                {proveedores.map((nombre) => (
                  <option key={nombre} value={nombre}>{nombre}</option>
                ))}
              </select>
            </div>
            <div className="col-md-2">
              <button
                className="btn btn-outline-primary w-100"
                type="button"
                onClick={seleccionarVisibles}
                disabled={productosVisibles.length === 0}
              >
                {todosVisiblesSeleccionados ? "Quitar visibles" : "Seleccionar visibles"}
              </button>
            </div>
          </div>

          {cargando ? (
            <p className="text-secondary mb-0" role="status">Cargando productos...</p>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead className="table-light">
                  <tr>
                    <th scope="col">Seleccionar</th>
                    <th scope="col">Producto</th>
                    <th scope="col">Código</th>
                    <th scope="col">Proveedor actual</th>
                  </tr>
                </thead>
                <tbody>
                  {productosVisibles.map((producto) => (
                    <tr key={producto.id}>
                      <td>
                        <input
                          className="form-check-input"
                          type="checkbox"
                          aria-label={`Seleccionar ${producto.nombre}`}
                          checked={seleccionados.has(producto.id)}
                          onChange={() => alternarProducto(producto.id)}
                        />
                      </td>
                      <td>{producto.nombre}</td>
                      <td>{producto.codigo_barras || "—"}</td>
                      <td>{producto.proveedor || <span className="text-secondary">Sin asignar</span>}</td>
                    </tr>
                  ))}
                  {productosVisibles.length === 0 && (
                    <tr>
                      <td colSpan="4" className="text-center text-secondary py-4">
                        No hay productos que coincidan con el filtro.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
