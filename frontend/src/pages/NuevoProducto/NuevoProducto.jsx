import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./NuevoProducto.css";
import {
  actualizarProducto,
  crearCategoria,
  crearMarca,
  crearProducto,
  getCategorias,
  getMarcas,
  getProducto,
} from "../../api/productos";

const VACIO = {
  nombre: "",
  marca: "",
  categoria: "",
  proveedor: "",
  codigo_barras: "",
  tipo_venta: "unidad",
  stock: "",
  costo: "",
  precio_venta: "",
  stock_minimo: "",
  stock_critico: "",
};

const NuevoProducto = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState(VACIO);
  const [categorias, setCategorias] = useState([]);
  const [marcas, setMarcas] = useState([]);
  const [nuevaCategoria, setNuevaCategoria] = useState("");
  const [nuevaMarca, setNuevaMarca] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [guardandoCategoria, setGuardandoCategoria] = useState(false);
  const [guardandoMarca, setGuardandoMarca] = useState(false);
  const esEdicion = Boolean(id);

  useEffect(() => {
    Promise.all([getCategorias(), getMarcas()])
      .then(([listaCategorias, listaMarcas]) => {
        setCategorias(listaCategorias);
        setMarcas(listaMarcas);
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!id) return;

    getProducto(id)
      .then((producto) => {
        setForm({
          nombre: producto.nombre || "",
          marca: producto.marca || "",
          categoria: producto.categoria || "",
          proveedor: producto.proveedor || "",
          codigo_barras: producto.codigo_interno ? "" : producto.codigo_barras || "",
          tipo_venta: producto.tipo_venta || "unidad",
          stock: String(producto.stock ?? ""),
          costo: String(producto.costo ?? ""),
          precio_venta: String(producto.precio_venta ?? ""),
          stock_minimo: String(producto.stock_minimo ?? ""),
          stock_critico: String(producto.stock_critico ?? ""),
        });
      })
      .catch((e) => setError(e.message));
  }, [id]);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleCrearCategoria = async () => {
    setError("");
    setMensaje("");
    setGuardandoCategoria(true);
    try {
      const creada = await crearCategoria(nuevaCategoria);
      setCategorias((actuales) => [...actuales, creada.nombre].sort((a, b) => a.localeCompare(b)));
      setForm((actual) => ({ ...actual, categoria: creada.nombre }));
      setNuevaCategoria("");
      setMensaje("Categoría guardada");
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardandoCategoria(false);
    }
  };

  const handleCrearMarca = async () => {
    setError("");
    setMensaje("");
    setGuardandoMarca(true);
    try {
      const creada = await crearMarca(nuevaMarca);
      setMarcas((actuales) => [...actuales, creada.nombre].sort((a, b) => a.localeCompare(b)));
      setForm((actual) => ({ ...actual, marca: creada.nombre }));
      setNuevaMarca("");
      setMensaje("Marca guardada");
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardandoMarca(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMensaje("");
    setGuardando(true);

    const payload = {
      ...form,
      stock: form.stock === "" ? 0 : Number(form.stock),
      costo: form.costo === "" ? 0 : Number(form.costo),
      precio_venta: form.precio_venta === "" ? 0 : Number(form.precio_venta),
      stock_minimo: form.stock_minimo === "" ? 0 : Number(form.stock_minimo),
      stock_critico: form.stock_critico === "" ? 0 : Number(form.stock_critico),
    };

    try {
      if (esEdicion) {
        await actualizarProducto(id, payload);
        setMensaje("Producto actualizado");
      } else {
        await crearProducto(payload);
        setMensaje("Producto guardado");
        setForm(VACIO);
      }
      setTimeout(() => navigate("/inventario"), 600);
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <>
      <div className="header-inventario">
        <h1 className="titulo-izq">
          {esEdicion ? "Editar producto" : "Nuevo producto"}
        </h1>
      </div>
      <div className="nuevo-producto-container">
        <form className="container-info-prods" onSubmit={handleSubmit}>
          <div className="card-header">
            <span className="icon-info">ⓘ</span>
            <h3>Información General</h3>
          </div>
          <hr className="divider" />

          <div className="campo-grupo">
            <label>Nombre del producto</label>
            <input
              name="nombre"
              type="text"
              placeholder="Ej: Proteína Whey"
              value={form.nombre}
              onChange={onChange}
              required
            />
          </div>

          <div className="campos-form">
            <div className="campo-grupo">
              <label>Marca</label>
              <select name="marca" value={form.marca} onChange={onChange}>
                <option value="">Seleccione una marca</option>
                {marcas.map((marca) => (
                  <option key={marca} value={marca}>{marca}</option>
                ))}
              </select>
              <div className="agregar-categoria">
                <input
                  type="text"
                  aria-label="Nueva marca"
                  placeholder="Nueva marca"
                  value={nuevaMarca}
                  onChange={(e) => setNuevaMarca(e.target.value)}
                />
                <button
                  type="button"
                  onClick={handleCrearMarca}
                  disabled={guardandoMarca || !nuevaMarca.trim()}
                >
                  {guardandoMarca ? "Guardando..." : "Agregar"}
                </button>
              </div>
            </div>
            <div className="campo-grupo">
              <label>Categoría</label>
              <select name="categoria" value={form.categoria} onChange={onChange} required>
                <option value="">Seleccione una categoría</option>
                {categorias.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <div className="agregar-categoria">
                <input
                  type="text"
                  aria-label="Nueva categoría"
                  placeholder="Nueva categoría"
                  value={nuevaCategoria}
                  onChange={(e) => setNuevaCategoria(e.target.value)}
                />
                <button
                  type="button"
                  onClick={handleCrearCategoria}
                  disabled={guardandoCategoria || !nuevaCategoria.trim()}
                >
                  {guardandoCategoria ? "Guardando..." : "Agregar"}
                </button>
              </div>
            </div>
            <div className="campo-grupo">
              <label>Proveedor</label>
              <input
                name="proveedor"
                type="text"
                placeholder="Nombre del proveedor"
                value={form.proveedor}
                onChange={onChange}
              />
            </div>
          </div>

          <div className="campos-form">
            <div className="campo-grupo">
              <label>Código de barras</label>
              <input
                name="codigo_barras"
                type="text"
                placeholder="Vacío = código interno automático"
                value={form.codigo_barras}
                onChange={onChange}
              />
            </div>
            <div className="campo-grupo">
              <label>Se vende por</label>
              <select name="tipo_venta" value={form.tipo_venta} onChange={onChange}>
                <option value="unidad">Unidad</option>
                <option value="peso">Peso (kg)</option>
              </select>
            </div>
          </div>

          <div className="campos-form">
            <div className="campo-grupo">
              <label>Stock actual</label>
              <input
                name="stock"
                type="number"
                min="0"
                step={form.tipo_venta === "peso" ? "0.01" : "1"}
                placeholder={form.tipo_venta === "peso" ? "0.00" : "0"}
                value={form.stock}
                onChange={onChange}
              />
            </div>
            <div className="campo-grupo">
              <label>Costo</label>
              <input
                name="costo"
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={form.costo}
                onChange={onChange}
              />
            </div>
            <div className="campo-grupo">
              <label>Precio de venta</label>
              <input
                name="precio_venta"
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={form.precio_venta}
                onChange={onChange}
              />
            </div>
          </div>

          <div className="campos-form">
            <div className="campo-grupo">
              <label>Stock mínimo (alerta)</label>
              <input
                name="stock_minimo"
                type="number"
                min="0"
                step={form.tipo_venta === "peso" ? "0.01" : "1"}
                value={form.stock_minimo}
                onChange={onChange}
              />
            </div>
          </div>

          {error && <p className="form-error">{error}</p>}
          {mensaje && <p className="form-ok">{mensaje}</p>}

          <div className="botones-form">
            <button type="button" className="btn-cancelar" onClick={() => navigate("/inventario")}>
              Cancelar
            </button>
            <button className="btn-guardar" type="submit" disabled={guardando}>
              {guardando ? "Guardando..." : esEdicion ? "Guardar cambios" : "Guardar producto"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
};

export default NuevoProducto;
