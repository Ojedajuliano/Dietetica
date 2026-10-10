import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import './Sidebar.css'

const Sidebar = ({ usuario, onCerrarSesion }) => {
  const [open, setOpen] = useState(false)

  const seccionesProductos = [
    { nombre: 'Ver todos', pagina: '/ver-todo' },
    { nombre: 'Catalogo', pagina: '/catalogo' },
    { nombre: 'Movimientos de stock', pagina: '/movimientos' },
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
          <NavLink to="/administracion">Administración</NavLink>
        </nav>
        <div className="mt-auto">
          <small className="d-block text-secondary mb-2">{usuario?.nombre}</small>
          <button className="btn btn-outline-secondary btn-sm w-100" type="button" onClick={onCerrarSesion}>
            Cerrar sesión
          </button>
        </div>
      </aside>
    </>
  )
}

export default Sidebar