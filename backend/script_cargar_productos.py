import sqlite3
from database import get_connection, crear_producto

productos_demo = [
    {
        "nombre": "Almendras Peladas",
        "marca": "Nuts&Co",
        "categoria": "Frutos secos",
        "codigo_barras": "7791234567890",
        "tipo_venta": "peso",
        "stock": 15.5,
        "costo": 8000,
        "precio_venta": 12000,
        "stock_minimo": 2.0,
        "stock_critico": 0.5,
        "proveedor": "Distribuidora San Juan"
    },
    {
        "nombre": "Proteína Whey Vainilla 1kg",
        "marca": "Star Nutrition",
        "categoria": "Proteínas",
        "codigo_barras": "7799876543210",
        "tipo_venta": "unidad",
        "stock": 10,
        "costo": 15000,
        "precio_venta": 22000,
        "stock_minimo": 3,
        "stock_critico": 1,
        "proveedor": "Suplementos Mayorista"
    },
    {
        "nombre": "Mantequilla de Maní Natural 500g",
        "marca": "Hardcore",
        "categoria": "Snacks",
        "codigo_barras": "",
        "tipo_venta": "unidad",
        "stock": 24,
        "costo": 3500,
        "precio_venta": 5000,
        "stock_minimo": 5,
        "stock_critico": 2,
        "proveedor": "Hardcore Oficial"
    },
    {
        "nombre": "Creatina Monohidratada 300g",
        "marca": "ENA",
        "categoria": "Creatinas",
        "codigo_barras": "7791122334455",
        "tipo_venta": "unidad",
        "stock": 0,
        "costo": 18000,
        "precio_venta": 25000,
        "stock_minimo": 5,
        "stock_critico": 2,
        "proveedor": "Suplementos Mayorista"
    }
]

def cargar_productos():
    print("Cargando productos de prueba...")
    for prod in productos_demo:
        try:
            crear_producto(prod)
            print(f"OK: {prod['nombre']} agregado correctamente.")
        except Exception as e:
            print(f"Error agregando {prod['nombre']}: {e}")
    print("¡Proceso completado!")

if __name__ == "__main__":
    cargar_productos()
