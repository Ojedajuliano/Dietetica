import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import './Sidebar.css'

const Sidebar = () => {
  const [open, setOpen] = useState(false)

  const seccionesProductos = [
    { nombre: 'Ver todos', pagina: '/ver-todo' },
    { nombre: 'Catalogo', pagina: '/catalogo' },
    { nombre: 'Movimientos', pagina: '/movimientos' },
    { nombre: 'Vencimiento', pagina: '/vencimiento' },
  ]

  return (
    <>
      <aside className='sidebar'>
        <h1>Dietética y <br />
        Nutrición</h1>
        <hr />
        <nav>
          <NavLink to="/inventario">Inventario</NavLink>
          <NavLink to="/nuevo-producto">Nuevo Producto</NavLink>

          <div className="dropdown-wrapper">
            <button
              type="button"
              className="dropdown-toggle"
              onClick={() => setOpen(!open)}
            >
              Productos
            </button>

            <div className={`dropdown-content ${open ? 'dropdown-open' : ''}`}>
              {seccionesProductos.map((s) => (
                <NavLink key={s.nombre} to={s.pagina} className="dropdown-item">
                  {s.nombre}
                </NavLink>
              ))}
            </div>
          </div>
          <NavLink to="/compra-venta">Compra Venta</NavLink>
          {/* <NavLink to="/historial">Historial</NavLink> */}
          <NavLink to="/administracion">Administracion</NavLink>
        </nav>
      </aside>
    </>
  )
}

export default Sidebar