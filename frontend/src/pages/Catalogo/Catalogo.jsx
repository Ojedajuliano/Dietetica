import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSearchParams } from "react-router-dom";
import "../Inventario/Inventario.css";
import Tablas from "../../components/Tablas/Tablas";
import { getCategorias, getProductos } from "../../api/productos";

const Catalogo = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const categoria = searchParams.get("categoria") || "";
  const [productos, setProductos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [busqueda, setBusqueda] = useState("");
  const [error, setError] = useState("");

  const cargar = async (q = busqueda, cat = categoria) => {
    try {
      setProductos(await getProductos({ q, categoria: cat }));
      setError("");
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    getCategorias().then(setCategorias).catch(() => {});
  }, []);

  useEffect(() => {
    let vigente = true;
    getProductos({ categoria })
      .then((resultado) => {
        if (vigente) {
          setProductos(resultado);
          setError("");
        }
      })
      .catch((e) => {
        if (vigente) setError(e.message);
      });
    return () => { vigente = false; };
  }, [categoria]);

  const seleccionarCategoria = (nuevaCategoria) => {
    setSearchParams(nuevaCategoria ? { categoria: nuevaCategoria } : {});
  };

  return (
    <div className="inventario-container">
      <div className="header-inventario">
        <h1 className="titulo-izq">Catálogo por categoría</h1>
        <form className="search-box" onSubmit={(e) => { e.preventDefault(); cargar(); }}>
          <input
            type="text"
            placeholder="Buscar producto..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          <button type="submit">Buscar</button>
        </form>
      </div>
      <div className="table-content-wrapper">
        {error && <p className="text-danger">{error}</p>}
        <div className="filtros-inventario">
          <button className={`filtro-btn ${categoria === "" ? "activo" : ""}`} onClick={() => seleccionarCategoria("")}>Todas</button>
          {categorias.map((c) => (
            <button
              key={c}
              className={`filtro-btn ${categoria === c ? "activo" : ""}`}
              onClick={() => seleccionarCategoria(c)}
            >
              {c}
            </button>
          ))}
        </div>
        <Tablas
          productos={productos}
          onRefresh={() => cargar()}
          onAgregar={() => navigate("/nuevo-producto")}
        />
      </div>
    </div>
  );
};

export default Catalogo;
