import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import "./App.css";
import { cerrarSesion, getUsuarioActual } from "./api/auth";
import Sidebar from "./components/Sidebar/Sidebar";
import Administracion from "./pages/Administracion/Administracion";
import Caja from "./pages/Caja/Caja";
import Catalogo from "./pages/Catalogo/Catalogo";
import CompraVenta from "./pages/CompraVenta/CompraVenta";
import Inventario from "./pages/Inventario/Inventario";
import Movimientos from "./pages/Movimientos/Movimientos";
import NuevoProducto from "./pages/NuevoProducto/NuevoProducto";
import Productos from "./pages/Productos/Productos";
import Proveedores from "./pages/Proveedores/Proveedores";
import Vencimiento from "./pages/Vencimiento/Vencimiento";
import Login from "./pages/Login";

function LayoutPrivado({ usuario, onCerrarSesion }) {
  return (
    <div className="layout">
      <Sidebar usuario={usuario} onCerrarSesion={onCerrarSesion} />
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}

function App() {
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    getUsuarioActual()
      .then(({ usuario: actual }) => setUsuario(actual))
      .catch(() => setUsuario(null))
      .finally(() => setCargando(false));
  }, []);

  const salir = async () => {
    try {
      await cerrarSesion();
      setUsuario(null);
    } catch (error) {
      window.alert(`No se pudo cerrar la sesión: ${error.message}`);
    }
  };

  if (cargando) {
    return <div className="d-flex min-vh-100 align-items-center justify-content-center">Cargando...</div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={usuario ? <Navigate to="/inventario" replace /> : <Login onLogin={setUsuario} />}
        />
        <Route
          element={usuario ? (
            <LayoutPrivado usuario={usuario} onCerrarSesion={salir} />
          ) : (
            <Navigate to="/login" replace />
          )}
        >
          <Route path="/" element={<Navigate to="/inventario" replace />} />
          <Route path="/inventario" element={<Inventario />} />
          <Route path="/nuevo-producto" element={<NuevoProducto />} />
          <Route path="/nuevo-producto/:id" element={<NuevoProducto />} />
          <Route path="/ver-todo" element={<Productos />} />
          <Route path="/catalogo" element={<Catalogo />} />
          <Route path="/movimientos" element={<Movimientos />} />
          <Route path="/vencimiento" element={<Vencimiento />} />
          <Route path="/caja" element={<Caja />} />
          <Route path="/proveedores" element={<Proveedores />} />
          <Route path="/compra-venta" element={<CompraVenta />} />
          <Route
            path="/administracion"
            element={<Administracion usuario={usuario} onAdminLogin={setUsuario} />}
          />
          <Route path="*" element={<Navigate to="/inventario" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
