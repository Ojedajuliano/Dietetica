import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getActividad, getUsuarios, iniciarSesionAdministrador } from "../../api/auth";
import "../Inventario/Inventario.css";

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

const PanelAdministracion = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [actividad, setActividad] = useState([]);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      const [listaUsuarios, listaActividad] = await Promise.all([
        getUsuarios(),
        getActividad(),
      ]);
      setUsuarios(listaUsuarios);
      setActividad(listaActividad);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    Promise.all([getUsuarios(), getActividad()])
      .then(([listaUsuarios, listaActividad]) => {
        setUsuarios(listaUsuarios);
        setActividad(listaActividad);
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    const actualizarActividad = () => {
      getActividad()
        .then(setActividad)
        .catch((e) => setError(e.message));
    };
    const intervalo = window.setInterval(actualizarActividad, 10000);
    return () => window.clearInterval(intervalo);
  }, []);

  return (
    <div className="inventario-container">
      <div className="header-inventario">
        <h1 className="titulo-izq">Administración</h1>
      </div>
      <div className="table-content-wrapper">
        {error && <div className="alert alert-danger">{error}</div>}

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
            <button className="btn btn-outline-primary btn-sm" type="button" onClick={cargar}>
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
