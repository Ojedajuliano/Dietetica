import sqlite3
from database import get_connection

def simular_ventas():
    print("Simulando ventas (movimientos de salida) en el historial...")
    conn = get_connection()
    
    # Obtener algunos productos para simularles ventas
    productos = conn.execute("SELECT id, nombre, stock FROM productos WHERE stock > 0 LIMIT 2").fetchall()
    
    if not productos:
        print("Error: No hay productos con stock para simular ventas. Corre script_cargar_productos.py primero.")
        return

    for prod in productos:
        prod_id = prod["id"]
        cantidad_vendida = 1.0
        nuevo_stock = float(prod["stock"]) - cantidad_vendida
        
        # Descontar stock
        conn.execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, prod_id))

        # Registrar el movimiento falso de tipo "venta" para que salga en el historial
        conn.execute(
            """
            INSERT INTO inventario_movimientos (producto_id, tipo, cantidad, motivo)
            VALUES (?, 'salida', ?, 'Venta de mostrador (Demo)')
            """,
            (prod_id, cantidad_vendida)
        )
        print(f"OK: Venta simulada: 1.0 de {prod['nombre']}")

    conn.commit()
    conn.close()
    print("¡Ventas simuladas completadas!")

if __name__ == "__main__":
    simular_ventas()
