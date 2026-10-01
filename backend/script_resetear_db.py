import os
from database import init_db, DB_PATH

def resetear_db():
    print("Reseteando toda la base de datos...")
    
    # 1. Eliminar el archivo viejo si existe
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Archivo dietetica.db eliminado.")
        except Exception as e:
            print(f"Error eliminando archivo (Asegurate que no esté abierto): {e}")
            return
            
    # 2. Volver a crearla con las tablas de init_db()
    init_db()
    print("Base de datos creada desde cero con el usuario admin/123.")

if __name__ == "__main__":
    resetear_db()
