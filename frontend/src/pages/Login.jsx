import { useState } from "react";
import { iniciarSesion, registrarEmpleado } from "../api/auth";

const FORM_INICIAL = { nombre: "", usuario: "", password: "" };

const Login = ({ onLogin }) => {
  const [usuario, setUsuario] = useState("");
  const [password, setPassword] = useState("");
  const [registro, setRegistro] = useState(FORM_INICIAL);
  const [errorLogin, setErrorLogin] = useState("");
  const [errorRegistro, setErrorRegistro] = useState("");
  const [ingresando, setIngresando] = useState(false);
  const [registrando, setRegistrando] = useState(false);

  const ingresar = async (event) => {
    event.preventDefault();
    setErrorLogin("");
    setIngresando(true);
    try {
      const data = await iniciarSesion(usuario.trim(), password);
      onLogin(data.usuario);
    } catch (e) {
      setErrorLogin(e.message);
    } finally {
      setIngresando(false);
    }
  };

  const crearCuenta = async (event) => {
    event.preventDefault();
    setErrorRegistro("");
    setRegistrando(true);
    try {
      const data = await registrarEmpleado(registro);
      onLogin(data.usuario);
    } catch (e) {
      setErrorRegistro(e.message);
    } finally {
      setRegistrando(false);
    }
  };

  return (
    <main className="container min-vh-100 d-flex flex-column justify-content-center py-4">
      <header className="text-center mb-4">
        <h1 className="h2 fw-bold text-primary">Dietética y Nutrición</h1>
        <p className="text-secondary mb-0">Sistema de gestión de inventario</p>
      </header>
      <div className="row g-4 justify-content-center">
        <div className="col-12 col-lg-5">
          <section className="card border-0 shadow p-4 rounded-4 h-100">
            <h2 className="h4 fw-bold mb-1">Iniciar sesión</h2>
            <p className="text-secondary mb-4">Ingresá con tu cuenta de empleado o administrador.</p>
            {errorLogin && <div className="alert alert-danger" role="alert">{errorLogin}</div>}
            <form onSubmit={ingresar}>
              <label className="form-label" htmlFor="login-usuario">Usuario</label>
              <input
                id="login-usuario"
                className="form-control mb-3"
                autoComplete="username"
                value={usuario}
                onChange={(event) => setUsuario(event.target.value)}
                required
              />
              <label className="form-label" htmlFor="login-password">Contraseña</label>
              <input
                id="login-password"
                className="form-control mb-4"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
              <button className="btn btn-primary w-100" type="submit" disabled={ingresando}>
                {ingresando ? "Ingresando..." : "Ingresar"}
              </button>
            </form>
          </section>
        </div>
        <div className="col-12 col-lg-5">
          <section className="card border-0 shadow p-4 rounded-4 h-100">
            <h2 className="h4 fw-bold mb-1">Crear usuario</h2>
            <p className="text-secondary mb-4">Registrá una cuenta de empleado para ingresar al sistema.</p>
            {errorRegistro && <div className="alert alert-danger" role="alert">{errorRegistro}</div>}
            <form onSubmit={crearCuenta}>
              <label className="form-label" htmlFor="registro-nombre">Nombre completo</label>
              <input
                id="registro-nombre"
                className="form-control mb-3"
                autoComplete="name"
                minLength={2}
                maxLength={80}
                value={registro.nombre}
                onChange={(event) => setRegistro({ ...registro, nombre: event.target.value })}
                required
              />
              <label className="form-label" htmlFor="registro-usuario">Usuario</label>
              <input
                id="registro-usuario"
                className="form-control mb-3"
                autoComplete="username"
                minLength={3}
                maxLength={30}
                pattern="[A-Za-z0-9._-]+"
                title="Usá letras, números, punto, guion o guion bajo"
                value={registro.usuario}
                onChange={(event) => setRegistro({ ...registro, usuario: event.target.value })}
                required
              />
              <label className="form-label" htmlFor="registro-password">Contraseña</label>
              <input
                id="registro-password"
                className="form-control mb-2"
                type="password"
                autoComplete="new-password"
                minLength={8}
                pattern="(?=.*[A-Za-z])(?=.*[0-9]).{8,}"
                title="Debe tener al menos 8 caracteres, una letra y un número"
                value={registro.password}
                onChange={(event) => setRegistro({ ...registro, password: event.target.value })}
                required
              />
              <small className="text-secondary d-block mb-4">
                Mínimo 8 caracteres, incluyendo una letra y un número. La contraseña se guarda protegida.
              </small>
              <button className="btn btn-outline-primary w-100" type="submit" disabled={registrando}>
                {registrando ? "Creando usuario..." : "Crear usuario e ingresar"}
              </button>
            </form>
          </section>
        </div>
      </div>
    </main>
  );
};

export default Login;
