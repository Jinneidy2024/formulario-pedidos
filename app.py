from flask import Flask, request, render_template_string, send_file
import sqlite3, os
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Crear carpeta de uploads si no existe
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Lista de productos disponibles
PRODUCTOS = [
    "Producto A",
    "Producto B",
    "Producto C",
    "Producto D",
    "Producto E",
    "Producto F",
    "Producto G"
]

# Crear base de datos
def init_db():
    with sqlite3.connect("pedidos.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consecutivo TEXT UNIQUE NOT NULL,
                fecha_pedido TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                codigo_cliente TEXT NOT NULL,
                fecha_entrega TEXT NOT NULL,
                direccion_entrega TEXT NOT NULL,
                contacto TEXT NOT NULL,
                comentarios TEXT,
                archivo_oc TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedido_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                producto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
            )
        """)

init_db()

# Generar consecutivo único
def generar_consecutivo():
    fecha = datetime.now().strftime("%Y%m%d")
    with sqlite3.connect("pedidos.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE consecutivo LIKE ?", (f"{fecha}%",))
        count = cursor.fetchone()[0] + 1
    return f"{fecha}-{count:04d}"

# FORMULARIO CORPORATIVO
form_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Formulario de Pedidos</title>

    <link rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">

    <style>
        body {
            background: #f0f2f5;
            font-family: "Segoe UI", Arial, sans-serif;
        }
        .card {
            border-radius: 12px;
            border: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .btn-primary {
            background-color: #0056b3;
            border-color: #004a99;
        }
        .btn-primary:hover {
            background-color: #003f87;
        }
        .section-title {
            font-weight: 600;
            color: #003366;
            margin-bottom: 15px;
        }
        label {
            font-weight: 500;
        }
    </style>
</head>

<body class="p-4">

    <div class="container">

        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="text-primary">Registro de Pedido</h2>
            <a href="/pedidos" class="btn btn-outline-primary">Ver pedidos</a>
        </div>

        <div class="card p-4">

            <form method="post" action="/registrar" enctype="multipart/form-data">

                <h4 class="section-title">Datos del Cliente</h4>

                <div class="row mb-3">
                    <div class="col-md-6">
                        <label>Fecha del Pedido</label>
                        <input type="date" name="fecha_pedido" class="form-control" required>
                    </div>

                    <div class="col-md-6">
                        <label>Fecha de Entrega</label>
                        <input type="date" name="fecha_entrega" class="form-control" required>
                    </div>
                </div>

                <div class="mb-3">
                    <label>Nombre del Cliente</label>
                    <input type="text" name="nombre_cliente" class="form-control" required>
                </div>

                <div class="mb-3">
                    <label>Código del Cliente</label>
                    <input type="text" name="codigo_cliente" class="form-control" required>
                </div>

                <div class="mb-3">
                    <label>Dirección de Entrega</label>
                    <input type="text" name="direccion_entrega" class="form-control" required>
                </div>

                <div class="mb-3">
                    <label>Contacto (correo del cliente)</label>
                    <input type="email" name="contacto" class="form-control" required>
                </div>

                <div class="mb-3">
                    <label>Comentarios</label>
                    <textarea name="comentarios" class="form-control" rows="3"></textarea>
                </div>

                <div class="mb-4">
                    <label>Orden de Compra (PDF, JPG, PNG)</label>
                    <input type="file" name="archivo_oc" class="form-control" accept=".pdf,.jpg,.png">
                </div>

                <h4 class="section-title">Productos y Cantidades</h4>

                {% for p in productos %}
                <div class="row align-items-center mb-3">
                    <div class="col-md-6">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="producto[]" value="{{p}}">
                            <label class="form-check-label">{{p}}</label>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <input type="number" class="form-control"
                               name="cantidad_{{ p.replace(' ', '_') }}" min="1"
                               placeholder="Cantidad">
                    </div>
                </div>
                {% endfor %}

                <div class="text-end mt-4">
                    <button type="submit" class="btn btn-primary btn-lg">
                        Registrar Pedido
                    </button>
                </div>

            </form>
        </div>
    </div>

</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(form_html, productos=PRODUCTOS)

@app.route("/registrar", methods=["POST"])
def registrar():
    consecutivo = generar_consecutivo()

    fecha_pedido = request.form["fecha_pedido"]
    nombre_cliente = request.form["nombre_cliente"]
    codigo_cliente = request.form["codigo_cliente"]
    fecha_entrega = request.form["fecha_entrega"]
    direccion_entrega = request.form["direccion_entrega"]
    contacto = request.form["contacto"]
    comentarios = request.form.get("comentarios", "")

    archivo = request.files.get("archivo_oc")
    archivo_nombre = None

    if archivo and archivo.filename != "":
        archivo_nombre = f"{consecutivo}_{secure_filename(archivo.filename)}"
        archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], archivo_nombre))

    with sqlite3.connect("pedidos.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO pedidos (consecutivo, fecha_pedido, nombre_cliente, codigo_cliente,
                                 fecha_entrega, direccion_entrega, contacto, comentarios, archivo_oc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (consecutivo, fecha_pedido, nombre_cliente, codigo_cliente,
              fecha_entrega, direccion_entrega, contacto, comentarios, archivo_nombre))

        pedido_id = cursor.lastrowid

        productos = request.form.getlist("producto[]")

        for p in productos:
            key = f"cantidad_{p.replace(' ', '_')}"
            cantidad = request.form.get(key, 0)

            if cantidad and int(cantidad) > 0:
                cursor.execute("""
                    INSERT INTO pedido_detalle (pedido_id, producto, cantidad)
                    VALUES (?, ?, ?)
                """, (pedido_id, p, cantidad))

        conn.commit()

    return f"Pedido registrado con consecutivo: {consecutivo} <br><br><a href='/'>Nuevo pedido</a> | <a href='/pedidos'>Ver pedidos</a>"

# LISTADO CORPORATIVO
@app.route("/pedidos")
def pedidos():
    with sqlite3.connect("pedidos.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, consecutivo, fecha_pedido, nombre_cliente, codigo_cliente, fecha_entrega
            FROM pedidos
            ORDER BY id DESC
        """)
        datos = cursor.fetchall()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Listado de Pedidos</title>
        <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>

    <body class="p-4" style="background:#f0f2f5; font-family:Segoe UI, Arial;">
        <div class="container">

            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2 class="text-primary">Listado de Pedidos</h2>
                <a href="/" class="btn btn-outline-primary">Nuevo pedido</a>
            </div>

            <form method="get" action="/buscar" class="mb-4">
                <div class="input-group">
                    <input type="text" name="q" class="form-control" placeholder="Buscar por cliente, consecutivo o fecha">
                    <button class="btn btn-primary">Buscar</button>
                </div>
            </form>

            <a href="/exportar_excel" class="btn btn-success mb-3">Exportar a Excel</a>

            <div class="card p-3 shadow-sm">
                <table class="table table-striped table-hover">
                    <thead class="table-primary">
                        <tr>
                            <th>ID</th>
                            <th>Consecutivo</th>
                            <th>Fecha Pedido</th>
                            <th>Cliente</th>
                            <th>Código</th>
                            <th>Fecha Entrega</th>
                            <th>Detalle</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for row in datos:
        html += f"""
            <tr>
                <td>{row[0]}</td>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td>{row[3]}</td>
                <td>{row[4]}</td>
                <td>{row[5]}</td>
                <td><a class="btn btn-sm btn-primary" href="/detalle/{row[0]}">Ver</a></td>
            </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    return html

# BUSQUEDA CORPORATIVA
@app.route("/buscar")
def buscar():
    q = request.args.get("q", "")

    with sqlite3.connect("pedidos.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, consecutivo, fecha_pedido, nombre_cliente, codigo_cliente, fecha_entrega
            FROM pedidos
            WHERE nombre_cliente LIKE ? OR codigo_cliente LIKE ? OR consecutivo LIKE ? OR fecha_pedido LIKE ?
            ORDER BY id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"))
        datos = cursor.fetchall()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resultados de búsqueda</title>
        <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>

    <body class="p-4" style="background:#f0f2f5; font-family:Segoe UI, Arial;">
        <div class="container">

            <h2 class="text-primary">Resultados de búsqueda: {q}</h2>
            <a href="/pedidos" class="btn btn-outline-primary mb-3">Volver</a>

            <div class="card p-3 shadow-sm">
                <table class="table table-striped table-hover">
                    <thead class="table-primary">
                        <tr>
                            <th>ID</th>
                            <th>Consecutivo</th>
                            <th>Fecha Pedido</th>
                            <th>Cliente</th>
                            <th>Código</th>
                            <th>Fecha Entrega</th>
                            <th>Detalle</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for row in datos:
        html += f"""
            <tr>
                <td>{row[0]}</td>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td>{row[3]}</td>
                <td>{row[4]}</td>
                <td>{row[5]}</td>
                <td><a class="btn btn-sm btn-primary" href="/detalle/{row[0]}">Ver</a></td>
            </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    return html

# DETALLE CORPORATIVO
@app.route("/detalle/<int:pedido_id>")
def detalle(pedido_id):
    with sqlite3.connect("pedidos.db") as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
        pedido = cursor.fetchone()

        cursor.execute("SELECT producto, cantidad FROM pedido_detalle WHERE pedido_id = ?", (pedido_id,))
        detalles = cursor.fetchall()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Detalle del Pedido</title>
        <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>

    <body class="p-4" style="background:#f0f2f5; font-family:Segoe UI, Arial;">
        <div class="container">

            <h2 class="text-primary mb-4">Detalle del Pedido {pedido[1]}</h2>

            <div class="card p-4 shadow-sm mb-4">
                <h4 class="text-secondary">Información del Cliente</h4>
                <p><b>Cliente:</b> {pedido[3]} ({pedido[4]})</p>
                <p><b>Fecha Pedido:</b> {pedido[2]}</p>
                <p><b>Fecha Entrega:</b> {pedido[5]}</p>
                <p><b>Dirección:</b> {pedido[6]}</p>
                <p><b>Contacto:</b> {pedido[7]}</p>
                <p><b>Comentarios:</b> {pedido[8]}</p>
            </div>

            <div class="card p-4 shadow-sm">
                <h4 class="text-secondary">Productos</h4>
                <ul class="list-group">
    """

    for p in detalles:
        html += f"<li class='list-group-item'>{p[0]} — {p[1]} unidades</li>"

    html += """
                </ul>
            </div>

            <a href="/pedidos" class="btn btn-outline-primary mt-4">Volver</a>

        </div>
    </body>
    </html>
    """

    return html

# EXPORTAR EXCEL
@app.route("/exportar_excel")
def exportar_excel():
    conn = sqlite3.connect("pedidos.db")

    df_pedidos = pd.read_sql_query("SELECT * FROM pedidos", conn)
    df_detalle = pd.read_sql_query("SELECT * FROM pedido_detalle", conn)

    conn.close()

    archivo = "reporte_pedidos.xlsx"

    with pd.ExcelWriter(archivo) as writer:
        df_pedidos.to_excel(writer, sheet_name="Pedidos", index=False)
        df_detalle.to_excel(writer, sheet_name="Detalle", index=False)

    return send_file(archivo, as_attachment=True)

if __name__ == "__main__":

    app.run(debug=True)
