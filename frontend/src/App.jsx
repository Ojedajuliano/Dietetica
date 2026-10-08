import './App.css'
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from './components/Sidebar/Sidebar'
import Inventario from './pages/Inventario/Inventario'
import NuevoProducto from './pages/NuevoProducto/NuevoProducto'
import Productos from './pages/Productos/Productos'
import Administracion from './pages/Administracion/Administracion'
import Catalogo from './pages/Catalogo/Catalogo'
import Movimientos from './pages/Movimientos/Movimientos'
import Vencimiento from './pages/Vencimiento/Vencimiento'
import Historial from './pages/Historial/Historial'
import Panel from './pages/Panel/Panel'
import CompraVenta from './pages/CompraVenta/CompraVenta'

function App() {

  return (
    <BrowserRouter>

      <div className="layout">
        <Sidebar />

        <main className="content">
          <Routes>
            <Route path='/' element={<Navigate to="/inventario" />} />
            <Route path='/inventario' element={<Inventario />} />
            <Route path='/nuevo-producto' element={<NuevoProducto />} />
            <Route path='/nuevo-producto/:id' element={<NuevoProducto />} />
            <Route path='/ver-todo' element={<Productos />} />
            <Route path='/catalogo' element={<Catalogo />} />
            <Route path='/movimientos' element={<Movimientos />} />
            <Route path='/vencimiento' element={<Vencimiento />} />
            <Route path='/compra-venta' element={<CompraVenta />} />
            {/* <Route path='/historial' element={<Historial />} /> */}
            <Route path='/administracion' element={<Administracion />} />
            <Route path='/Panel' element={<Panel />} />
          </Routes>
        </main>
      </div>

    </BrowserRouter>
  )
}

export default App
