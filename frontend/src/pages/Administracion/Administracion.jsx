import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getActividad,
  getEstadisticasAdministracion,
  getUsuarios,
  iniciarSesionAdministrador,
} from "../../api/auth";
import "../Inventario/Inventario.css";
import "./Administracion.css";

const moneda = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 2,
});

const numero = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 3 });

const LoginAdministrador = ({ onAdminLogin }) => {
  const [usuario, setUsuario] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [ingresando, setIngresando] = useState(false);

  const ingresar = async (event) => {
    event.preventDefault();
    setError("");
    setIngresando(true);
    try {
      const data = await iniciarSesionAdministrador(usuario.trim(), password);
      onAdminLogin(data.usuario);
    } catch (e) {
      setError(e.message);
    } finally {
      setIngresando(false);
    }
  };

  return (
    <div className="inventario-container">
      <div className="header-inventario">
        <h1 className="titulo-izq">Administración</h1>
      </div>
      <div className="container py-5">
        <section className="card border-0 shadow-sm p-4 mx-auto" style={{ maxWidth: "440px" }}>
          <h2 className="h4 fw-bold mb-2">Acceso de administrador</h2>
          <p className="text-secondary">Ingresá las credenciales de administrador para consultar movimientos y usuarios.</p>
          {error && <div className="alert alert-danger" role="alert">{error}</div>}
          <form onSubmit={ingresar}>
            <label className="form-label" htmlFor="admin-usuario">Usuario administrador</label>
            <input
              id="admin-usuario"
              className="form-control mb-3"
              autoComplete="username"
              value={usuario}
              onChange={(event) => setUsuario(event.target.value)}
              required
            />
            <label className="form-label" htmlFor="admin-password">Contraseña</label>
            <input
              id="admin-password"
              className="form-control mb-4"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <button className="btn btn-primary w-100 mb-3" type="submit" disabled={ingresando}>
              {ingresando ? "Validando..." : "Ingresar a Administración"}
            </button>
          </form>
          <Link to="/inventario" className="text-center">Volver al inventario</Link>
        </section>
      </div>
    </div>
  );
};

function GraficoVentas({ meses }) {
  const maximo = Math.max(...meses.map((mes) => mes.total), 0);

  return (
    <div className="estadistica-grafico-ventas" role="img" aria-label="Ventas totales por mes durante los últimos seis meses">
      {meses.map((mes) => {
        const fecha = new Date(`${mes.mes}-02T00:00:00`);
        const etiqueta = new Intl.DateTimeFormat("es-AR", { month: "short" }).format(fecha);
        const alto = maximo > 0 ? (mes.total / maximo) * 100 : 0;
        return (
          <div className="estadistica-columna" key={mes.mes} title={`${etiqueta}: ${moneda.format(mes.total)}`}>
            <span className="estadistica-valor-mes">{moneda.format(mes.total)}</span>
            <div className="estadistica-barra-mes-fondo">
              <div className="estadistica-barra-mes" style={{ height: `${alto}%` }} />
            </div>
            <span className="estadistica-etiqueta-mes">{etiqueta}</span>
          </div>
        );
      })}
    </div>
  );
}

function GraficoProductos({ productos, tipo }) {
  const mayor = Math.max(...productos.map((producto) => producto.cantidad), 0);

  if (productos.length === 0) {
    return <p className="estadistica-vacio mb-0">Todavía no hay ventas registradas.</p>;
  }

  return (
    <div className="estadistica-lista-barras" role="img" aria-label="Productos más vendidos por cantidad">
      {productos.map((producto) => (
        <div className="estadistica-producto-barra" key={producto.id}>
          <div className="estadistica-producto-encabezado">
            <span title={producto.producto}>{producto.producto}</span>
            <strong>{numero.format(producto.cantidad)} {producto.tipo_venta === "peso" ? "kg" : tipo}</strong>
          </div>
          <div className="estadistica-barra-horizontal-fondo">
            <div
              className="estadistica-barra-horizontal"
              style={{ width: `${mayor > 0 ? (producto.cantidad / mayor) * 100 : 0}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function GraficoRentabilidad({ productos }) {
  const mayor = Math.max(...productos.map((producto) => Math.abs(producto.ganancia)), 0);

  if (productos.length === 0) {
    return <p className="estadistica-vacio mb-0">Todavía no hay ventas para calcular la rentabilidad.</p>;
  }

  return (
    <div className="estadistica-lista-barras" role="img" aria-label="Ganancia bruta por producto vendido">
      {productos.map((producto) => {
        const positiva = producto.ganancia >= 0;
        return (
          <div className="estadistica-producto-barra" key={producto.id}>
            <div className="estadistica-producto-encabezado">
              <span title={producto.producto}>{producto.producto}</span>
              <strong className={positiva ? "estadistica-ganancia" : "estadistica-perdida"}>
                {moneda.format(producto.ganancia)}
              </strong>
            </div>
            <div className="estadistica-barra-horizontal-fondo">
              <div
                className={`estadistica-barra-horizontal ${positiva ? "" : "estadistica-barra-negativa"}`}
                style={{ width: `${mayor > 0 ? (Math.abs(producto.ganancia) / mayor) * 100 : 0}%` }}
              />
            </div>
            <small className="text-secondary">
              Ingresos {moneda.format(producto.ingresos)} · Costo {moneda.format(producto.costo)}
            </small>
          </div>
        );
      })}
    </div>
  );
}

function PanelEstadisticas({ estadisticas, cargando, error, onActualizar }) {
  const resumen = estadisticas?.resumen;

  return (
    <section className="estadisticas-panel">
      <div className="estadisticas-titulo">
        <div>
          <h2 className="h4 fw-bold mb-1">Estadísticas del negocio</h2>
          <p className="text-secondary mb-0">Ventas completadas, rentabilidad e inventario actual.</p>
        </div>
        <button className="btn btn-outline-primary btn-sm" type="button" onClick={onActualizar} disabled={cargando}>
          <i className="bi bi-arrow-clockwise me-1" aria-hidden="true" />
          {cargando ? "Actualizando..." : "Actualizar"}
        </button>
      </div>

      {error && <div className="alert alert-danger mt-3 mb-0" role="alert">{error}</div>}
      {cargando && !estadisticas ? (
        <div className="estadistica-vacio mt-3" role="status">Cargando estadísticas...</div>
      ) : (
        <>
          <div className="estadisticas-indicadores">
            <article className="estadistica-indicador">
              <span className="estadistica-indicador-icono ventas"><i className="bi bi-cash-stack" aria-hidden="true" /></span>
              <div><span>Ingresos por ventas</span><strong>{moneda.format(resumen?.ingresos ?? 0)}</strong></div>
            </article>
            <article className="estadistica-indicador">
              <span className="estadistica-indicador-icono ganancia"><i className="bi bi-graph-up-arrow" aria-hidden="true" /></span>
              <div><span>Ganancia bruta</span><strong className={(resumen?.ganancia_bruta ?? 0) < 0 ? "estadistica-perdida" : ""}>{moneda.format(resumen?.ganancia_bruta ?? 0)}</strong></div>
            </article>
            <article className="estadistica-indicador">
              <span className="estadistica-indicador-icono inversion"><i className="bi bi-box-seam" aria-hidden="true" /></span>
              <div><span>Dinero invertido en stock</span><strong>{moneda.format(resumen?.inversion_stock ?? 0)}</strong></div>
            </article>
            <article className="estadistica-indicador">
              <span className="estadistica-indicador-icono margen"><i className="bi bi-percent" aria-hidden="true" /></span>
              <div><span>Margen bruto · {resumen?.ventas_completadas ?? 0} ventas</span><strong>{numero.format(resumen?.margen_porcentaje ?? 0)}%</strong></div>
            </article>
          </div>

          <div className="estadisticas-graficos">
            <article className="card border-0 shadow-sm p-4">
              <h3 className="h6 fw-bold mb-1">Ventas por mes</h3>
              <p className="text-secondary small mb-3">Ingresos de los últimos seis meses</p>
              <GraficoVentas meses={estadisticas?.ventas_mensuales ?? []} />
            </article>
            <article className="card border-0 shadow-sm p-4">
              <h3 className="h6 fw-bold mb-1">Productos más vendidos</h3>
              <p className="text-secondary small mb-3">Ordenados por cantidad vendida</p>
              <GraficoProductos productos={estadisticas?.mas_vendidos ?? []} tipo="u." />
            </article>
            <article className="card border-0 shadow-sm p-4 estadisticas-grafico-ancho">
              <h3 className="h6 fw-bold mb-1">Ganancias y pérdidas por producto</h3>
              <p className="text-secondary small mb-3">Ingresos menos el costo de los productos vendidos</p>
              <GraficoRentabilidad productos={estadisticas?.rentabilidad ?? []} />
            </article>
          </div>

          <section className="card border-0 shadow-sm p-4 mt-4">
            <div className="d-flex align-items-center justify-content-between gap-3 mb-3">
              <div>
                <h3 className="h6 fw-bold mb-1">Productos para reponer</h3>
                <p className="text-secondary small mb-0">Productos con stock igual o inferior al mínimo configurado.</p>
              </div>
              <span className="badge rounded-pill text-bg-warning">{estadisticas?.reposicion?.length ?? 0}</span>
            </div>
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead className="table-light">
                  <tr><th>Producto</th><th>Marca</th><th>Stock actual</th><th>Stock mínimo</th><th>Estado</th></tr>
                </thead>
                <tbody>
                  {(estadisticas?.reposicion ?? []).map((producto) => {
                    const critico = producto.stock <= producto.stock_critico;
                    return (
                      <tr key={producto.id}>
                        <td>{producto.producto}</td>
                        <td>{producto.marca || "—"}</td>
                        <td>{numero.format(producto.stock)} {producto.unidad_medida}</td>
                        <td>{numero.format(producto.stock_minimo)} {producto.unidad_medida}</td>
                        <td><span className={`badge ${critico ? "text-bg-danger" : "text-bg-warning"}`}>{critico ? "Crítico" : "Bajo mínimo"}</span></td>
                      </tr>
                    );
                  })}
                  {(estadisticas?.reposicion ?? []).length === 0 && (
                    <tr><td colSpan="5" className="text-center text-secondary py-4">No hay productos pendientes de reposición.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </section>
  );
}

const PanelAdministracion = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [actividad, setActividad] = useState([]);
  const [estadisticas, setEstadisticas] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const [listaUsuarios, listaActividad, resumenEstadisticas] = await Promise.all([
        getUsuarios(),
        getActividad(),
        getEstadisticasAdministracion(),
      ]);
      setUsuarios(listaUsuarios);
      setActividad(listaActividad);
      setEstadisticas(resumenEstadisticas);
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    const inicializar = window.setTimeout(cargar, 0);
    const intervalo = window.setInterval(cargar, 30000);
    return () => {
      window.clearTimeout(inicializar);
      window.clearInterval(intervalo);
    };
  }, [cargar]);

  return (
    <div className="inventario-container">
      <div className="header-inventario">
        <h1 className="titulo-izq">Administración</h1>
      </div>
      <div className="table-content-wrapper">
        {error && <div className="alert alert-danger" role="alert">{error}</div>}

        <PanelEstadisticas
          estadisticas={estadisticas}
          cargando={cargando}
          error={estadisticas ? error : ""}
          onActualizar={cargar}
        />

        <section className="card border-0 shadow-sm p-4 mb-4">
          <h2 className="h5 fw-bold mb-3">Usuarios registrados ({usuarios.length})</h2>
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr><th>Nombre</th><th>Usuario</th><th>Rol</th><th>Estado</th></tr>
              </thead>
              <tbody>
                {usuarios.map((user) => (
                  <tr key={user.id}>
                    <td>{user.nombre}</td>
                    <td>{user.usuario}</td>
                    <td>{user.rol}</td>
                    <td>{user.activo ? "Activo" : "Inactivo"}</td>
                  </tr>
                ))}
                {usuarios.length === 0 && (
                  <tr><td colSpan="4" className="text-center text-secondary py-4">No hay usuarios para mostrar.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="card border-0 shadow-sm p-4">
          <div className="d-flex align-items-center justify-content-between gap-3 mb-3">
            <h2 className="h5 fw-bold mb-0">Registro de movimientos</h2>
            <button className="btn btn-outline-primary btn-sm" type="button" onClick={cargar} disabled={cargando}>
              Actualizar
            </button>
          </div>
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr><th>Día</th><th>Hora</th><th>Usuario</th><th>Acción</th><th>Detalle</th></tr>
              </thead>
              <tbody>
                {actividad.map((item) => (
                  <tr key={item.id}>
                    <td className="text-nowrap">{item.fecha.slice(0, 10)}</td>
                    <td className="text-nowrap">{item.fecha.slice(11, 19)}</td>
                    <td>{item.usuario_nombre} <small className="text-secondary">({item.usuario})</small></td>
                    <td className="text-nowrap">{item.accion}</td>
                    <td>{item.detalle}</td>
                  </tr>
                ))}
                {actividad.length === 0 && (
                  <tr><td colSpan="5" className="text-center text-secondary py-4">Todavía no hay movimientos registrados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
};

const Administracion = ({ usuario, onAdminLogin }) => {
  if (usuario?.rol !== "Administrador") {
    return <LoginAdministrador onAdminLogin={onAdminLogin} />;
  }
  return <PanelAdministracion />;
};

export default Administracion;
