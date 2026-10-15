# Gestión de productos e inventario

## Puesta en marcha

- Backend: desde `backend`, instalar `requirements.txt` y ejecutar `python app.py`.
- Frontend: desde `frontend`, ejecutar `npm install` y `npm run dev`.
- El frontend se conecta al backend Flask en `http://localhost:5000`.
- Iniciar sesión con el usuario inicial `admin` y contraseña `123`. Los empleados pueden crear su usuario desde la pantalla principal o el administrador puede gestionarlos desde **Administración**. En producción, definir la variable `FLASK_SECRET_KEY` antes de iniciar el backend.

Al iniciar, el backend crea las tablas de movimientos y lotes que falten y agrega a `productos` los campos necesarios para stock, tipo de venta, proveedor y códigos internos. Si la base ya tenía productos sin código, se les asigna un código `INT-` automáticamente. Los productos con movimientos o lotes se archivan al eliminarlos para conservar su historial.

## Operaciones disponibles

- Productos: alta y edición de nombre, marca, categoría, proveedor, código de barras, tipo de venta (unidad o peso), stock, costo, precio y umbrales mínimo/crítico. Al dar de alta, se solicita el vencimiento del lote inicial y se registra junto con el stock; luego se abre la pantalla de vencimientos. Las marcas y categorías se pueden crear desde el formulario y quedan guardadas. Si el código se deja vacío, se asigna uno interno único.
- Inventario: búsqueda por nombre o código, filtros por stock agotado, bajo/crítico y lotes próximos a vencer. El resumen presenta valuación al costo y al precio de venta.
- Precios: actualización masiva por porcentaje o monto, limitada opcionalmente por categoría y proveedor. Un valor negativo aplica un descuento.
- Lotes y vencimientos: registrar cantidad y fecha de vencimiento de cada lote. El ingreso suma esa cantidad al stock; la pantalla alerta sobre lotes vencidos y los próximos a vencer en 30 días.
- Caja: abrir con un monto inicial, registrar ingresos y egresos, consultar el saldo esperado, hacer cierres parciales o finales y consultar diferencias e historial. Las ventas registradas durante una caja abierta se agregan automáticamente como ingresos.
- Proveedores: asociar productos a un proveedor existente o escribir el nombre de uno nuevo. Cada producto tiene un proveedor asignado, y se puede buscar y filtrar el listado por proveedor.
- Movimientos: registrar mermas, roturas, consumo propio, bajas por vencimiento y devoluciones, siempre con cantidad y justificación. Las bajas reducen stock; las devoluciones lo reincorporan. Los ajustes manuales y el stock inicial también quedan en el historial.
- Usuarios y auditoría: las cuentas de empleados se crean desde la pantalla principal o desde Administración y se almacenan con contraseña protegida en SQLite. Allí también se consulta el registro de compras, ventas, cambios de productos y movimientos de stock, incluyendo usuario, día y hora. El inventario requiere iniciar sesión.

## API de inventario

- `POST /api/auth/login`, `POST /api/auth/admin-login`, `GET /api/auth/me`, `POST /api/auth/logout`
- `POST /api/auth/register` (crea una cuenta de empleado e inicia su sesión)
- `GET/POST /api/usuarios` y `GET /api/administracion/actividad` (solo administrador)
- `GET/POST /api/productos`, `GET/PUT/DELETE /api/productos/<id>`
- `PATCH /api/productos/<id>/stock`
- `GET /api/caja`, `POST /api/caja/apertura`, `POST /api/caja/movimientos`, `POST /api/caja/cierres`
- `GET /api/inventario/resumen`, `GET/POST /api/categorias`, `GET/POST /api/marcas`, `GET /api/proveedores`, `POST /api/proveedores/asociaciones`
- `POST /api/precios/actualizacion-masiva`
- `GET/POST /api/lotes`
- `GET/POST /api/movimientos`

Las cantidades son decimales para permitir productos fraccionados y vendidos por peso.
Las rutas de inventario requieren una sesión iniciada; las compras, ventas, modificaciones y eliminaciones se registran para su consulta desde Administración.